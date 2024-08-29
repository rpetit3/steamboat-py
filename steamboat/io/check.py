from pathlib import Path


def check_file(filename: str) -> str:
    """
    Check that a file exists and not empty, if true, return the absolute path

    Args:
        filename (str): a file to validate exists

    Returns:
        str: absolute path to file

    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if the file is empty

    Examples:
        >>> from steamboat.io.check import check_file
        >>> file = check_file("data.fasta")
    """
    f = Path(filename)
    if not f.exists():
        raise FileNotFoundError(f"File ('{filename}') not found, cannot continue")
    elif f.stat().st_size == 0:
        raise ValueError(f"File ('{filename}') is empty, cannot continue")
    return f.absolute()


def file_exists_error(filename: str, force: bool = False):
    """
    Determine if a file exists and raise an error if it does.

    Args:
        filename (str): the file to check
        force (bool, optional): force overwrite. Defaults to False.

    Raises:
        FileExistsError: if the file exists and force is False
    """
    if Path(filename).exists() and not force:
        raise FileExistsError(
            f"Results already exists! Use --force to overwrite: {filename}"
        )
