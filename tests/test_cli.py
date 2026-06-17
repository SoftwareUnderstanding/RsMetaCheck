"""Unit tests verifying CLI argument handling and dispatch."""

import importlib
import json
from unittest.mock import MagicMock

import pytest

from rsmetacheck.config import AnalysisConfig

cli_module = importlib.import_module("rsmetacheck.cli")

REPO_URL = "https://github.com/SoftwareUnderstanding/sw-metadata-bot"


def test_cli_with_generate_codemeta_adds_codemeta_output(monkeypatch, tmp_path):
    """Ensure --generate-codemeta requests codemeta output in SoMEF command."""
    somef_output_dir = tmp_path / "somef_outputs"
    expected_codemeta = str(somef_output_dir / "somef_generated_codemeta.json")

    run_analysis_mock = MagicMock()
    subprocess_run_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
            "--somef-output",
            str(somef_output_dir),
            "--generate-codemeta",
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr("rsmetacheck.run_somef.subprocess.run", subprocess_run_mock)

    cli_module.cli()

    command = subprocess_run_mock.call_args.args[0]
    assert command[0:2] == ["somef", "describe"]
    assert "-c" in command
    assert expected_codemeta in command

    run_analysis_mock.assert_called_once()


def test_cli_without_generate_codemeta_keeps_default_behavior(monkeypatch, tmp_path):
    """Ensure default CLI call does not request codemeta output from SoMEF."""
    somef_output_dir = tmp_path / "somef_outputs"

    run_analysis_mock = MagicMock()
    subprocess_run_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
            "--somef-output",
            str(somef_output_dir),
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr("rsmetacheck.run_somef.subprocess.run", subprocess_run_mock)

    cli_module.cli()

    command = subprocess_run_mock.call_args.args[0]
    assert command[0:2] == ["somef", "describe"]
    assert "-c" not in command

    run_analysis_mock.assert_called_once()


def test_cli_skip_somef_bypasses_somef_execution(monkeypatch, tmp_path):
    """--skip-somef should call run_analysis directly without running SoMEF."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")

    run_analysis_mock = MagicMock()
    ensure_somef_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", ensure_somef_mock)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    ensure_somef_mock.assert_not_called()
    run_analysis_mock.assert_called_once()


def test_cli_skip_somef_with_missing_file_skips_and_warns(monkeypatch, capsys):
    """--skip-somef with a missing file should print a warning and skip."""
    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            "/nonexistent/file.json",
            "--skip-somef",
        ],
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    captured = capsys.readouterr()
    assert "Warning: File not found" in captured.out


def test_cli_verbose_flag_passed_to_run_analysis(monkeypatch, tmp_path):
    """--verbose should be forwarded to run_analysis."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")

    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
            "--verbose",
        ],
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    call_kwargs = run_analysis_mock.call_args.kwargs
    assert call_kwargs.get("verbose") is True


def test_cli_verbose_defaults_to_false(monkeypatch, tmp_path):
    """Default is verbose=False when --verbose is not provided."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")

    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
        ],
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    call_kwargs = run_analysis_mock.call_args.kwargs
    assert call_kwargs.get("verbose") is False


def test_cli_branch_passed_to_somef(monkeypatch, tmp_path):
    """-b / --branch should be forwarded to the somef command."""
    somef_output_dir = tmp_path / "somef_outputs"

    run_analysis_mock = MagicMock()
    subprocess_run_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
            "--somef-output",
            str(somef_output_dir),
            "-b",
            "develop",
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr("rsmetacheck.run_somef.subprocess.run", subprocess_run_mock)

    cli_module.cli()

    command = subprocess_run_mock.call_args.args[0]
    assert "-b" in command
    assert "develop" in command


def test_cli_threshold_passed_to_somef(monkeypatch, tmp_path):
    """--threshold should be forwarded to the somef command."""
    somef_output_dir = tmp_path / "somef_outputs"

    run_analysis_mock = MagicMock()
    subprocess_run_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
            "--somef-output",
            str(somef_output_dir),
            "--threshold",
            "0.5",
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr("rsmetacheck.run_somef.subprocess.run", subprocess_run_mock)

    cli_module.cli()

    command = subprocess_run_mock.call_args.args[0]
    assert "-t" in command
    assert "0.5" in command


def test_cli_notes_output_passed_to_run_analysis(monkeypatch, tmp_path):
    """--notes-output should be forwarded to run_analysis."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")
    notes_path = tmp_path / "notes.json"

    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
            "--notes-output",
            str(notes_path),
        ],
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    call_kwargs = run_analysis_mock.call_args.kwargs
    assert call_kwargs.get("notes_output") == str(notes_path)


def test_cli_custom_pitfalls_output_dir(monkeypatch, tmp_path):
    """--pitfalls-output should be forwarded to run_analysis."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")
    pitfalls_dir = tmp_path / "custom_pitfalls"

    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
            "--pitfalls-output",
            str(pitfalls_dir),
        ],
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    call_args = run_analysis_mock.call_args.args
    assert str(call_args[1]) == str(pitfalls_dir)


def test_cli_custom_analysis_output_path(monkeypatch, tmp_path):
    """--analysis-output should be forwarded to run_analysis."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")
    analysis_file = tmp_path / "custom_summary.json"

    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
            "--analysis-output",
            str(analysis_file),
        ],
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    call_args = run_analysis_mock.call_args.args
    assert str(call_args[2]) == str(analysis_file)


def test_cli_custom_somef_output_dir(monkeypatch, tmp_path):
    """--somef-output should be forwarded to run_somef_single."""
    somef_output_dir = tmp_path / "custom_somef"

    run_analysis_mock = MagicMock()
    run_somef_single_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
            "--somef-output",
            str(somef_output_dir),
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr(cli_module, "run_somef_single", run_somef_single_mock)

    cli_module.cli()

    call_args = run_somef_single_mock.call_args.args
    assert str(call_args[1]) == str(somef_output_dir)


def test_cli_input_url_triggers_run_somef_single(monkeypatch):
    """An HTTP URL as --input should trigger run_somef_single."""
    run_analysis_mock = MagicMock()
    run_somef_single_mock = MagicMock()
    run_somef_batch_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr(cli_module, "run_somef_single", run_somef_single_mock)
    monkeypatch.setattr(cli_module, "run_somef_batch", run_somef_batch_mock)

    cli_module.cli()

    run_somef_single_mock.assert_called_once()
    run_somef_batch_mock.assert_not_called()


def test_cli_input_file_triggers_run_somef_batch(monkeypatch, tmp_path):
    """A JSON file as --input should trigger run_somef_batch."""
    batch_file = tmp_path / "repos.json"
    batch_file.write_text('{"repositories": ["https://github.com/a/b"]}')

    run_analysis_mock = MagicMock()
    run_somef_single_mock = MagicMock()
    run_somef_batch_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(batch_file),
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr(cli_module, "run_somef_single", run_somef_single_mock)
    monkeypatch.setattr(cli_module, "run_somef_batch", run_somef_batch_mock)

    cli_module.cli()

    run_somef_single_mock.assert_not_called()
    run_somef_batch_mock.assert_called_once()


def test_cli_invalid_input_warns(monkeypatch, capsys):
    """Invalid input (not URL, not existing file) should produce a warning."""
    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            "just-a-string-not-a-url-or-file",
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    captured = capsys.readouterr()
    assert "Skipping invalid input" in captured.out


def test_cli_multiple_inputs_triggers_multiple_calls(monkeypatch, tmp_path):
    """Multiple --input values should each be processed."""
    batch_file = tmp_path / "repos.json"
    batch_file.write_text('{"repositories": ["https://github.com/a/b"]}')

    run_analysis_mock = MagicMock()
    run_somef_single_mock = MagicMock()
    run_somef_batch_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
            str(batch_file),
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr(cli_module, "run_somef_single", run_somef_single_mock)
    monkeypatch.setattr(cli_module, "run_somef_batch", run_somef_batch_mock)

    cli_module.cli()

    run_somef_single_mock.assert_called_once()
    run_somef_batch_mock.assert_called_once()


def test_cli_aborts_analysis_when_somef_produces_no_outputs(monkeypatch, capsys):
    """When all SoMEF runs fail, CLI should stop before run_analysis."""
    run_analysis_mock = MagicMock()
    run_somef_single_mock = MagicMock(return_value=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            REPO_URL,
        ],
    )
    monkeypatch.setattr(cli_module, "ensure_somef_configured", lambda: True)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)
    monkeypatch.setattr(cli_module, "run_somef_single", run_somef_single_mock)

    cli_module.cli()

    captured = capsys.readouterr()
    assert "SoMEF did not produce any outputs" in captured.out
    run_analysis_mock.assert_not_called()


def test_cli_input_required(monkeypatch):
    """CLI should fail if --input is not provided."""
    monkeypatch.setattr(
        "sys.argv",
        ["rsmetacheck"],
    )

    try:
        cli_module.cli()
        assert False, "Expected SystemExit"
    except SystemExit:
        pass


def test_cli_config_profile_forwarded_to_run_analysis(monkeypatch, tmp_path):
    """--config and --config-profile should load and forward analysis config."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")

    run_analysis_mock = MagicMock()
    expected_config = AnalysisConfig(profile="unstable")
    load_config_mock = MagicMock(return_value=expected_config)

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
            "--config",
            "custom.toml",
            "--config-profile",
            "unstable",
        ],
    )
    monkeypatch.setattr(cli_module, "load_analysis_config", load_config_mock)
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    load_config_mock.assert_called_once_with(config_path="custom.toml", profile="unstable")
    assert run_analysis_mock.call_args.kwargs["analysis_config"] is expected_config


def test_cli_config_load_error_stops_execution(monkeypatch, tmp_path, capsys):
    """Config loading errors should stop execution and print a message."""
    somef_file = tmp_path / "somef_output.json"
    somef_file.write_text("{}")

    run_analysis_mock = MagicMock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "rsmetacheck",
            "--input",
            str(somef_file),
            "--skip-somef",
            "--config",
            "missing.toml",
        ],
    )
    monkeypatch.setattr(
        cli_module,
        "load_analysis_config",
        MagicMock(side_effect=FileNotFoundError("missing")),
    )
    monkeypatch.setattr(cli_module, "run_analysis", run_analysis_mock)

    cli_module.cli()

    captured = capsys.readouterr()
    assert "Error loading config" in captured.out
    run_analysis_mock.assert_not_called()


def test_exit_on_findings_pitfalls_cause_exit(tmp_path, capsys):
    """Exit code 1 when pitfalls detected and fail_on_pitfalls=True."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "summary": {
            "total_pitfalls_detected": 3,
            "total_warnings_detected": 0,
        }
    }))
    config = AnalysisConfig(fail_on_pitfalls=True, fail_on_warnings=False)

    with pytest.raises(SystemExit) as exc_info:
        cli_module._exit_on_findings(str(analysis_file), config)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "CI gate: 3 pitfall(s) detected" in captured.out


def test_exit_on_findings_warnings_cause_exit(tmp_path, capsys):
    """Exit code 1 when warnings detected and fail_on_warnings=True."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "summary": {
            "total_pitfalls_detected": 0,
            "total_warnings_detected": 2,
        }
    }))
    config = AnalysisConfig(fail_on_pitfalls=False, fail_on_warnings=True)

    with pytest.raises(SystemExit) as exc_info:
        cli_module._exit_on_findings(str(analysis_file), config)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "CI gate: 2 warning(s) detected" in captured.out


def test_exit_on_findings_both_cause_exit(tmp_path, capsys):
    """Exit code 1 when both pitfalls and warnings detected with both flags True."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "summary": {
            "total_pitfalls_detected": 1,
            "total_warnings_detected": 1,
        }
    }))
    config = AnalysisConfig(fail_on_pitfalls=True, fail_on_warnings=True)

    with pytest.raises(SystemExit) as exc_info:
        cli_module._exit_on_findings(str(analysis_file), config)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "CI gate: 1 pitfall(s) detected" in captured.out
    assert "CI gate: 1 warning(s) detected" in captured.out


def test_exit_on_findings_no_exit_when_flags_false(tmp_path):
    """No exit when fail flags are False even with findings."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "summary": {
            "total_pitfalls_detected": 5,
            "total_warnings_detected": 5,
        }
    }))
    config = AnalysisConfig(fail_on_pitfalls=False, fail_on_warnings=False)

    # Should not raise SystemExit
    cli_module._exit_on_findings(str(analysis_file), config)


def test_exit_on_findings_no_exit_with_zero_findings(tmp_path):
    """No exit when zero pitfalls and warnings even with flags True."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "summary": {
            "total_pitfalls_detected": 0,
            "total_warnings_detected": 0,
        }
    }))
    config = AnalysisConfig(fail_on_pitfalls=True, fail_on_warnings=True)

    # Should not raise SystemExit
    cli_module._exit_on_findings(str(analysis_file), config)


def test_exit_on_findings_missing_file_prints_warning(tmp_path, capsys):
    """Missing analysis file should print warning and not exit."""
    config = AnalysisConfig(fail_on_pitfalls=True, fail_on_warnings=True)

    cli_module._exit_on_findings(str(tmp_path / "nonexistent.json"), config)

    captured = capsys.readouterr()
    assert "Warning: Could not read analysis output" in captured.out


def test_exit_on_findings_malformed_json_prints_warning(tmp_path, capsys):
    """Malformed analysis file should print warning and not exit."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text("not valid json")

    config = AnalysisConfig(fail_on_pitfalls=True, fail_on_warnings=True)

    cli_module._exit_on_findings(str(analysis_file), config)

    captured = capsys.readouterr()
    assert "Warning: Could not read analysis output" in captured.out


def test_exit_on_findings_missing_summary_fields_treated_as_zero(tmp_path):
    """Missing summary fields should be treated as 0 (no exit)."""
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({"summary": {}}))

    config = AnalysisConfig(fail_on_pitfalls=True, fail_on_warnings=True)

    # Should not raise SystemExit
    cli_module._exit_on_findings(str(analysis_file), config)
