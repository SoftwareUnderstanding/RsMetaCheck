[![Documentation Status](https://readthedocs.org/projects/rsmetacheck/badge/?version=latest)](https://rsmetacheck.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18956787.svg)](https://doi.org/10.5281/zenodo.18956787)
[![PyPI - Version](https://img.shields.io/pypi/v/rsmetacheck)](https://pypi.org/project/rsmetacheck/)

# Research Software MetaCheck (a Pitfall/Warning Detection Tool)

This project provides an automated tool for detecting common metadata quality issues (pitfalls & Warnings)
in software repositories. The tool analyzes SoMEF (Software Metadata Extraction Framework) output
files to identify various problems in repository metadata
files such as `codemeta.json`, `package.json`, `setup.py`, `DESCRIPTION`, and others.

## Overview

MetaCheck identifies **29 different types of metadata quality issues** across multiple programming languages
(Python, Java, C++, C, R, Rust). These pitfalls range from version mismatches and
license template placeholders to broken URLs and improperly formatted metadata fields.

You can visit our [catalog](https://softwareunderstanding.github.io/RsMetaCheck/) to see in details what these pitfalls are, where are they usually detected and how to fix them.

### Supported Pitfall Types

The tool detects the following categories of issues:

- **Version-related pitfalls**: Version mismatches between metadata files and releases
- **License-related pitfalls**: Template placeholders, copyright-only licenses, missing version specifications
- **URL validation pitfalls**: Broken links for CI, software requirements, download URLs
- **Metadata format pitfalls**: Improper field formatting, multiple authors in single fields, etc...
- **Identifier pitfalls**: Invalid or missing unique identifiers, bare DOIs
- **Repository reference pitfalls**: Mismatched code repositories, Git shorthand usage

## Requirements

- **Python 3.11**
- Required Python packages:
  - `requests` (for URL validation)
  - `pathlib` (built-in)
  - `json` (built-in)
  - `re` (built-in)
  - `somef` (For extracting metadata from the repositories)

## Installation

### Using Poetry (Recommended)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/SoftwareUnderstanding/RsMetaCheck.git
   cd RsMetaCheck
   ```

2. **Install with Poetry**:

   ```bash
   poetry install
   ```

3. **Configure SoMEF** (optional but recommended):
   Initially, the installation process will run `somef configure -a` to automatically set it up and install the necessary packages but the rate limit will be low. If you need more, you should reconfigure SoMEF, you can run the following command:
   ```bash
   poetry run somef configure
   ```
   Then add your GitHub authentication token to avoid API rate limits when analyzing repositories in batches.

### Using pip

Alternatively, you can install directly from GitHub:

```bash
pip install git+https://github.com/SoftwareUnderstanding/RsMetaCheck.git
```

## Usage

For full usage instructions — including CLI options, GitHub Action integration, GitLab CI/CD setup, output format, and configuration — please refer to the [usage documentation](https://rsmetacheck.readthedocs.io/en/latest/usage/).

## Troubleshooting

### Common Issues

1. **"There is no valid repository URL" error**: Ensure the JSON file that contains the repositories
   has a valid structure and that you are inputing the correct path
2. **Network timeouts**: Some pitfalls validate URLs and may time out this is normal behavior

### Performance Notes

- URL validation pitfalls may take longer due to network requests
- Large datasets may require several minutes to complete analysis
- Progress is displayed in real-time showing which pitfalls are found

## Contributing

The system is designed with modularity in mind. Each pitfall detector is implemented as a
separate module in the `scripts/` directory, making it easy to add new pitfall types or modify
existing detection logic.
