"""Unit tests to verify CLI behavior for codemeta generation."""

import importlib
from unittest.mock import MagicMock

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
