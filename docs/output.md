# Output

When you run RSMetaCheck, it generates several files containing the results of the analysis.

## Generated Files

*   **all_pitfalls_results.json**: A comprehensive report containing summary statistics of all analyzed repositories.
*   **pitfalls/*.jsonld**: Detailed JSON-LD files for each analyzed repository, containing the specific pitfalls and warnings detected.
*   **somef_outputs/*.json**: The raw metadata extracted by SoMEF for each repository.

## Report Contents

The comprehensive report (`all_pitfalls_results.json`) includes:

1.  **Summary Statistics**: Total repositories analyzed, success rate, and overall health.
2.  **Pitfall Breakdown**: A count and percentage for each type of pitfall detected across the entire batch.
3.  **Language Breakdown**: Statistics specific to different programming languages (Python, Java, R, etc.).
4.  **Standardized Output**: Each repository's results are provided in a standardized JSON-LD format.

## Verbose Mode

By default, the output files only contain detected pitfalls and warnings. If you want to include all tests (even those that passed), use the `--verbose` flag during execution:

```bash
poetry run rsmetacheck --input <url> --verbose
```
