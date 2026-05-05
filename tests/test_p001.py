import pytest
from unittest.mock import patch
from rsmetacheck.scripts.pitfalls.p001 import (
    extract_version_from_metadata,
    extract_latest_release_version,
    detect_version_mismatch
)


class TestExtractVersionFromMetadata:
    """Test suite for extract_version_from_metadata function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No version key
        ({}, None),
        ({"other_key": "value"}, None),

        # Version not a list
        ({"version": "1.0.0"}, None),
        ({"version": {}}, None),

        # Empty version list
        ({"version": []}, None),

        # Version from codemeta.json with source at top level
        ({
             "version": [{
                 "source": "repository/codemeta.json",
                 "result": {"value": "1.2.3"}
             }]
         },
         {"source": "repository/codemeta.json", "version": "1.2.3"}),

        # Version from DESCRIPTION file
        ({
             "version": [{
                 "source": "repository/DESCRIPTION",
                 "result": {"value": "2.0.1"}
             }]
         }, {"source": "repository/DESCRIPTION", "version": "2.0.1"}),

        # Version from package.json
        ({
             "version": [{
                 "source": "repository/package.json",
                 "result": {"value": "3.1.4"}
             }]
         }, {"source": "repository/package.json", "version": "3.1.4"}),

        # Version with result.source structure
        ({
             "version": [{
                 "result": {
                     "source": "repository/pyproject.toml",
                     "value": "0.5.0"
                 }
             }]
         }, {"source": "repository/pyproject.toml", "version": "0.5.0"}),


        # Missing result or value
        ({
             "version": [{
                 "source": "repository/codemeta.json"
             }]
         }, None),
        ({
             "version": [{
                 "source": "repository/codemeta.json",
                 "result": {}
             }]
         }, None),
    ])
    def test_extract_version_scenarios(self, somef_data, expected):
        """Test various scenarios for version extraction"""
        result = extract_version_from_metadata(somef_data)
        assert result == expected


class TestExtractLatestReleaseVersion:
    """Test suite for extract_latest_release_version function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No releases key
        ({}, None),
        ({"other_key": "value"}, None),

        # Releases not a list
        ({"releases": "v1.0.0"}, None),
        ({"releases": {}}, None),

        # Empty releases list
        ({"releases": []}, None),

        # Release with tag at top level
        ({
             "releases": [{"tag": "v1.0.0"}]
         }, "v1.0.0"),

        # Release with tag in result
        ({
             "releases": [{
                 "result": {"tag": "v2.3.1"}
             }]
         }, "v2.3.1"),

        # Multiple releases (should return first)
        ({
             "releases": [
                 {"tag": "v3.0.0"},
                 {"tag": "v2.9.9"},
                 {"tag": "v2.5.0"}
             ]
         }, "v3.0.0"),

        # Release without tag
        ({
             "releases": [{"name": "Release 1.0"}]
         }, None),

        # Release with nested result but no tag
        ({
             "releases": [{
                 "result": {"name": "Release"}
             }]
         }, None),

        # Non-dict release entry
        ({
             "releases": ["v1.0.0"]
         }, None),
    ])
    def test_extract_release_scenarios(self, somef_data, expected):
        """Test various scenarios for release version extraction"""
        result = extract_latest_release_version(somef_data)
        assert result == expected


class TestDetectVersionMismatch:
    """Test suite for detect_version_mismatch function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_metadata_ver,expected_release_ver,expected_has_note", [
        # No version mismatch - versions match
        (
                {
                    "version": [{
                        "source": "repo/codemeta.json",
                        "result": {"value": "v1.0.0"}
                    }],
                    "releases": [{"tag": "v1.0.0"}]
                },
                "test_repo.json",
                False,
                "1.0.0",
                "1.0.0",
                False
        ),

        # Version mismatch but release is ahead (metadata behind) - should not flag
        (
                {
                    "version": [{
                        "source": "repo/package.json",
                        "result": {"value": "1.2.3"}
                    }],
                    "releases": [{"tag": "v2.0.0"}]
                },
                "test_repo.json",
                False,
                "1.2.3",
                "2.0.0",
                False
        ),

        # No metadata version
        (
                {
                    "releases": [{"tag": "v1.0.0"}]
                },
                "test_repo.json",
                False,
                None,
                None,
                False
        ),

        # No release version
        (
                {
                    "version": [{
                        "source": "repo/codemeta.json",
                        "result": {"value": "1.0.0"}
                    }]
                },
                "test_repo.json",
                False,
                None,
                None,
                False
        ),

        # Version mismatch with normalization (v prefix) - release ahead, no flag
        (
                {
                    "version": [{
                        "source": "repo/setup.py",
                        "result": {"value": "2.5.0"}
                    }],
                    "releases": [{"tag": "v2.5.1"}]
                },
                "another_repo.json",
                False,
                "2.5.0",
                "2.5.1",
                False
        ),

        # Significant version diff, metadata ahead of release (0.12.4 vs 0.12.1) - should be pitfall
        (
                {
                    "version": [{
                        "source": "repo/codemeta.json",
                        "result": {"value": "0.12.4"}
                    }],
                    "releases": [{"tag": "0.12.1"}]
                },
                "big_diff_repo.json",
                True,
                "0.12.4",
                "0.12.1",
                False
        ),

        # Small version diff, metadata ahead of release (0.4.3 vs 0.4.2) - should be note only
        (
                {
                    "version": [{
                        "source": "repo/codemeta.json",
                        "result": {"value": "0.4.3"}
                    }],
                    "releases": [{"tag": "0.4.2"}]
                },
                "small_diff_repo.json",
                False,
                "0.4.3",
                "0.4.2",
                True
        ),

        # Pre-release vs stable, metadata ahead (0.4.3.dev1 vs 0.4.2) - should be note
        (
                {
                    "version": [{
                        "source": "repo/codemeta.json",
                        "result": {"value": "0.4.3.dev1"}
                    }],
                    "releases": [{"tag": "0.4.2"}]
                },
                "prerelease_repo.json",
                False,
                "0.4.3.dev1",
                "0.4.2",
                True
        ),
    ])
    def test_detect_mismatch_scenarios(self, somef_data, file_name,
                                       expected_has_pitfall, expected_metadata_ver,
                                       expected_release_ver, expected_has_note):
        """Test various version mismatch detection scenarios"""
        with patch('rsmetacheck.scripts.pitfalls.p001.normalize_version', side_effect=lambda x: x.lstrip('v')):
            with patch('rsmetacheck.scripts.pitfalls.p001.extract_metadata_source_filename', return_value="test_file"):
                result = detect_version_mismatch(somef_data, file_name)

                assert result["has_pitfall"] == expected_has_pitfall
                assert result["has_note"] == expected_has_note
                assert result["file_name"] == file_name
                assert result["metadata_version"] == expected_metadata_ver
                assert result["release_version"] == expected_release_ver

                if expected_has_pitfall:
                    assert result["metadata_source"] is not None
                    assert result["metadata_source_file"] is not None

                if expected_has_note:
                    assert result["note_text"] is not None

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_version_mismatch(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "has_note" in result
        assert "file_name" in result
        assert "metadata_version" in result
        assert "release_version" in result
        assert "metadata_source" in result
        assert "metadata_source_file" in result
        assert "note_text" in result