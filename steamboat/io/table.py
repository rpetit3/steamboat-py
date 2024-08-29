import csv
import logging

def read_table(
    input: str, delimiter: str = "\t", has_header: bool = True
) -> dict | list:
    """
    Parse a delimited file.

    Args:
        input (str): input delimited file to be parsed
        delimiter (str, optional): delimiter used to separate column values. Defaults to '\t'.
        has_header (bool, optional): the first line should be treated as a header. Defaults to True.

    Returns:
        Union[list, dict]: A dict is returned if a header is present, otherwise a list is returned

    Examples:
        >>> from camlhmp.utils import parse_table
        >>> data = parse_table("data.tsv")
    """
    logging.debug(f"Reading table from {input} with delimiter {delimiter}")
    data = []
    with open(input, "rt") as fh:
        for row in (
            csv.DictReader(fh, delimiter=delimiter)
            if has_header
            else csv.reader(fh, delimiter=delimiter)
        ):
            data.append(row)
    return data


def write_table(output: str, data: list, delimiter: str = "\t"):
    """
    Write a list or dictionary to a delimited file.

    Args:
        output (str): output delimited file to be written
        data (list): a list of dicts to be written to the file
        delimiter (str, optional): delimiter to separate column values. Defaults to '\t'.

    Examples:
        >>> from camlhmp.utils import write_table
        >>> write_table("data.tsv", [{"col1": "val1", "col2": "val2"}])
        >>> write_table("data.csv", [{"col1": "val1", "col2": "val2"}], delimiter=",")
    """
    logging.debug(f"Writing table to {output} with delimiter {delimiter}")
    with open(output, "wt") as fh:
        writer = csv.DictWriter(fh, delimiter=delimiter, fieldnames=data[0].keys())
        writer.writeheader()
        if next(iter(data[0].values())):
            # Data is not empty
            writer.writerows(data)
        else:
            # Data is empty
            logging.debug("No values found, only writing the column headers")
