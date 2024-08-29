import logging

import yaml


def read_yaml(yamlfile: str) -> dict | list:
    """
    Parse a YAML file.

    Args:
        yamlfile (str): input YAML file to be read

    Returns:
        Union[list, dict]: the values parsed from the YAML file

    Examples:
        >>> from camlhmp.utils import read_yaml
        >>> data = read_yaml("data.yaml")
    """
    logging.debug(f"Reading YAML from {yamlfile}")
    with open(yamlfile, "rt") as fh:
        return yaml.safe_load(fh)


def write_yaml(yamlfile: str, data: dict | list):
    """
    Write a list or dictionary to a YAML file.

    Args:
        yamlfile (str): output YAML file to be written
        data (Union[list, dict]): a list or dictionary to be written to the file

    Examples:
        >>> from camlhmp.utils import write_yaml
        >>> write_yaml("data.yaml", {"key": "value"})
    """
    logging.debug(f"Writing YAML to {yamlfile}")
    with open(yamlfile, "wt") as fh:
        yaml.dump(data, fh)
