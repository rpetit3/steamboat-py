import logging
from collections import OrderedDict
from pathlib import Path

from steamboat.io.fasta import read_fasta
from steamboat.io.table import read_table

# GISAID Related (last updated 2023/06/26)
GISAID_TYPE = 'betacoronavirus'
GISAID_FIELDS = [
    'submitter',
    'fn',
    'covv_virus_name',
    'covv_type',
    'covv_passage',
    'covv_collection_date',
    'covv_location',
    'covv_add_location',
    'covv_host',
    'covv_add_host_info',
    'covv_sampling_strategy',
    'covv_gender',
    'covv_patient_age',
    'covv_patient_status',
    'covv_specimen',
    'covv_outbreak',
    'covv_last_vaccinated',
    'covv_treatment',
    'covv_seq_technology',
    'covv_assembly_method',
    'covv_coverage',
    'covv_orig_lab',
    'covv_orig_lab_addr',
    'covv_provider_sample_id',
    'covv_subm_lab',
    'covv_subm_lab_addr',
    'covv_subm_sample_id',
    'covv_consortium',
    'covv_authors',
    'covv_comment',
    'comment_type'
]
GISAID_HEADERS = {
    'submitter': 'Submitter',
    'fn': 'FASTA filename',
    'covv_virus_name': 'Virus name',
    'covv_type': 'Type',
    'covv_passage': 'Passage details/history',
    'covv_collection_date': 'Collection date',
    'covv_location': 'Location',
    'covv_add_location': 'Additional location information',
    'covv_host': 'Host',
    'covv_add_host_info': 'Additional host information',
    'covv_sampling_strategy': 'Sampling Strategy',
    'covv_gender': 'Gender',
    'covv_patient_age': 'Patient age',
    'covv_patient_status': 'Patient status',
    'covv_specimen': 'Specimen source',
    'covv_outbreak': 'Outbreak',
    'covv_last_vaccinated': 'Last vaccinated',
    'covv_treatment': 'Treatment',
    'covv_seq_technology': 'Sequencing technology',
    'covv_assembly_method': 'Assembly method',
    'covv_coverage': 'Coverage',
    'covv_orig_lab': 'Originating lab',
    'covv_orig_lab_addr': 'Address',
    'covv_provider_sample_id': 'Sample ID given by the sample provider',
    'covv_subm_lab': 'Submitting lab',
    'covv_subm_lab_addr': 'Address',
    'covv_subm_sample_id': 'Sample ID given by the submitting laboratory',
    'covv_consortium': 'Sequencing consortium',
    'covv_authors': 'Authors',
    'covv_comment': 'Comment',
    'comment_type': 'Comment Icon'
}
SEQUENCER = {
    'clearlabs': 'Oxford Nanopore Technologies (via ClearLabs)',
    'iseq': 'Illumina iSeq',
    'hiseq': 'Illumina HiSeq',
    'miseq': 'Illumina MiSeq',
    'nextseq': 'Illumina NextSeq',
    'ont': 'Oxford Nanopore Technologies'
}


def gisaid_header() -> str:
    """
    Return the GISAID header for a metadata file

    Returns:
        str: A string of the GISAID header

    Examples:
        >>> from steamboat.repos.gisaid import gisaid_header
        >>> header = gisaid_header()
    """
    header1 = []
    header2 = []
    for field in GISAID_FIELDS:
        header1.append(f'"{field}"')
        header2.append(f'"{GISAID_HEADERS[field]}"')
    header1_description = ','.join(header1)
    header2_description = ','.join(header2)
    return f'{header1_description}\n{header2_description}\n'


def gisaid_formatter(metadata: dict, fasta: str, sequencer: str, constants: dict) -> dict:
    """
    Format metadata and FASTA sequences for GISAID submission

    Args:
        metadata (dict): metadata associated with an input sample
        fasta (str): The FASTA file in which the sequences are stored
        sequencer (str): the sequencer used to generate sequences
        constants (dict): constant information for GISAID fields

    Returns:
        dict: A dictionary of formatted metadata

    Examples:
        >>> from steamboat.repos.gisaid import gisaid_formatter
        >>> metadata = gisaid_formatter(metadata[sample_id], "assemblies", "miseq", yaml_file)
    """
    logging.debug(f"Formatting {metadata['sample_id']} metadata for GISAID submission")
    authors = "{}, and {}".format(", ".join(constants['AUTHORS'][:-1]), constants['AUTHORS'][-1])
    year = metadata['collection_date'].split("-")[0]
    virus_name = f'hCoV-19/{constants["COUNTRY"]}/{constants["SUBMISSION_ID_PREFIX"]}{metadata["sample_id"]}/{year}'
    location = f'{constants["CONTINENT"]} / {constants["COUNTRY"]} / {constants["STATE"]}'
    return OrderedDict((
        ('submitter', constants['SUBMITTER']),
        ('fn', fasta),
        ('covv_virus_name', virus_name),
        ('covv_type', GISAID_TYPE),
        ('covv_passage', constants['GISAID_PASSAGE']),
        ('covv_collection_date', metadata['collection_date']),
        ('covv_location', location),
        ('covv_add_location', ''),
        ('covv_host', constants['GISAID_HOST']),
        ('covv_add_host_info', ''),
        ('covv_sampling_strategy', constants['GISAID_SAMPLING_STRATEGY'] if 'GISAID_SAMPLING_STRATEGY' in constants else ''),
        ('covv_gender', metadata['sex'].lower()),
        ('covv_patient_age', '>90' if int(metadata['age']) >= 90 else metadata['age']),
        ('covv_patient_status', constants['GISAID_PATIENT_STATUS']),
        ('covv_specimen', metadata['source'] if 'source' in metadata else ''),
        ('covv_outbreak', ''),
        ('covv_last_vaccinated', ''),
        ('covv_treatment', ''),
        ('covv_seq_technology', SEQUENCER[sequencer]),
        ('covv_assembly_method', ''),
        ('covv_coverage', ''),
        ('covv_orig_lab', constants['ORIGINATING_LAB']),
        ('covv_orig_lab_addr', constants['ORIGINATING_LAB_ADDRESS']),
        ('covv_provider_sample_id', ''),
        ('covv_subm_lab', constants['SUBMITTING_LAB']),
        ('covv_subm_lab_addr', constants['SUBMITTING_LAB_ADDRESS']),
        ('covv_subm_sample_id', ''),
        ('covv_consortium', ''),
        ('covv_authors', authors),
        ('covv_comment', ''),
        ('comment_type', '')
    ))


def parse_consensus_assemblies(assemblies: str, extension: str) -> dict:
    """
    Parse a directory of consensus assemblies and return a dictionary of assemblies

    Args:
        assemblies (str): directory of consensus assemblies
        extension (str): the file extension of the assemblies

    Returns:
        dict: A dictionary of assemblies

    Examples:
        >>> from steamboat.repos.gisaid import parse_consensus_assemblies
        >>> assemblies = parse_consensus_assemblies("assemblies", "fasta")
    """
    seqs = {}
    for assembly in Path(assemblies).glob(f"*.{extension}"):
        fasta = read_fasta(assembly, "list")

        if len(fasta) == 1:
            seqs[(assembly.name).replace(f".{extension}", "")] = fasta[0]
        elif len(fasta) > 1:
            logging.error(f"Consensus assembly for {assembly} contains more than one sequence")
        else:
            logging.error(f"Consensus assembly for {assembly} is empty")

    logging.debug(f"Found {len(seqs)} consensus assemblies")
    return seqs


def parse_results(input: str, pipeline: str) -> dict:
    """
    Parse a pipeline results file and return a dictionary of results

    Args:
        input (str): input results file to be parsed
        pipeline (str): the pipeline used to generate the results

    Returns:
        dict: A dictionary of results

    Examples:
        >>> from steamboat.repos.gisaid import parse_results
        >>> results = parse_results("data.tsv", "cecret")
    """
    logging.debug(f"Parsing results from {input} generated by {pipeline}")
    data = read_table(input)
    if pipeline == 'cecret':
        return _parse_cecret_results(data)
    elif pipeline == 'titan':
        return _parse_titan_results(data)
    else:
        raise ValueError("Invalid pipeline, please use either 'cecret' or 'titan'")


def _parse_cecret_results(data: list) -> dict:
    """
    Parse the results from the cecret pipeline

    num_N = number of Ns in the genome
    samtools_per_1X_coverage_after_trimming = percent of the genome covered by at least 1X

    Args:
        data (list): the data to be parsed

    Returns:
        dict: A dictionary of parsed results

    Examples:
        >>> from steamboat.repos.gisaid  import _parse_cecret_results
        >>> results = _parse_cecret_results(data)
    """
    final_data = {}
    for row in data:
        row['total_ns'] = row['num_N']
        row['percent_coverage'] = row['samtools_per_1X_coverage_after_trimming']
        final_data[row["sample_id"]] = row

    logging.debug(f"Found {len(final_data)} samples for cecret results") 
    return final_data


def _parse_titan_results(data: list) -> dict:
    """
    Parse the results from the titan pipeline

    number_n = number of Ns in the genome
    percent_reference_coverage = percent of the genome covered by the reference

    Args:
        data (list): the data to be parsed

    Returns:
        dict: A dictionary of parsed results

    Examples:
        >>> from steamboat.repos.gisaid import _parse_titan_results
        >>> results = _parse_titan_results(data)
    """
    final_data = {}
    for row in data:
        row['total_ns'] = row['number_n']
        row['percent_coverage'] = row['percent_reference_coverage']
        final_data[row["sample"]] = row

    logging.debug(f"Found {len(final_data)} samples for titan results")
    return final_data
