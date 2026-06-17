from rsmetacheck.config import AnalysisConfig, load_analysis_config


def test_load_analysis_config_auto_detects_default_file(tmp_path):
    config_file = tmp_path / ".rsmetacheck.toml"
    config_file.write_text(
        """
ignore = ["p001", "W002"]
exclude_files = ["codemeta.json"]

[parameters.P001]
ahead_significant_diff = 10
""".strip()
    )

    config = load_analysis_config(cwd=tmp_path)

    assert config.source_path == config_file
    assert config.is_ignored("P001")
    assert config.is_ignored("w002")
    assert config.exclude_files == ["codemeta.json"]
    assert config.get_parameters("P001")["ahead_significant_diff"] == 10


def test_load_analysis_config_merges_profile_overrides(tmp_path):
    config_file = tmp_path / ".rsmetacheck.toml"
    config_file.write_text(
        """
ignore = ["W002"]
exclude_files = ["base.txt"]

[parameters.P001]
ahead_significant_diff = 2

[profiles.unstable]
ignore = ["P017"]
exclude_files = ["dev.txt"]

[profiles.unstable.parameters.P001]
ahead_significant_diff = 10
""".strip()
    )

    config = load_analysis_config(cwd=tmp_path, profile="unstable")

    assert config.profile == "unstable"
    assert config.is_ignored("W002")
    assert config.is_ignored("P017")
    assert config.exclude_files == ["base.txt", "dev.txt"]
    assert config.get_parameters("P001")["ahead_significant_diff"] == 10


def test_load_analysis_config_missing_profile_raises(tmp_path):
    config_file = tmp_path / ".rsmetacheck.toml"
    config_file.write_text('[profiles.unstable]\nignore = ["W002"]\n')

    try:
        load_analysis_config(cwd=tmp_path, profile="prerelease")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_analysis_config_fail_flags_default_to_true():
    """fail_on_pitfalls and fail_on_warnings should default to True."""
    config = AnalysisConfig()
    assert config.fail_on_pitfalls is True
    assert config.fail_on_warnings is True


def test_load_analysis_config_reads_fail_flags_from_toml(tmp_path):
    """fail_on_pitfalls and fail_on_warnings should be read from TOML root."""
    config_file = tmp_path / ".rsmetacheck.toml"
    config_file.write_text(
        """
fail_on_pitfalls = false
fail_on_warnings = false
""".strip()
    )

    config = load_analysis_config(cwd=tmp_path)

    assert config.fail_on_pitfalls is False
    assert config.fail_on_warnings is False


def test_load_analysis_config_fail_flags_default_when_absent(tmp_path):
    """When TOML has no fail flags, they should default to True."""
    config_file = tmp_path / ".rsmetacheck.toml"
    config_file.write_text('ignore = ["P001"]\n')

    config = load_analysis_config(cwd=tmp_path)

    assert config.fail_on_pitfalls is True
    assert config.fail_on_warnings is True


def test_load_analysis_config_profile_overrides_fail_flags(tmp_path):
    """Profile-level fail flags should override base values."""
    config_file = tmp_path / ".rsmetacheck.toml"
    config_file.write_text(
        """
fail_on_pitfalls = true
fail_on_warnings = true

[profiles.permissive]
fail_on_pitfalls = false
fail_on_warnings = false
""".strip()
    )

    config = load_analysis_config(cwd=tmp_path, profile="permissive")

    assert config.fail_on_pitfalls is False
    assert config.fail_on_warnings is False
