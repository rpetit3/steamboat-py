#!/usr/bin/env bash
# Create a mock ONT directory structure for testing ont-merge.
# Generates a minimal but representative layout with obfuscated IDs.
# Usage: bash tests/ont/create-test-data.sh [BASE_DIR]
#   BASE_DIR defaults to /tmp/ont-test
set -euo pipefail

BASE_DIR="${1:-/tmp/ont-test}"

# create_barcode RUN_DIR FLOWCELL HASH1 HASH2 BARCODE PASS_COUNT FAIL_COUNT
create_barcode() {
    local run_dir="$1" fc="$2" h1="$3" h2="$4" bc="$5" npass="$6" nfail="$7"

    mkdir -p "${run_dir}/fastq_pass/${bc}"
    for ((i = 0; i < npass; i++)); do
        touch "${run_dir}/fastq_pass/${bc}/${fc}_pass_${bc}_${h1}_${h2}_${i}.fastq.gz"
    done

    if ((nfail > 0)); then
        mkdir -p "${run_dir}/fastq_fail/${bc}"
        for ((i = 0; i < nfail; i++)); do
            touch "${run_dir}/fastq_fail/${bc}/${fc}_fail_${bc}_${h1}_${h2}_${i}.fastq.gz"
        done
    fi
}

echo "Creating test directory structure under ${BASE_DIR} ..."

# Run 1: barcodeNN naming, 3 barcodes + unclassified, pass and fail
RUN1="${BASE_DIR}/data/TestRun-250101/FAA00001/20250101_1200_X1_FAA00001_aabbccdd"
create_barcode "${RUN1}" FAA00001 aabbccdd 11111111 barcode01    3 1
create_barcode "${RUN1}" FAA00001 aabbccdd 11111111 barcode02    5 2
create_barcode "${RUN1}" FAA00001 aabbccdd 11111111 barcode03    1 0
create_barcode "${RUN1}" FAA00001 aabbccdd 11111111 unclassified 2 3

mkdir -p "${RUN1}/other_reports"
touch "${RUN1}/report_FAA00001_20250101_1204_aabbccdd.html"
touch "${RUN1}/report_FAA00001_20250101_1204_aabbccdd.json"
touch "${RUN1}/report_FAA00001_20250101_1204_aabbccdd.md"
touch "${RUN1}/final_summary_FAA00001_aabbccdd_11111111.txt"
touch "${RUN1}/sequencing_summary_FAA00001_aabbccdd_11111111.txt"
touch "${RUN1}/other_reports/pore_scan_data_FAA00001_aabbccdd_11111111.csv"

# Run 2: bcNN naming, 2 barcodes + unclassified
RUN2="${BASE_DIR}/data/TestRun-250201/FBB00002/20250201_0900_X2_FBB00002_ddeeff00"
create_barcode "${RUN2}" FBB00002 ddeeff00 22222222 bc01         4 1
create_barcode "${RUN2}" FBB00002 ddeeff00 22222222 bc02         2 0
create_barcode "${RUN2}" FBB00002 ddeeff00 22222222 unclassified 1 1

touch "${RUN2}/report_FBB00002_20250201_0904_ddeeff00.html"
touch "${RUN2}/final_summary_FBB00002_ddeeff00_22222222.txt"

DIR_COUNT=$(find "${BASE_DIR}" -type d | wc -l)
FILE_COUNT=$(find "${BASE_DIR}" -type f | wc -l)
echo "Done: ${DIR_COUNT} directories, ${FILE_COUNT} files created under ${BASE_DIR}"
