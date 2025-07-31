import csv
import logging
import os
import sys

import rich
import rich.console
import rich.traceback
import rich_click as click
from rich import print
from rich.logging import RichHandler

import steamboat
from steamboat.io.check import check_file, file_exists_error
from steamboat.io.yaml import read_yaml
from steamboat.repos.nwss import NWSS_FIELDS, parse_results


# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "nwss-batch": [
        {
            "name": "Required Options",
            "options": [
                "--results",
                "--yaml",
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
    help="A TSV (or CSV) file with the dPCR results",
)
@click.option(
    "--yaml",
    "-y",
    required=True,
    default=os.environ.get("NWSS_YAML", None),
    show_default=True,
    help="A YAML formatted file containing constant information for NWSS fields.",
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
    default="nwss-batch",
    show_default=True,
    help="Prefix to use for output files",
)
@click.option("--force", is_flag=True, help="Overwrite existing reports")
@click.option("--verbose", is_flag=True, help="Increase the verbosity of output")
@click.option("--silent", is_flag=True, help="Only critical errors will be printed")
@click.option("--version", is_flag=True, help="Print version")
def nwss_batch(
    results,
    yaml,
    outdir,
    prefix,
    force,
    verbose,
    silent,
    version,
):
    """nwss-batch - Format data for NWSS submission."""
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
    yaml_file = check_file(yaml)

    # Output files
    nwss_csv = f'{outdir}/{prefix}.csv'

    # Make sure output files don't already exist
    file_exists_error(nwss_csv, force)

    # Read in the data
    yaml_data = read_yaml(yaml_file)
    parsed_results = parse_results(results_file, yaml_data)

    # Write the output files
    logging.info(f"Writing {nwss_csv}")
    with open(nwss_csv, 'wt') as csv_fh:
        writer = csv.DictWriter(csv_fh, fieldnames=NWSS_FIELDS)
        writer.writeheader()
        writer.writerows(parsed_results)


def main():
    if len(sys.argv) == 1:
        nwss_batch.main(["--help"])
    else:
        nwss_batch()


if __name__ == "__main__":
    main()
