# Usage

RSMetaCheck can be used as a local command-line tool or integrated into your CI/CD pipeline as a GitHub Action or a GitLab CI/CD job.

## Command Line Interface

### Analyze a Single Repository

```bash
poetry run rsmetacheck --input https://github.com/tidyverse/tidyverse
```

### Analyze a Specific Branch

Use `--branch` (short: `-b`) to target a non-default branch:

```bash
poetry run rsmetacheck --input https://github.com/tidyverse/tidyverse --branch develop
```

### Analyze Multiple Repositories

Pass several URLs directly on the command line:

```bash
poetry run rsmetacheck --input https://github.com/example/repo_1 https://github.com/example/repo_2
```

Or create a `repositories.json` file and pass it as the input:

```json
{
  "repositories": [
    "https://github.com/example/repo_1",
    "https://github.com/example/repo_2"
  ]
}
```

```bash
poetry run rsmetacheck --input repositories.json
```

### Customize Output Paths

By default RSMetaCheck writes its output to the current working directory. Use the flags below to redirect any of the outputs:

| Flag | Default | Description |
|------|---------|-------------|
| `--somef-output` | `./somef_outputs` | Directory for raw SoMEF JSON files |
| `--pitfalls-output` | `./pitfalls_outputs` | Directory for per-repository pitfall JSON-LD files |
| `--analysis-output` | `./analysis_results.json` | File for the overall summary report |
| `--notes-output` | *(not created)* | File for minor version-discrepancy notes (see below) |

```bash
poetry run rsmetacheck --input repositories.json \
  --somef-output ./results/somef \
  --pitfalls-output ./results/pitfalls \
  --analysis-output ./results/summary.json \
  --notes-output ./results/notes.json
```

### Version Discrepancy Notes

When a metadata version differs from the release version only slightly (every component differs by less than 2, e.g. `0.4.3.dev1` vs `0.4.2`), RSMetaCheck records a **note** instead of a full pitfall. Notes are only written when `--notes-output` is provided:

```bash
poetry run rsmetacheck --input https://github.com/example/repo --notes-output ./notes.json
```

Example notes file:

```json
{
  "total_notes": 1,
  "notes": [
    {
      "repository": "example/repo",
      "file_name": "repo_output.json",
      "code": "P001",
      "note": "Version discrepancy: metadata '0.4.3.dev1' vs release '0.4.2'"
    }
  ]
}
```

When the difference is significant (any component differs by 2 or more, e.g. `0.12.4` vs `0.12.1`), the issue is still reported as a pitfall regardless.

### Skip SoMEF and Analyze Existing Outputs

If you have already run SoMEF separately, pass `--skip-somef` and point `--input` at the existing JSON files to avoid re-running SoMEF:

```bash
poetry run rsmetacheck --skip-somef --input somef_outputs/*.json
```

Multiple glob patterns are supported:

```bash
poetry run rsmetacheck --skip-somef --input my_somef_outputs_1/*.json my_somef_outputs_2/*.json
```

### Verbose Output

By default, only detected pitfalls and warnings appear in the output JSON-LD files. Use `--verbose` to also include checks that passed:

```bash
poetry run rsmetacheck --input https://github.com/tidyverse/tidyverse --verbose
```

### SoMEF Confidence Threshold

Use `--threshold` to control how confident SoMEF must be before including a metadata field (default: `0.8`):

```bash
poetry run rsmetacheck --input https://github.com/example/repo --threshold 0.6
```

### Generate CodeMeta Files

Use `-c` / `--generate-codemeta` to instruct SoMEF to also produce a `codemeta.json` file for each repository:

```bash
poetry run rsmetacheck --input https://github.com/example/repo --generate-codemeta
```

### Configure Analysis Rules

RSMetaCheck automatically detects a `.rsmetacheck.toml` (or `rsmetacheck.toml`) file at the working directory. Alternatively, supply a custom path with `--config`:

```bash
poetry run rsmetacheck --input https://github.com/example/repo --config ./ci/rsmetacheck.toml
```

Supported configuration keys:

- `ignore` — list of pitfall/warning codes to skip (e.g. `"P001"`, `"W002"`)
- `exclude_files` — glob patterns, filenames, or substrings of metadata sources to ignore
- `parameters` — per-check tunable parameters
- `active_profile` — name of the profile to activate automatically when no `--config-profile` flag is passed
- `profiles` — named groups of overrides that can be selected at runtime

Full example:

```toml
ignore = ["W002"]
exclude_files = ["**/generated/**", "tmp_metadata.json"]
active_profile = "unstable"

[parameters.P001]
ahead_significant_diff = 2

[parameters.W002]
stale_after_days = 3

[profiles.unstable]
ignore = ["W002", "P017"]

[profiles.unstable.parameters.P001]
ahead_significant_diff = 10

[profiles.prerelease]
ignore = []

[profiles.prerelease.parameters.P001]
ahead_significant_diff = 1
```

Activate a profile from the command line (overrides `active_profile`):

```bash
poetry run rsmetacheck --input https://github.com/example/repo --config-profile unstable
```

## GitHub Action

You can integrate RSMetaCheck into your GitHub workflow to test your own repository and detect issues automatically.
Please refer to our action in the GitHub MarketPlace at [rsmetacheck actions](https://github.com/marketplace/actions/rsmetacheck) for more information.

## GitLab CI/CD

You can integrate RSMetaCheck into your GitLab pipelines by adding the following snippet to your `.gitlab-ci.yml` file:

```yaml
rsmetacheck:
  image: python:3.11
  stage: test
  script:
    - pip install rsmetacheck
    - somef configure -a
    - rsmetacheck --input $CI_PROJECT_URL
  artifacts:
    paths:
      - pitfalls_outputs/
      - somef_outputs/
      - analysis_results.json
    when: always
    expire_in: 1 week
```

`$CI_PROJECT_URL` is a [built-in GitLab CI/CD variable](https://docs.gitlab.com/ee/ci/variables/predefined_variables.html) that automatically resolves to your repository's URL.

### Providing a GitHub Token (recommended)

SoMEF fetches repository metadata from GitHub's API. Without a token, anonymous requests are subject to low rate limits. Store your GitHub personal access token as a [GitLab CI/CD variable](https://docs.gitlab.com/ee/ci/variables/) named `GITHUB_TOKEN` and pass it to `somef configure`:

```yaml
rsmetacheck:
  image: python:3.11
  stage: test
  script:
    - pip install rsmetacheck
    - somef configure -a -t $GITHUB_TOKEN
    - rsmetacheck --input $CI_PROJECT_URL
  artifacts:
    paths:
      - pitfalls_outputs/
      - somef_outputs/
      - analysis_results.json
    when: always
    expire_in: 1 week
```

