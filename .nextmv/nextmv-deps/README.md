# Nextmv package dependency latest check

This script checks if any Nextmv dependencies listed in `requirements.txt` or `pyproject.toml` have newer versions available on PyPI.

## Usage

Run the script using Python:

```bash
python check_dependencies.py
```

The script will output a list of dependencies that have newer versions available, along with the current and latest version numbers. Furthermore, it will ping a specified URL to notify about the outdated dependencies.
