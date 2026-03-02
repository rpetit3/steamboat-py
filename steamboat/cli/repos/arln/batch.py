import csv
import logging
import sys
from pathlib import Path

import rich
import rich.console
import rich.traceback
import rich_click as click
from rich import print
from rich.logging import RichHandler

import steamboat
from steamboat.io.check import check_file, file_exists_error
from steamboat.repos.arln import ARLN_FIELDS, parse_arln


# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "arln-batch": [
        {
            "name": "Required Options",
            "options": [
                "--metadata",
                "--gigatyper",
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
    "--metadata",
    "-m",
    required=False if "--version" in sys.argv else True,
    help="A CSV file with sequencing metadata (e.g. temp/cres.csv)",
)
@click.option(
    "--gigatyper",
    "-g",
    required=False if "--version" in sys.argv else True,
    help="A TSV file with GigaTyper results (e.g. temp/gigatyper.txt)",
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
    default="arln-batch",
    show_default=True,
    help="Prefix to use for output files",
)
@click.option("--force", is_flag=True, help="Overwrite existing reports")
@click.option("--verbose", is_flag=True, help="Increase the verbosity of output")
@click.option("--silent", is_flag=True, help="Only critical errors will be printed")
@click.option("--version", is_flag=True, help="Print version")
def arln_batch(
    metadata,
    gigatyper,
    outdir,
    prefix,
    force,
    verbose,
    silent,
    version,
):
    """arln-batch - Format data for ARLN submission."""
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
    metadata_file = check_file(metadata)
    gigatyper_file = check_file(gigatyper)

    # Output files
    arln_csv = Path(outdir) / f'{prefix}.csv'

    # Make sure output files don't already exist, delete if --force
    file_exists_error(arln_csv, force)
    if force and arln_csv.exists():
        arln_csv.unlink()

    # Read in the data
    parsed_results = parse_arln(metadata_file, gigatyper_file)

    # Write the output files
    logging.info(f"Writing {arln_csv}")
    with open(arln_csv, 'wt') as csv_fh:
        writer = csv.DictWriter(csv_fh, fieldnames=ARLN_FIELDS)
        writer.writeheader()
        writer.writerows(parsed_results)


def main():
    if len(sys.argv) == 1:
        arln_batch.main(["--help"])
    else:
        arln_batch()


if __name__ == "__main__":
    main()
