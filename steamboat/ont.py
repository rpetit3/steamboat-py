import json
import logging
import sys
from pathlib import Path

from steamboat.utils.generic import execute

FASTQ_SCAN_FIELDS = [
    "total_bp",
    "read_total",
    "read_min",
    "read_mean",
    "read_median",
    "read_max",
    "qual_mean",
]

SUMMARY_FIELDS = (
    ["flowcell_id", "sample_id"]
    + [f"pass_{field}" for field in FASTQ_SCAN_FIELDS]
    + [f"fail_{field}" for field in FASTQ_SCAN_FIELDS]
    + ["merged_file"]
)


def _run_fastq_scan(fastq_files):
    """
    Run fastq-scan on one or more gzipped FASTQ files and return QC stats.

    Args:
        fastq_files (list): List of paths to .fastq.gz files.

    Returns:
        dict: The qc_stats from fastq-scan, or empty dict if no files.
    """
    if not fastq_files:
        return {}

    file_list = " ".join(str(f) for f in fastq_files)
    result = execute(f"zcat {file_list} | fastq-scan -q", capture=True, allow_fail=True)

    if result is None:
        logging.warning("fastq-scan failed, returning empty stats")
        return {}

    stdout, stderr = result
    try:
        data = json.loads(stdout)
        return data.get("qc_stats", {})
    except json.JSONDecodeError:
        logging.warning(f"Failed to parse fastq-scan output: {stdout[:200]}")
        return {}


def _extract_stats(qc_stats, prefix):
    """
    Extract the fields we care about from fastq-scan qc_stats with a prefix.

    Args:
        qc_stats (dict): The qc_stats dict from fastq-scan output.
        prefix (str): Prefix to add to each field name (e.g. "pass" or "fail").

    Returns:
        dict: Prefixed stats dict.
    """
    result = {}
    for field in FASTQ_SCAN_FIELDS:
        result[f"{prefix}_{field}"] = qc_stats.get(field, 0)
    return result


def discover_runs(run_dir):
    """
    Discover all ONT run subdirectories under a run directory.

    Looks for the pattern: <run_dir>/<FLOWCELL_ID>/<ONT_ID>/fastq_pass/

    Args:
        run_dir (str): Path to the ONT run directory.

    Returns:
        list: List of dicts with keys: flowcell_id, ont_id, ont_dir.
    """
    run_path = Path(run_dir)
    runs = []
    for flowcell_dir in sorted(run_path.iterdir()):
        if not flowcell_dir.is_dir():
            continue
        for ont_dir in sorted(flowcell_dir.iterdir()):
            if not ont_dir.is_dir():
                continue
            fastq_pass = ont_dir / "fastq_pass"
            if fastq_pass.is_dir():
                runs.append({
                    "flowcell_id": flowcell_dir.name,
                    "ont_id": ont_dir.name,
                    "ont_dir": str(ont_dir),
                })
                logging.debug(
                    f"Found run: flowcell={flowcell_dir.name} ont_id={ont_dir.name}"
                )
    if not runs:
        logging.error(f"No ONT runs found under {run_dir}")
    return runs


def preview_barcodes(ont_dir, flowcell_id):
    """
    Preview what would be merged for a given ONT run without performing any actions.

    Args:
        ont_dir (str): Path to the ONT run subdirectory (contains fastq_pass/).
        flowcell_id (str): Flow cell ID for summary output.

    Returns:
        list: List of preview dicts, one per barcode.
    """
    ont_path = Path(ont_dir)
    fastq_pass = ont_path / "fastq_pass"
    fastq_fail = ont_path / "fastq_fail"
    preview = []

    for barcode_dir in sorted(fastq_pass.iterdir()):
        if not barcode_dir.is_dir():
            continue

        sample_id = barcode_dir.name
        pass_files = list(barcode_dir.glob("*.fastq.gz"))
        fail_dir = fastq_fail / sample_id
        fail_files = list(fail_dir.glob("*.fastq.gz")) if fail_dir.is_dir() else []

        if not pass_files:
            continue

        preview.append({
            "flowcell_id": flowcell_id,
            "sample_id": sample_id,
            "pass_files": len(pass_files),
            "fail_files": len(fail_files),
        })

    return preview


def merge_barcodes(ont_dir, flowcell_id, outdir):
    """
    Merge fastq_pass chunks per barcode using cat and collect stats via fastq-scan.

    Only pass reads are merged into output files. Fail reads are scanned for
    stats only (no merged file written).

    Args:
        ont_dir (str): Path to the ONT run subdirectory (contains fastq_pass/).
        flowcell_id (str): Flow cell ID for summary output.
        outdir (str): Output directory for merged files.

    Returns:
        list: List of summary dicts, one per barcode.
    """
    ont_path = Path(ont_dir)
    out_path = Path(outdir)
    fastq_pass = ont_path / "fastq_pass"
    fastq_fail = ont_path / "fastq_fail"
    summary = []

    out_path.mkdir(parents=True, exist_ok=True)

    for barcode_dir in sorted(fastq_pass.iterdir()):
        if not barcode_dir.is_dir():
            continue

        sample_id = barcode_dir.name
        pass_files = sorted(barcode_dir.glob("*.fastq.gz"))

        if not pass_files:
            logging.warning(f"Skipping {sample_id}: no fastq.gz files in fastq_pass")
            continue

        # Merge pass files
        merged_file = out_path / f"{sample_id}.fastq.gz"
        logging.info(f"Merging {len(pass_files)} files for {flowcell_id}/{sample_id}")

        file_list = " ".join(str(f) for f in pass_files)
        execute(f"cat {file_list} > {merged_file}")

        # Get pass stats from merged file
        pass_stats = _run_fastq_scan([merged_file])

        # Get fail stats (scan in-place, no merge)
        fail_dir = fastq_fail / sample_id
        fail_files = sorted(fail_dir.glob("*.fastq.gz")) if fail_dir.is_dir() else []
        fail_stats = _run_fastq_scan(fail_files)

        # Build summary row
        row = {
            "flowcell_id": flowcell_id,
            "sample_id": sample_id,
        }
        row.update(_extract_stats(pass_stats, "pass"))
        row.update(_extract_stats(fail_stats, "fail"))
        row["merged_file"] = str(merged_file)

        summary.append(row)

    return summary
