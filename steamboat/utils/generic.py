import logging
import subprocess
import sys
from pathlib import Path
from shutil import which
from sys import platform


def _execute_single(cmd, directory, capture):
    """
    Execute a single command without shell.

    Args:
        cmd (str): The command to be executed.
        directory (Path): The working directory.
        capture (bool): Capture the output of the command.

    Returns:
        Union[bool, list]: True if successful, or [stdout, stderr] if capture=True.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    command = subprocess.run(
        cmd.split(),
        cwd=directory,
        capture_output=True,
        text=True,
        check=True,
    )
    logging.debug(f"Exit code: {command.returncode}")
    logging.debug(f"STDOUT:\n{command.stdout}")
    logging.debug(f"STDERR:\n{command.stderr}")

    if capture:
        return [command.stdout, command.stderr]
    return True


def _execute_piped(cmd, directory, capture):
    """
    Execute a command containing pipes or redirects without using shell.

    Pipes (|) are handled by chaining subprocess.Popen processes.
    Output redirects (>) are handled by writing stdout to a file.

    Args:
        cmd (str): The command to be executed (may contain | or >).
        directory (Path): The working directory.
        capture (bool): Capture the output of the command.

    Returns:
        Union[bool, list]: True if successful, or [stdout, stderr] if capture=True.

    Raises:
        subprocess.CalledProcessError: If any command in the pipeline returns
            a non-zero exit code.
    """
    # Split on output redirect first
    redirect_file = None
    if ">" in cmd:
        parts = cmd.split(">", 1)
        cmd = parts[0].strip()
        redirect_file = parts[1].strip().strip('"').strip("'")

    # Split on pipes
    commands = [c.strip().split() for c in cmd.split("|")]

    # Chain processes
    prev_stdout = None
    processes = []
    for args in commands:
        proc = subprocess.Popen(
            args,
            cwd=directory,
            stdin=prev_stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if prev_stdout is not None:
            prev_stdout.close()
        prev_stdout = proc.stdout
        processes.append(proc)

    # Read output from last process
    last = processes[-1]
    stdout_bytes, stderr_bytes = last.communicate()

    # Wait for all processes to finish
    for proc in processes[:-1]:
        proc.wait()

    # Check for errors in any process
    for i, proc in enumerate(processes):
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode,
                commands[i],
                output=stdout_bytes,
                stderr=stderr_bytes,
            )

    stderr = stderr_bytes.decode() if stderr_bytes else ""

    # Handle redirect - write binary bytes to file before any decoding
    if redirect_file:
        redirect_path = Path(directory) / redirect_file if not Path(redirect_file).is_absolute() else Path(redirect_file)
        redirect_path.parent.mkdir(parents=True, exist_ok=True)
        with open(redirect_path, "wb") as fh:
            fh.write(stdout_bytes or b"")
        logging.debug(f"Redirected output to {redirect_path}")
        stdout = ""
    else:
        stdout = stdout_bytes.decode() if stdout_bytes else ""

    logging.debug(f"STDOUT:\n{stdout}")
    logging.debug(f"STDERR:\n{stderr}")

    if capture:
        return [stdout, stderr]
    return True


def execute(
    cmd,
    directory=Path.cwd(),
    capture=False,
    allow_fail=False,
):
    """
    A simple wrapper around subprocess.

    Single commands are executed without shell. Commands containing pipes (|) or
    redirects (>) are executed via shell.

    Args:
        cmd (str): The command to be executed.
        directory (Path, optional): The directory to execute the command in. Defaults to Path.cwd().
        capture (bool, optional): Capture the output of the command. Defaults to False.
        allow_fail (bool, optional): Allow the command to fail. Defaults to False.

    Returns:
        Union[bool, list]: True if successful, or [stdout, stderr] if capture=True.

    Examples:
        >>> from steamboat.utils.generic import execute
        >>> stdout, stderr = execute("ls -la", capture=True)
        >>> execute("zcat file.gz | fastq-scan -q", capture=True)
    """
    logging.debug(f"Executing command: {cmd}")
    logging.debug(f"Working directory: {directory}")
    try:
        if "|" in cmd or ">" in cmd:
            return _execute_piped(cmd, directory, capture)
        else:
            return _execute_single(cmd, directory, capture)
    except subprocess.CalledProcessError as e:
        logging.error(f'"{cmd}" returned exit code {e.returncode}')
        logging.error(e)
        if allow_fail:
            return None
        else:
            sys.exit(e.returncode)


def check_dependency(program):
    """
    Check if a program is available on PATH.

    Args:
        program (str): The program name to check.

    Returns:
        str: The path to the program.

    Raises:
        SystemExit: If the program is not found.

    Examples:
        >>> from steamboat.utils.generic import check_dependency
        >>> check_dependency("fastq-scan")
    """
    which_path = which(program)
    if which_path:
        logging.debug(f"Found {program} at {which_path}")
        return which_path
    else:
        logging.error(f"'{program}' not found. Please install it and try again.")
        sys.exit(1)


def get_platform():
    """
    Get the platform of the executing machine.

    Returns:
        str: The platform of the executing machine.

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


def validate_file(filename):
    """
    Validate a file exists and not empty, if passing return the absolute path.

    Args:
        filename (str): a file to validate exists.

    Returns:
        str: absolute path to file.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if the file is empty.

    Examples:
        >>> from steamboat.utils.generic import validate_file
        >>> file = validate_file("data.fasta")
    """
    f = Path(filename)
    if not f.exists():
        raise FileNotFoundError(f"File ('{filename}') not found, cannot continue")
    elif f.stat().st_size == 0:
        raise ValueError(f"File ('{filename}') is empty, cannot continue")
    return str(f.absolute())
