# Usage

RSMetaCheck can be used as a local command-line tool or integrated into your CI/CD pipeline as a GitHub Action.

## Command Line Interface

### Analyze a Single Repository

```bash
poetry run rsmetacheck --input https://github.com/tidyverse/tidyverse
```

### Analyze a Specific Branch

```bash
poetry run rsmetacheck --input https://github.com/tidyverse/tidyverse --branch develop
```

### Analyze Multiple Repositories from a JSON File

Create a `repositories.json` file:

```json
{
  "repositories": [
    "https://github.com/example/repo_1",
    "https://github.com/example/repo_2"
  ]
}
```

Run the analysis:

```bash
poetry run rsmetacheck --input repositories.json
```

## GitHub Action

You can integrate RSMetaCheck into your GitHub workflows:

```yaml
name: RsMetaCheck

on: [push, pull_request]

jobs:
  check-metadata:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: SoftwareUnderstanding/RsMetaCheck@v0.2.1
        with:
          verbose: "false"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
