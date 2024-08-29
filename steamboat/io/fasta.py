import logging

from Bio import SeqIO


def read_fasta(fasta: str, return_type: str) -> dict | list:
    """
    Read an input FASTA file and return either a dictionary or list of sequences

    Args:
        fasta (str): The path to the FASTA file
        return_type (str): The type of return, either 'dict' or 'list'

    Returns:
        Union[dict, list]: A dictionary or list of sequences

    Raises:
        ValueError: if the return_type is not 'dict' or 'list'

    Examples:
        >>> from steamboat.io.fasta import read_fasta
        >>> seqs = read_fasta("data.fasta", "dict")
    """
    if return_type == "dict":
        return _read_fasta_as_dict(fasta)
    elif return_type == "list":
        return _read_fasta_as_list(fasta)
    else:
        raise ValueError("Invalid return type, please use either 'dict' or 'list'")


def _read_fasta_as_dict(fasta: str) -> dict:
    """
    Read an input FASTA file and return a dictionary of sequences

    Args:
        fasta (str): The path to the FASTA file

    Returns:
        dict: A dictionary of sequences with the sequence name as the key

    Examples:
        >>> from steamboat.io.fasta import read_fasta_as_dict
        >>> seqs = read_fasta_as_dict("data.fasta")
    """
    logging.debug(f"Reading FASTA from {fasta} as dictionary")
    seqs = {}
    with open(fasta, 'r') as fasta_fh:
        for record in SeqIO.parse(fasta_fh,'fasta'):
            seqs[record.name] = str(record.seq)
    return seqs


def _read_fasta_as_list(fasta: str) -> list:
    """
    Read an input FASTA file and return a list of sequences

    Args:
        fasta (str): The path to the FASTA file

    Returns:
        list: A list of sequences (sequence names are not included)

    Examples:
        >>> from steamboat.io.fasta import read_fasta_as_list
        >>> seqs = read_fasta_as_list("data.fasta")
    """
    logging.debug(f"Reading FASTA from {fasta} as list")
    seqs = []
    with open(fasta, 'r') as fasta_fh:
        for record in SeqIO.parse(fasta_fh,'fasta'):
            seqs.append(str(record.seq))
    return seqs


def write_fasta(fasta: str, seqs: dict | list):
    """
    Write a dictionary of sequences to a FASTA file

    Args:
        fasta (str): The path to the FASTA file
        seqs (dict): A dictionary of sequences with the sequence name as the key

    Raises:
        ValueError: if the sequence type is not a dictionary or list

    Examples:
        >>> from steamboat.io.fasta import write_fasta
        >>> write_fasta("data.fasta", {"seq1": "ATGC", "seq2": "ATGC"})
        >>> write_fasta("data.fasta", ["ATGC", "ATGC"])
    """
    if isinstance(seqs, dict):
        _write_dict_to_fasta(fasta, seqs)
    elif isinstance(seqs, list):
        _write_list_to_fasta(fasta, seqs)
    else:
        raise ValueError("Invalid sequence type, please use either a dictionary or list")


def _write_dict_to_fasta(fasta: str, seqs: dict):
    """
    Write a dictionary of sequences to a FASTA file

    Args:
        fasta (str): The path to the FASTA file
        seqs (dict): A dictionary of sequences with the sequence name as the key

    Examples:
        >>> from steamboat.io.fasta import write_dict_to_fasta
        >>> write_dict_to_fasta("data.fasta", {"seq1": "ATGC", "seq2": "ATGC"})
    """
    logging.debug(f"Writing dictionary to FASTA ({fasta})")
    with open(fasta, 'w') as fasta_fh:
        for seq_name, seq in seqs.items():
            fasta_fh.write(f">{seq_name}\n{seq}\n")


def _write_list_to_fasta(fasta: str, seqs: list):
    """
    Write a list of sequences to a FASTA file

    Args:
        fasta (str): The path to the FASTA file
        seqs (list): A list of sequences

    Examples:
        >>> from steamboat.io.fasta import write_list_to_fasta
        >>> write_list_to_fasta("data.fasta", ["ATGC", "ATGC"])
    """
    logging.debug(f"Writing list to FASTA ({fasta})")
    with open(fasta, 'w') as fasta_fh:
        for i, seq in enumerate(seqs):
            fasta_fh.write(f">seq{i}\n{seq}\n")
