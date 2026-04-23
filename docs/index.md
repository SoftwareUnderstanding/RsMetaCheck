# Research Metadata Check (RSMetaCheck) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18956787.svg)](https://doi.org/10.5281/zenodo.18956787) [![PyPI - Version](https://img.shields.io/pypi/v/rsmetacheck)](https://pypi.org/project/rsmetacheck/)

**RSMetaCheck** is an automated tool for detecting common metadata quality issues (pitfalls & warnings) in software repositories.
The tool analyzes SoMEF (Software Metadata Extraction Framework) output files to identify various problems in repository metadata
files such as `codemeta.json`, `package.json`, `setup.py`, `DESCRIPTION`, and others.

## Features

RSMetaCheck identifies **29 different types of metadata quality issues** across multiple programming languages (Python, Java, C++, C, R, Rust).

- **Version Consistency**: Detects mismatches between metadata files and actual software releases.
- **License Validation**: Identifies template placeholders, missing versions, and legal ambiguities in licenses.
- **Link Verification**: Checks for broken URLs in CI configurations, software requirements, and download links.
- **Metadata Formatting**: Validates field structures, author lists, and unique identifiers (DOIs, SWHIDs).
- **Repository Integrity**: Ensures codeRepository fields point to the correct source and avoid git shorthands.
