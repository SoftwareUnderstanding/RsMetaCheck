# Installation

RSMetaCheck requires **Python 3.11**.

## Using Poetry (Recommended)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/SoftwareUnderstanding/RsMetaCheck.git
   cd RsMetaCheck
   ```

2. **Install with Poetry**:

   ```bash
   poetry install
   ```

3. **Configure SoMEF** (Optional but recommended):

   Initially, the installation process runs `somef configure -a` automatically. If you need to reconfigure it (e.g., to add a GitHub token to avoid rate limits), run:

   ```bash
   poetry run somef configure
   ```

## Using pip

Alternatively, you can install directly from GitHub:

```bash
pip install git+https://github.com/SoftwareUnderstanding/RsMetaCheck.git
```
