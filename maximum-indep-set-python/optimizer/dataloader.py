import json
import sys
from typing import Any, Dict, Optional


def read_input(input_path: Optional[str] = None) -> Dict[str, Any]:
    """Given an input path returns a structured input

    Parameters
    ----------
    input_path : Optional[str], optional
        Input path (relative to main.py). By default None, which uses `sys.stdin`

    Returns
    -------
    Dict[str, Any]
        Structured data for solving problem in a dict with fields
        - "nodes": list of integer with node ids
        - "edges": list of lists with pairs of connected nodes
    """
    input_file = {}
    if input_path:
        with open(input_path, encoding="utf-8") as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)

    return input_file
