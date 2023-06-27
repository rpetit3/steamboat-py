from Bio import SeqIO

def read_fasta_dict(fasta: str) -> dict:
    """
    Read an input FASTA file and return a dictionary of sequences

    Args:
        fasta (str): The path to the FASTA file

    Returns:
        dict: A dictionary of sequences with the sequence name as the key
    """
    seqs = {}
    with open(fasta, 'r') as fasta_fh:
        for record in SeqIO.parse(fasta_fh,'fasta'):
            seqs[record.name] = str(record.seq)
    return seqs


def read_fasta_list(fasta: str) -> list:
    """
    Read an input FASTA file and return a list of sequences

    Args:
        fasta (str): The path to the FASTA file

    Returns:
        list: A list of sequences (sequence names are not included)
    """
    seqs = []
    with open(fasta, 'r') as fasta_fh:
        for record in SeqIO.parse(fasta_fh,'fasta'):
            seqs.append(str(record.seq))
    return seqs
