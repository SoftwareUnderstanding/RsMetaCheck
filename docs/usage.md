# Usage

RSMetaCheck can be used as a local command-line tool or integrated into your CI/CD pipeline as a GitHub Action or a GitLab CI/CD job.

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

### Configure Analysis Rules

RsMetaCheck can load a root-level `.rsmetacheck.toml` file to customize analysis behavior.

```toml
ignore = ["W002"]
exclude_files = ["tmp_metadata.json"]

[parameters.P001]
ahead_significant_diff = 10

[profiles.prerelease]
ignore = []

[profiles.unstable]
ignore = ["W002", "P017"]
```

Use a profile:

```bash
poetry run rsmetacheck --input https://github.com/example/repo --config-profile unstable
```

Use an explicit config path:

```bash
poetry run rsmetacheck --input https://github.com/example/repo --config ./ci/rsmetacheck.toml
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

SoMEF fetches repository metadata from GitHub's API. Without a token, anonymous requests are subject to low rate limits. To avoid this, store your GitHub personal access token as a [GitLab CI/CD variable](https://docs.gitlab.com/ee/ci/variables/) named `GITHUB_TOKEN` and pass it to `somef configure`:

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
