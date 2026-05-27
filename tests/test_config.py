from rsmetacheck.config import load_analysis_config


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
