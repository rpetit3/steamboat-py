import logging
import os
import sys
from pathlib import Path

import rich
import rich.console
import rich.traceback
import rich_click as click
from rich import print
from rich.logging import RichHandler
from rich.table import Table

import steamboat
from steamboat.io.check import check_file, file_exists_error
from steamboat.io.fasta import read_fasta
from steamboat.io.table import read_table
from steamboat.io.yaml import read_yaml
from steamboat.repos.gisaid import gisaid_header, gisaid_formatter, parse_consensus_assemblies, parse_results


# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "gisaid-batch": [
        {
            "name": "Required Options",
            "options": [
                "--results",
                "--assemblies",
                "--metadata",
                "--sequencer",
                "--yaml",
            ],
        },
        {
            "name": "Filtering Options",
            "options": [
                "--min-coverage",
                "--max-ns",
            ],
        },
        {
            "name": "Additional Options",
            "options": [
                "--prefix",
                "--outdir",
                "--force",
                "--verbose",
                "--silent",
                "--version",
                "--help",
            ],
        },
    ]
}


@click.command()
@click.option(
    "--results",
    "-r",
    required=False if "--version" in sys.argv else True,
    help="A CSV or TSV file with the results of pipeline analysis",
)
@click.option(
    "--assemblies",
    "-a",
    required=False if "--version" in sys.argv else True,
    help="Directory of FASTA assemblies to be uploaded",
)
@click.option(
    "--metadata",
    "-m",
    required=False if "--version" in sys.argv else True,
    help="A TSV or CSV file of metadata associated with input samples",
)
@click.option(
    "--sequencer",
    "-s",
    required=False if "--version" in sys.argv else True,
    type=click.Choice(['clearlabs', 'iseq', 'hiseq', 'miseq', 'nextseq', 'ont'], case_sensitive=True),
    help="Sequencer used to generate sequences.",
)
@click.option(
    "--yaml",
    "-y",
    required=True,
    default=os.environ.get("GISAID_YAML", None),
    show_default=True,
    help="A YAML formatted file containing constant information for GISAID fields.",
)
@click.option(
    "--outdir",
    "-o",
    type=click.Path(exists=False),
    default="./",
    show_default=True,
    help="Directory to write output",
)
@click.option(
    "--prefix",
    "-p",
    type=str,
    default="gisaid-batch",
    show_default=True,
    help="Prefix to use for output files",
)
@click.option(
    "--min-coverage",
    default=70.0,
    show_default=True,
    help="Minimum percent coverage to count a hit",
)
@click.option(
    "--max-ns",
    default=7500,
    show_default=True,
    help="Minimum percent identity to count a hit",
)
@click.option(
    "--pipeline",
    "-p",
    default='cecret',
    type=click.Choice(['cecret', 'titan'], case_sensitive=True),
    show_default=True,
    help="Pipeline used for analysis.",
)
@click.option(
    "--extension",
    "-e",
    default='consensus.fa',
    show_default=True,
    help="The extension used for assemblies.",
)
@click.option(
    "--sample-prefix",
    help="Add this to the beginning on sample names in the metadata file.",
)
@click.option("--force", is_flag=True, help="Overwrite existing reports")
@click.option("--verbose", is_flag=True, help="Increase the verbosity of output")
@click.option("--silent", is_flag=True, help="Only critical errors will be printed")
@click.option("--version", is_flag=True, help="Print version")
def gisaid_batch(
    results,
    assemblies,
    metadata,
    sequencer,
    yaml,
    prefix,
    outdir,
    min_coverage,
    max_ns,
    pipeline,
    extension,
    sample_prefix,
    force,
    verbose,
    silent,
    version,
):
    """gisaid-batch - Format data for GISAID submission."""
    # Setup logs
    logging.basicConfig(
        format="%(asctime)s:%(name)s:%(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            RichHandler(rich_tracebacks=True, console=rich.console.Console(stderr=True))
        ],
    )
    logging.getLogger().setLevel(
        logging.ERROR if silent else logging.DEBUG if verbose else logging.INFO
    )

    # If prompted, print version, then exit
    if version:
        print(f"steamboat, version {steamboat.__version__}", file=sys.stderr)
        sys.exit(0)

    # Verify input files
    results_file = check_file(results)
    metadata_file = check_file(metadata)
    yaml_file = check_file(yaml)

    # Output files
    gisaid_fasta = f'{outdir}/{prefix}.fasta'
    gisaid_metadata = f'{outdir}/{prefix}.csv'
    gisaid_excluded = f'{outdir}/{prefix}.excluded.txt'

    # Make sure output files don't already exist
    file_exists_error(gisaid_fasta, force)
    file_exists_error(gisaid_metadata, force)
    file_exists_error(gisaid_excluded, force)

    # Read in the data
    results = parse_results(results_file, pipeline)
    metadata = read_table(metadata_file, delimiter="\t", has_header=True)
    yaml_data = read_yaml(yaml_file)
    assemblies = parse_consensus_assemblies(assemblies, extension)

    # Process each sample
    excluded = []
    final_data = {}
    for sample in metadata:
        sample_id = sample['sample_id']
        if sample_prefix:
            sample_id = f"{sample_prefix}{sample_id}"

        if sample_id not in results:
            logging.warning(f"Results for {sample_id} not found in {results_file}, skipping")
            continue

        if sample_id not in assemblies:
            logging.warning(f"Consensus assembly for {sample_id} not found in {assemblies.keys()}, skipping")
            continue

        # Check if the sample passes the filters
        exclude_reason = []
        if float(results[sample_id]['percent_coverage']) < min_coverage:
            message = f"{sample_id} - Low percent coverage ({results[sample_id]['percent_coverage']}%). Expected >= {min_coverage}%"
            exclude_reason.append(message)
            logging.warning(message)

        if int(results[sample_id]['total_ns']) > max_ns:
            message = f"{sample_id} - Too many Ns ({results[sample_id]['total_ns']}). Expected <= {max_ns}"
            exclude_reason.append(message)
            logging.warning(message)

        if exclude_reason:
            excluded.append([sample_id, ";".join(exclude_reason)])
        else:
            final_data[sample["sample_id"]] = {
                'data': gisaid_formatter(
                    sample,
                    str(Path(gisaid_fasta).name),
                    sequencer,
                    yaml_data,
                ),
                'sequence': assemblies[sample_id],
            }

    # Write the output files
    logging.info(f"Writing {gisaid_metadata}")
    logging.info(f"Writing {gisaid_fasta}")
    with open(gisaid_fasta, 'wt') as fasta_fh, open(gisaid_metadata, 'wt') as metadata_fh:
        metadata_fh.write(gisaid_header())
        for sample, data in final_data.items():
            fields = [f'"{x}"' for x in data['data'].values()]
            row = ",".join(fields)
            metadata_fh.write(f"{row}\n")
            fasta_fh.write(f">{data['data']['covv_virus_name']}\n{data['sequence']}\n")

    # Write the excluded samples
    logging.info(f"Writing {gisaid_excluded}")
    with open(gisaid_excluded, 'wt') as excluded_fh:
        excluded_fh.write("sample_id\treason\n")
        for sample in excluded:
            excluded_fh.write(f"{sample[0]}\t{sample[1]}\n")


def main():
    if len(sys.argv) == 1:
        gisaid_batch.main(["--help"])
    else:
        gisaid_batch()


if __name__ == "__main__":
    main()
