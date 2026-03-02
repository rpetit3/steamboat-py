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
        # Process CRE sample
        lims_id = row["LIMS ID #"]
        # Extract year from first two digits of LIMS ID
        year = f"20{lims_id[:2]}"
        return {
            'record_id': lims_id,
            'arln_specimen_id': lims_id,
            'wgs_id': f"{year}LC_{lims_id}",
            'srr_number': row["SRR ID"], 
            'wgs_date_id_created': row["Extraction Date"],
            'wgs_date_sent_to_seqfac': row["Extraction Date"],
            'wgs_date_put_on_sequencer': row["Date Sequenced"],
        }

    return {}


def _process_bactopia_summary(row: dict) -> list:
    """
    Parser for Bactopia summary results and extract MLST information.

    Args:
        row (dict): a row from the Bactopia summary table

    Returns:
        list: 0: sample_id, 1: ARLN formatted MLST result

    Columns of interest: sample, mlst_scheme, mlst_st


    CSV data element:

    bacterial_wgs_result

    Entry value and format instructions:

    Enter "MLST_<WGS result>_<scheme used>" or "N/A" based on the below scenarios.

    If an isolate does not have a defined Oxford, Pasteur, or Achtman MLST scheme, please enter the abbreviated organism name in place of the scheme name for <scheme used> (e.g., MLST_114_ecloacae; MLST_147_kpneumoniae; MLST_773_paeruginosa).

    If the MLST profile cannot be defined for an isolate with an available MLST scheme due to the presence of a novel allele or novel profile, please enter "_unnamed" for <WGS result> (e.g., MLST_unnamed_Oxford; MLST_unnamed_ecloacae).

    For E. coli and A. baumannii isolates, for which two MLST schemes are available, please report MLST results from both schemes (e.g., MLST_2_Pasteur; MLST_208_Oxford)

    If an MLST scheme is not available for an isolate's genus/species, please leave this data element blank.

    Example record entry (K. aerogenes):

    MLST_93_kaerogenes

    Example record entry (E.coli):

    MLST_10_Achtman; MLST_650_Pasteur

    Example record entry (A. baumannii):

    MLST_473_Oxford; MLST_2_Pasteur

    """
    sample_id = row["sample"]
    mlst_scheme = row["mlst_scheme"]
    mlst_st = row["mlst_st"]

    if mlst_scheme and mlst_st:
        bacterial_wgs_result = f"MLST_{mlst_st}_{mlst_scheme}"
    elif mlst_scheme and not mlst_st:
        bacterial_wgs_result = f"MLST_unnamed_{mlst_scheme}"
    else:
        bacterial_wgs_result = ""

    return sample_id, bacterial_wgs_result


def parse_arln(metadata: str, summary: str) -> dict:
    """
    Parse a sequencing metadata file and a summary of Bactopia results file,
    then return a dictionary of results

    Args:
        metadata (str): sequencing metadata file to be parsed in CSV format
        summary (str): summary of Bactopia results file to be parsed in TSV format

    Returns:
        dict: A dictionary of results

    Examples:
        >>> from steamboat.repos.nwss import parse_results
        >>> results = parse_results("data.tsv", mappings)
    """
    logging.debug(f"Parsing metadata from {metadata}")
    results = []

    bactopia_results = {}
    for row in read_table(summary, delimiter="\t", has_header=True):
        sample_id, mlst = _process_bactopia_summary(row)
        bactopia_results[sample_id] = mlst

    for row in read_table(metadata, delimiter=",", has_header=True):
        row_results = _process_metadata(row)
        if row_results['record_id'] in bactopia_results:
            row_results['bacterial_wgs_result'] = bactopia_results[row_results['record_id']]
        else:
            logging.error(f"No Bactopia results found for record_id {row_results['record_id']}")
            sys.exit(1)

    return results
