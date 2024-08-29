import logging
import sys
from pathlib import Path
from sys import platform

from executor import ExternalCommand, ExternalCommandFailed


def execute(
    cmd,
    directory=Path.cwd(),
    capture=False,
    stdout_file=None,
    stderr_file=None,
    allow_fail=False,
):
    """
    A simple wrapper around executor.
s
    Args:
        cmd (str): The command to be executed
        directory (Path, optional): The directory to execute the command in. Defaults to Path.cwd().
        capture (bool, optional): Capture the output of the command. Defaults to False.
        stdout_file (Path, optional): The file to write stdout to. Defaults to None.
        stderr_file (Path, optional): The file to write stderr to. Defaults to None.
        allow_fail (bool, optional): Allow the command to fail. Defaults to False.

    Returns:
        Union[bool, list]: True if successful, otherwise a list of stdout and stderr

    Raises:
        ExternalCommandFailed: If the command fails and allow_fail is True

    Examples:
        >>> from steamboat.utils.generic import execute
        >>> stdout, stderr = execute(
                f"{cat_type} {subject} | {engine} -query {query} -subject - -outfmt '6 {outfmt}' {qcov_hsp_perc} {perc_identity}",
                capture=True,
            )
    """
    try:
        command = ExternalCommand(
            cmd,
            directory=directory,
            capture=True,
            capture_stderr=True,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )

        command.start()
        logging.debug(command.decoded_stdout)
        logging.debug(command.decoded_stderr)

        if capture:
            return [command.decoded_stdout, command.decoded_stderr]
        return True
    except ExternalCommandFailed as e:
        if allow_fail:
            logging.error(e)
            sys.exit(e.returncode)
        else:
            return None


def get_platform() -> str:
    """
    Get the platform of the executing machine

    Returns:
        str: The platform of the executing machine

    Examples:
        >>> from steamboat.utils.generic import get_platform
        >>> platform = get_platform()
    """
    if platform == "darwin":
        return "mac"
    elif platform == "win32":
        # Windows is not supported
        logging.error("Windows is not supported.")
        sys.exit(1)
    return "linux"


def validate_file(filename: str) -> str:
    """
    Validate a file exists and not empty, if passing return the absolute path

    Args:
        filename (str): a file to validate exists

    Returns:
        str: absolute path to file

    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if the file is empty

    Examples:
        >>> from steamboat.utils.generic import validate_file
        >>> file = validate_file("data.fasta")
    """
    f = Path(filename)
    if not f.exists():
        raise FileNotFoundError(f"File ('{filename}') not found, cannot continue")
    elif f.stat().st_size == 0:
        raise ValueError(f"File ('{filename}') is empty, cannot continue")
    return f.absolute()
