import logging
import sys

from steamboat.io.table import read_table

ARLN_FIELDS = [
    "record_id",
    "arln_specimen_id",
    "phl",        # WY
    "wgs_status", # WGS Successful
    "wgs_id",
    "srr_number",
    "bacterial_wgs_result",
    "wgs_date_id_created",
    "wgs_date_put_on_sequencer",
    "wgs_date_sent_to_seqfac",
]

ARLN_CONSTANTS = {
    "phl": "WY",
    "wgs_status": "WGS Successful",
}


def _process_metadata(row: dict) -> dict:
    """
    Extract necessary fields from a row of sequencing metadata.

    Args:
        row (dict): a row from the sequencing metadata table

    Returns:
        dict: extracted fields for ARLN submission

    Mappings for ARLN:
        LIMS ID # -> wgs_id appended with the year (YYYY) LIMSID
        LIMS ID # -> arln_specimen_id
        LIMS ID # -> record_id
        SRR ID -> srr_number
        Extraction Date -> wgs_date_id_created
        Extraction Date -> wgs_date_sent_to_seqfac
        Date Sequenced -> wgs_date_put_on_sequencer
    """
    if row["Sample Type"] == "CRE":
        # Check for missing required fields
        required_fields = {
            "LIMS ID #": row.get("LIMS ID #", "").strip(),
            "SRR ID": row.get("SRR ID", "").strip(),
            "Extraction Date": row.get("Extraction Date", "").strip(),
            "Date Sequenced": row.get("Date Sequenced", "").strip(),
        }
        missing = [field for field, value in required_fields.items() if not value]
        if missing:
            return {"_missing": missing, "_sample": row.get("LIMS ID #", "UNKNOWN").strip() or "UNKNOWN"}

        # Process CRE sample
        lims_id = required_fields["LIMS ID #"]
        # Extract year from first two digits of LIMS ID
        year = f"20{lims_id[:2]}"
        return {
            'record_id': lims_id,
            'arln_specimen_id': lims_id,
            'wgs_id': f"{year}LC_{lims_id}",
            'srr_number': required_fields["SRR ID"],
            'wgs_date_id_created': required_fields["Extraction Date"],
            'wgs_date_sent_to_seqfac': required_fields["Extraction Date"],
            'wgs_date_put_on_sequencer': required_fields["Date Sequenced"],
        }

    return {}


def _process_gigatyper(row: dict) -> tuple:
    """
    Extract sample ID and formatted MLST report from GigaTyper results.

    Args:
        row (dict): a row from the GigaTyper output table

    Returns:
        tuple: (sample_id, formatted_report)

    Columns of interest: sample, formatted_report
    """
    return row["sample"], row["formatted_report"]


def parse_arln(metadata: str, gigatyper: str) -> dict:
    """
    Parse a sequencing metadata file and a GigaTyper results file,
    then return a list of ARLN-formatted results.

    Args:
        metadata (str): sequencing metadata file to be parsed in CSV format
        gigatyper (str): GigaTyper results file to be parsed in TSV format

    Returns:
        list: A list of ARLN-formatted result dictionaries
    """
    logging.debug(f"Parsing metadata from {metadata}")
    results = []

    gigatyper_results = {}
    for row in read_table(gigatyper, delimiter="\t", has_header=True):
        sample_id, formatted_report = _process_gigatyper(row)
        if sample_id in gigatyper_results:
            gigatyper_results[sample_id].append(formatted_report)
        else:
            gigatyper_results[sample_id] = [formatted_report]
    gigatyper_results = {k: ";".join(v) for k, v in gigatyper_results.items()}

    errors = {}
    for row in read_table(metadata, delimiter=",", has_header=True):
        row_results = _process_metadata(row)
        if not row_results:
            continue

        sample = row.get("LIMS ID #", "UNKNOWN").strip() or "UNKNOWN"
        missing = []

        if "_missing" in row_results:
            missing.extend(row_results['_missing'])

        if sample not in gigatyper_results:
            missing.append("GigaTyper results")
        elif not missing:
            row_results['bacterial_wgs_result'] = gigatyper_results[sample]

        if missing:
            errors[sample] = missing
        else:
            row_results.update(ARLN_CONSTANTS)
            results.append(row_results)

    if errors:
        logging.error("Samples with missing data detected:")
        for sample, missing in errors.items():
            logging.error(f"  Sample '{sample}': missing {', '.join(missing)}")
        sys.exit(1)

    return results
