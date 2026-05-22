"""Integration tests verifying the full pipeline with mock SoMEF fixtures. We are using mock data from SoMEF to save time running the tests"""

import json
from pathlib import Path

from rsmetacheck.config import AnalysisConfig
from rsmetacheck.detect_pitfalls_main import detect_all_pitfalls
from rsmetacheck.detect_pitfalls_main import main as detect_pitfalls_main


def _make_somef_data(version="1.0.0", release_tag="1.0.0", repo_name="owner/repo"):
    """Create a minimal SoMEF JSON fixture."""
    data = {
        "full_name": [{"result": {"value": repo_name}}],
        "code_repository": [{"result": {"value": f"https://github.com/{repo_name}"}}],
        "version": [
            {"source": "repository/codemeta.json", "result": {"value": version}}
        ],
        "releases": [{"tag": release_tag}],
        "description": [],
        "name": [],
        "owner": [],
        "date_created": [],
        "date_updated": [],
        "license": [],
        "programming_languages": [],
    }
    return data


def _write_somef_file(dir_path, filename, somef_data):
    """Write a SoMEF fixture to a directory."""
    filepath = dir_path / filename
    filepath.write_text(json.dumps(somef_data))
    return filepath


def _find_issue_count(summary_data, code):
    for item in summary_data["pitfalls & warnings"]:
        current_code = item.get("pitfall_code") or item.get("warning_code")
        if current_code == code:
            return item["count"]
    raise AssertionError(f"Code not found in summary: {code}")


class TestSingleRepoPipeline:
    """Tests with a single SoMEF input file."""

    def test_single_file_produces_one_pitfall_jsonld(self, tmp_path):
        """One SoMEF file with a pitfall -> one pitfall JSON-LD output."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="2.0.0", release_tag="1.0.0"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            verbose=False,
        )

        pitfall_files = list(pitfalls_dir.glob("*.jsonld"))
        assert len(pitfall_files) == 1
        assert pitfall_files[0].name == "repo_1_pitfalls.jsonld"

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 1

    def test_single_file_with_no_issues_produces_no_pitfall_jsonld(self, tmp_path):
        """A file with no pitfalls should not produce a pitfall JSON-LD unless verbose."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="1.0.0", release_tag="1.0.0"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            verbose=False,
        )

        pitfall_files = list(pitfalls_dir.glob("*.jsonld"))
        assert len(pitfall_files) == 0

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 1

    def test_single_file_with_verbose_produces_pitfall_jsonld(self, tmp_path):
        """Verbose mode should produce a pitfall JSON-LD even without issues."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="1.0.0", release_tag="1.0.0"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            verbose=True,
        )

        pitfall_files = list(pitfalls_dir.glob("*.jsonld"))
        assert len(pitfall_files) == 1

    def test_notes_output_created_when_specified(self, tmp_path):
        """--notes-output should create the notes file when notes exist."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"
        notes_file = tmp_path / "notes.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="1.0.1", release_tag="1.0.0"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            notes_output=notes_file,
        )

        assert notes_file.exists()
        notes_data = json.loads(notes_file.read_text())
        assert "notes" in notes_data
        assert notes_data["total_notes"] >= 0


class TestMultipleRepoPipeline:
    """Tests with multiple SoMEF input files."""

    def test_two_files_produce_two_pitfall_jsonld(self, tmp_path):
        """Two SoMEF files with pitfalls -> two pitfall JSON-LD outputs."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_a.json",
            _make_somef_data(version="2.0.0", release_tag="1.0.0", repo_name="a/b"),
        )
        _write_somef_file(
            somef_dir,
            "repo_b.json",
            _make_somef_data(version="3.0.0", release_tag="1.0.0", repo_name="c/d"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            verbose=False,
        )

        pitfall_files = sorted(list(pitfalls_dir.glob("*.jsonld")))
        assert len(pitfall_files) == 2
        names = [f.name for f in pitfall_files]
        assert "repo_a_pitfalls.jsonld" in names
        assert "repo_b_pitfalls.jsonld" in names

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 2

    def test_summary_correct_repo_count(self, tmp_path):
        """Summary.json should reflect exactly the number of repos analyzed."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        for i in range(3):
            _write_somef_file(
                somef_dir,
                f"repo_{i}.json",
                _make_somef_data(version="3.0.0", release_tag="1.0.0", repo_name=f"org/repo_{i}"),
            )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            verbose=False,
        )

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 3
        pitfall_files = list(pitfalls_dir.glob("*.jsonld"))
        assert len(pitfall_files) == 3

    def test_no_pitfalls_in_all_repos_zero_count(self, tmp_path):
        """When no repos have pitfalls, pitfall counts should be zero."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        for i in range(2):
            _write_somef_file(
                somef_dir,
                f"repo_{i}.json",
                _make_somef_data(version="1.0.0", release_tag="1.0.0", repo_name=f"org/repo_{i}"),
            )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            verbose=False,
        )

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_pitfalls_detected"] == 0


class TestMainFunctionDispatch:
    """Tests for the main() function, which is what run_analyzer calls."""

    def test_main_with_somef_json_paths(self, tmp_path):
        """main() with somef_json_paths should process given files."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="2.0.0", release_tag="1.0.0"),
        )

        detect_pitfalls_main(
            somef_json_paths=list(somef_dir.glob("*.json")),
            pitfalls_dir=pitfalls_dir,
            analysis_output=summary_file,
        )

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 1

    def test_main_with_input_dir(self, tmp_path):
        """main() with input_dir should scan directory for JSON files."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="2.0.0", release_tag="1.0.0"),
        )

        detect_pitfalls_main(
            input_dir=str(somef_dir),
            pitfalls_dir=pitfalls_dir,
            analysis_output=summary_file,
        )

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 1

    def test_main_verbose(self, tmp_path):
        """main() with verbose=True should forward the flag."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="1.0.0", release_tag="1.0.0"),
        )

        detect_pitfalls_main(
            somef_json_paths=list(somef_dir.glob("*.json")),
            pitfalls_dir=pitfalls_dir,
            analysis_output=summary_file,
            verbose=True,
        )

        pitfall_files = list(pitfalls_dir.glob("*.jsonld"))
        assert len(pitfall_files) == 1


class TestErrorHandling:
    """Tests for graceful error handling."""

    def test_empty_input_list_does_not_crash(self, tmp_path):
        """An empty list of JSON files should not crash."""
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        detect_all_pitfalls(
            [],
            pitfalls_dir,
            summary_file,
        )

        assert pitfalls_dir.exists()

    def test_invalid_json_file_does_not_crash(self, tmp_path):
        """A malformed JSON file should print an error but not crash the pipeline."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        bad_file = somef_dir / "bad.json"
        bad_file.write_text("not valid json {{{")

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
        )

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 1

    def test_pipeline_continues_after_one_bad_file(self, tmp_path):
        """The pipeline should process valid files even if one file is broken."""
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "good.json",
            _make_somef_data(version="2.0.0", release_tag="1.0.0"),
        )
        bad_file = somef_dir / "bad.json"
        bad_file.write_text("{{invalid")

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
        )

        pitfall_files = list(pitfalls_dir.glob("*.jsonld"))
        assert len(pitfall_files) == 1
        assert pitfall_files[0].name.startswith("good")

        summary = json.loads(summary_file.read_text())
        assert summary["summary"]["total_repositories_analyzed"] == 2


class TestAnalysisConfiguration:
    """Tests for root config behavior in analysis."""

    def test_ignore_check_code_skips_detector(self, tmp_path):
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="2.0.0", release_tag="1.0.0"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            analysis_config=AnalysisConfig(ignored_checks={"P001"}),
        )

        summary = json.loads(summary_file.read_text())
        assert _find_issue_count(summary, "P001") == 0

    def test_p001_threshold_override_changes_note_to_pitfall(self, tmp_path):
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        _write_somef_file(
            somef_dir,
            "repo_1.json",
            _make_somef_data(version="0.4.3", release_tag="0.4.2"),
        )

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            analysis_config=AnalysisConfig(
                check_parameters={"P001": {"ahead_significant_diff": 1}}
            ),
        )

        summary = json.loads(summary_file.read_text())
        assert _find_issue_count(summary, "P001") == 1

    def test_exclude_files_removes_source_from_checks(self, tmp_path):
        somef_dir = tmp_path / "somef_inputs"
        somef_dir.mkdir()
        pitfalls_dir = tmp_path / "pitfalls_outputs"
        summary_file = tmp_path / "summary.json"

        somef_data = {
            "full_name": [{"result": {"value": "owner/repo"}}],
            "code_repository": [{"result": {"value": "https://github.com/owner/repo"}}],
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "result": {"value": "2.0.0"},
                }
            ],
            "releases": [{"tag": "1.0.0"}],
            "description": [],
            "name": [],
            "owner": [],
            "date_created": [],
            "date_updated": [],
            "license": [],
            "programming_languages": [],
        }
        _write_somef_file(somef_dir, "repo_1.json", somef_data)

        detect_all_pitfalls(
            list(somef_dir.glob("*.json")),
            pitfalls_dir,
            summary_file,
            analysis_config=AnalysisConfig(exclude_files=["codemeta.json"]),
        )

        summary = json.loads(summary_file.read_text())
        assert _find_issue_count(summary, "P001") == 0
