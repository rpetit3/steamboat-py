import logging
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
from steamboat.io.check import file_exists_error
from steamboat.io.table import write_table
from steamboat.ont import SUMMARY_FIELDS, discover_runs, merge_barcodes, preview_barcodes
from steamboat.utils.generic import check_dependency

# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "ont-merge": [
        {
            "name": "Required Options",
            "options": [
                "--run-dir",
            ],
        },
        {
            "name": "Additional Options",
            "options": [
                "--outdir",
                "--dry-run",
                "--force",
                "--verbose",
                "--silent",
                "--version",
                "--help",
            ],
        },
    ]
}


def _format_bp(bp):
    """Format base pairs into a human-readable string."""
    if bp >= 1_000_000_000:
        return f"{bp / 1_000_000_000:.2f} Gbp"
    elif bp >= 1_000_000:
        return f"{bp / 1_000_000:.2f} Mbp"
    elif bp >= 1_000:
        return f"{bp / 1_000:.2f} Kbp"
    else:
        return f"{bp} bp"


def _print_summary(summary):
    """
    Print a condensed Rich table summary to stderr.

    Args:
        summary (list): List of summary dicts from merge_barcodes.
    """
    table = Table(title="ONT Merge Summary")
    table.add_column("Flow Cell", style="cyan")
    table.add_column("Sample", style="green")
    table.add_column("Pass Total BP", justify="right")
    table.add_column("Fail Total BP", justify="right")

    for row in summary:
        table.add_row(
            row["flowcell_id"],
            row["sample_id"],
            _format_bp(row["pass_total_bp"]),
            _format_bp(row["fail_total_bp"]),
        )

    stderr.print(table)


def _print_dry_run(preview):
    """
    Print a dry-run preview table to stderr.

    Args:
        preview (list): List of preview dicts from preview_barcodes.
    """
    table = Table(title="ONT Merge Dry Run (no files written)")
    table.add_column("Flow Cell", style="cyan")
    table.add_column("Sample", style="green")
    table.add_column("Pass Files", justify="right")
    table.add_column("Fail Files", justify="right")

    for row in preview:
        table.add_row(
            row["flowcell_id"],
            row["sample_id"],
            str(row["pass_files"]),
            str(row["fail_files"]),
        )

    stderr.print(table)


@click.command()
@click.option(
    "--run-dir",
    "-r",
    required=False if "--version" in sys.argv else True,
    type=click.Path(exists=True),
    help="Path to the ONT run directory",
)
@click.option(
    "--outdir",
    "-o",
    type=click.Path(exists=False),
    default=None,
    help="Output directory (default: <run-dir>/merged)",
)
@click.option("--dry-run", is_flag=True, help="Show what would be merged without writing files")
@click.option("--force", is_flag=True, help="Overwrite existing merged output")
@click.option("--verbose", is_flag=True, help="Increase the verbosity of output")
@click.option("--silent", is_flag=True, help="Only critical errors will be printed")
@click.option("--version", is_flag=True, help="Print version")
def ont_merge(run_dir, outdir, dry_run, force, verbose, silent, version):
    """ont-merge - Merge ONT barcode FASTQ files per flow cell."""
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

    run_path = Path(run_dir).resolve()

    # Discover flow cells
    runs = discover_runs(str(run_path))
    if not runs:
        logging.error(f"No ONT runs found in {run_path}")
        sys.exit(1)

    logging.info(f"Found {len(runs)} ONT run(s) in {run_path}")

    # Dry run: preview what would be merged and exit
    if dry_run:
        all_preview = []
        for run in runs:
            all_preview.extend(
                preview_barcodes(run["ont_dir"], run["flowcell_id"])
            )
        if not all_preview:
            logging.warning("No barcodes found to merge")
        else:
            _print_dry_run(all_preview)
        sys.exit(0)

    # Verify dependencies
    check_dependency("fastq-scan")

    merged_dir = Path(outdir) if outdir else run_path / "merged"

    # Check if summary already exists
    summary_file = merged_dir / "summary.tsv"
    file_exists_error(summary_file, force)
    if force and summary_file.exists():
        summary_file.unlink()

    # Merge barcodes for each flow cell
    all_summary = []
    for run in runs:
        fc_outdir = merged_dir / run["flowcell_id"]

        if not force:
            if fc_outdir.is_dir() and any(fc_outdir.glob("*.fastq.gz")):
                raise FileExistsError(
                    f"Merged files already exist in {fc_outdir}. Use --force to overwrite."
                )

        run_summary = merge_barcodes(
            run["ont_dir"], run["flowcell_id"], str(fc_outdir)
        )
        all_summary.extend(run_summary)

    if not all_summary:
        logging.warning("No barcodes found to merge")
        sys.exit(0)

    # Write summary TSV
    logging.info(f"Writing {summary_file}")
    write_table(str(summary_file), all_summary, delimiter="\t")

    # Print condensed Rich summary table
    _print_summary(all_summary)


def main():
    if len(sys.argv) == 1:
        ont_merge.main(["--help"])
    else:
        ont_merge()


if __name__ == "__main__":
    main()
