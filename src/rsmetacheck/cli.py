import argparse
import json
import os
import sys
from pathlib import Path

from rsmetacheck.config import AnalysisConfig, load_analysis_config
from rsmetacheck.run_analyzer import run_analysis
from rsmetacheck.run_somef import (
    ensure_somef_configured,
    run_somef_batch,
    run_somef_single,
)


def _exit_on_findings(analysis_output: str, analysis_config: AnalysisConfig) -> None:
    try:
        with open(analysis_output) as f:
            data = json.load(f)
    except Exception as e:
        print(f"Warning: Could not read analysis output to evaluate exit code: {e}")
        return

    summary = data.get("summary", {})
    pitfalls = summary.get("total_pitfalls_detected", 0)
    warnings = summary.get("total_warnings_detected", 0)

    should_fail = False
    if analysis_config.fail_on_pitfalls and pitfalls > 0:
        print(f"CI gate: {pitfalls} pitfall(s) detected (fail_on_pitfalls=true).")
        should_fail = True
    if analysis_config.fail_on_warnings and warnings > 0:
        print(f"CI gate: {warnings} warning(s) detected (fail_on_warnings=true).")
        should_fail = True

    if should_fail:
        sys.exit(1)


def cli():
    parser = argparse.ArgumentParser(
        description="Detect metadata pitfalls in software repositories using SoMEF."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more: GitHub/GitLab URLs, JSON files containing repositories, OR existing SoMEF output files when using --skip-somef.",
    )
    parser.add_argument(
        "--skip-somef",
        action="store_true",
        help="Skip SoMEF execution and analyze existing SoMEF output files directly. --input should point to SoMEF JSON files.",
    )
    parser.add_argument(
        "--pitfalls-output",
        default=os.path.join(os.getcwd(), "pitfalls_outputs"),
        help="Directory to store pitfall JSON-LD files (default: ./pitfalls_outputs).",
    )
    parser.add_argument(
        "--somef-output",
        default=os.path.join(os.getcwd(), "somef_outputs"),
        help="Directory to store SoMEF output files (default: ./somef_outputs).",
    )
    parser.add_argument(
        "--analysis-output",
        default=os.path.join(os.getcwd(), "analysis_results.json"),
        help="File path for summary results (default: ./analysis_results.json).",
    )
    parser.add_argument(
        "--notes-output",
        default=None,
        help="File path for notes output (default: None, notes file is not created unless specified).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="SoMEF confidence threshold (default: 0.8). Only used when running SoMEF.",
    )
    parser.add_argument(
        "-b",
        "--branch",
        help="Branch of the repository to analyze. Overrides the default branch. Only used when running SoMEF.",
    )

    parser.add_argument(
        "-c",
        "--generate-codemeta",
        action="store_true",
        help="Generate codemeta files for each repository. Only used when running SoMEF.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include both detected AND undetected pitfalls in the output JSON-LD.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to RsMetaCheck TOML config file (default: auto-detect .rsmetacheck.toml at repository root).",
    )
    parser.add_argument(
        "--config-profile",
        default=None,
        help="Name of config profile to apply (e.g., unstable, prerelease).",
    )

    args = parser.parse_args()

    try:
        analysis_config = load_analysis_config(
            config_path=args.config,
            profile=args.config_profile,
        )
    except (FileNotFoundError, ValueError, OSError, Exception) as exc:
        print(f"Error loading config: {exc}")
        return

    if args.skip_somef:
        print(
            f"Skipping SoMEF execution. Analyzing {len(args.input)} existing SoMEF output files..."
        )

        somef_json_paths = []
        for json_path in args.input:
            if not os.path.exists(json_path):
                print(f"Warning: File not found, skipping: {json_path}")
                continue
            somef_json_paths.append(Path(json_path))

        if not somef_json_paths:
            print("Error: No valid SoMEF output files found.")
            return

        print(f"Analyzing {len(somef_json_paths)} SoMEF output files...")
        run_analysis(
            somef_json_paths,
            args.pitfalls_output,
            args.analysis_output,
            verbose=args.verbose,
            notes_output=args.notes_output,
            analysis_config=analysis_config,
        )

        _exit_on_findings(args.analysis_output, analysis_config)

    else:
        ensure_somef_configured()

        threshold = args.threshold
        somef_output_dir = args.somef_output
        generate_codemeta = args.generate_codemeta

        print(f"Detected {len(args.input)} input(s):")
        if generate_codemeta:
            print(
                "Codemeta generation is ENABLED. Codemeta files will be created for each repository."
            )

        any_somef_success = False

        for input_item in args.input:
            if input_item.startswith("http://") or input_item.startswith("https://"):
                print(f"Processing repository URL: {input_item}")
                success = run_somef_single(
                    input_item,
                    somef_output_dir,
                    threshold,
                    branch=args.branch,
                    generate_codemeta=generate_codemeta,
                )
                any_somef_success = any_somef_success or bool(success)
            elif os.path.exists(input_item):
                print(f"Processing repositories from file: {input_item}")
                success = run_somef_batch(
                    input_item,
                    somef_output_dir,
                    threshold,
                    branch=args.branch,
                    generate_codemeta=generate_codemeta,
                )
                any_somef_success = any_somef_success or bool(success)
            else:
                print(
                    f"Warning: Skipping invalid input (not a URL or existing file): {input_item}"
                )

        if not any_somef_success:
            print(
                "Error: SoMEF did not produce any outputs. Analysis is aborted."
            )
            print(
                "Fix SoMEF/authentication issues and rerun, or run with --skip-somef on existing SoMEF JSON files."
            )
            return

        print(f"\nRunning analysis on outputs in {somef_output_dir}...")
        run_analysis(
            somef_output_dir,
            args.pitfalls_output,
            args.analysis_output,
            verbose=args.verbose,
            notes_output=args.notes_output,
            analysis_config=analysis_config,
        )

        _exit_on_findings(args.analysis_output, analysis_config)


if __name__ == "__main__":
    cli()
