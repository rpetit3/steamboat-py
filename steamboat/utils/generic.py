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
    """A simple wrapper around executor."""
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
    Validate a file exists and return the absolute path

    Args:
        filename (str): a file to validate exists

    Returns:
        str: absolute path to file
    """
    f = Path(filename)
    if not f.exists():
        raise FileNotFoundError(f"File not found: {filename}")
    return f.absolute()
