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
        ({}, []),
        ({"other_key": "value"}, []),

        # Version not a list
        ({"version": "1.0.0"}, []),
        ({"version": {}}, []),

        # Empty version list
        ({"version": []}, []),

        # Version from codemeta.json with source at top level
        ({
             "version": [{
                 "source": "repository/codemeta.json",
                 "result": {"value": "1.2.3"}
             }]
         },
         [{"source": "repository/codemeta.json", "version": "1.2.3"}]),

        # Version from DESCRIPTION file
        ({
             "version": [{
                 "source": "repository/DESCRIPTION",
                 "result": {"value": "2.0.1"}
             }]
         }, [{"source": "repository/DESCRIPTION", "version": "2.0.1"}]),

        # Version from package.json
        ({
             "version": [{
                 "source": "repository/package.json",
                 "result": {"value": "3.1.4"}
             }]
         }, [{"source": "repository/package.json", "version": "3.1.4"}]),

        # Version with result.source structure
        ({
             "version": [{
                 "result": {
                     "source": "repository/pyproject.toml",
                     "value": "0.5.0"
                 }
             }]
         }, [{"source": "repository/pyproject.toml", "version": "0.5.0"}]),

        # Multiple metadata versions
        ({
             "version": [
                 {"source": "repository/codemeta.json", "result": {"value": "1.2.3"}},
                 {"source": "repository/pyproject.toml", "result": {"value": "0.5.0"}},
             ]
         },
         [
             {"source": "repository/codemeta.json", "version": "1.2.3"},
             {"source": "repository/pyproject.toml", "version": "0.5.0"},
         ]),

        # Non-metadata source mixed with metadata (only metadata returned)
        ({
             "version": [
                 {"source": "repository/README.md", "result": {"value": "1.2.3"}},
                 {"source": "repository/codemeta.json", "result": {"value": "1.0.0"}},
             ]
         },
         [{"source": "repository/codemeta.json", "version": "1.0.0"}]),

        # Missing result or value
        ({
             "version": [{
                 "source": "repository/codemeta.json"
             }]
         }, []),
        ({
             "version": [{
                 "source": "repository/codemeta.json",
                 "result": {}
             }]
         }, []),

        # Source as a list (SoMEF aggregate when same value in multiple files)
        ({
             "version": [{
                 "source": [
                     "https://raw.githubusercontent.com/user/repo/main/codemeta.json",
                     "https://raw.githubusercontent.com/user/repo/main/pyproject.toml",
                 ],
                 "result": {"value": "0.3.1"}
             }]
         },
         [
             {"source": "https://raw.githubusercontent.com/user/repo/main/codemeta.json", "version": "0.3.1"},
             {"source": "https://raw.githubusercontent.com/user/repo/main/pyproject.toml", "version": "0.3.1"},
         ]),

        # result.source as a list
        ({
             "version": [{
                 "result": {
                     "source": [
                         "https://raw.githubusercontent.com/user/repo/main/codemeta.json",
                         "https://raw.githubusercontent.com/user/repo/main/package.json",
                     ],
                     "value": "1.0.0"
                 }
             }]
         },
         [
             {"source": "https://raw.githubusercontent.com/user/repo/main/codemeta.json", "version": "1.0.0"},
             {"source": "https://raw.githubusercontent.com/user/repo/main/package.json", "version": "1.0.0"},
         ]),
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

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_metadata_ver,expected_release_ver,expected_has_note,expected_count", [
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
                False,
                0
        ),

        # Version mismatch - release ahead of metadata (metadata behind) → PITFALL
        (
                {
                    "version": [{
                        "source": "repo/package.json",
                        "result": {"value": "1.2.3"}
                    }],
                    "releases": [{"tag": "v2.0.0"}]
                },
                "test_repo.json",
                True,
                "1.2.3",
                "2.0.0",
                False,
                1
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
                False,
                0
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
                False,
                0
        ),

        # Release ahead of metadata (minor version behind) → PITFALL
        (
                {
                    "version": [{
                        "source": "repo/setup.py",
                        "result": {"value": "2.5.0"}
                    }],
                    "releases": [{"tag": "v2.5.1"}]
                },
                "another_repo.json",
                True,
                "2.5.0",
                "2.5.1",
                False,
                1
        ),

        # Metadata significantly ahead of release (diff >= 2) → PITFALL
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
                False,
                1
        ),

        # Metadata slightly ahead of release → NOTE
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
                True,
                1
        ),

        # Pre-release ahead of stable release → NOTE
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
                True,
                1
        ),
    ])
    def test_detect_mismatch_scenarios(self, somef_data, file_name,
                                       expected_has_pitfall, expected_metadata_ver,
                                       expected_release_ver, expected_has_note,
                                       expected_count):
        """Test various version mismatch detection scenarios"""
        with patch('rsmetacheck.scripts.pitfalls.p001.normalize_version', side_effect=lambda x: x.lstrip('v')):
            with patch('rsmetacheck.scripts.pitfalls.p001.extract_metadata_source_filename', return_value="test_file"):
                results = detect_version_mismatch(somef_data, file_name)

                assert isinstance(results, list)
                assert len(results) == expected_count

                if expected_count > 0:
                    result = results[0]
                    assert result["has_pitfall"] == expected_has_pitfall
                    assert result["has_note"] == expected_has_note
                    assert result["file_name"] == file_name
                    if expected_metadata_ver is not None:
                        assert result["metadata_version"] == expected_metadata_ver
                        assert result["release_version"] == expected_release_ver
                    if expected_has_pitfall:
                        assert result["metadata_source"] is not None
                        assert result["metadata_source_file"] is not None
                    if expected_has_note:
                        assert result["note_text"] is not None

    def test_result_structure(self):
        """Test that result for empty data returns an empty list"""
        somef_data = {}
        results = detect_version_mismatch(somef_data, "test.json")
        assert results == []

    def test_result_dict_structure(self):
        """Test that each result dict has the expected structure"""
        somef_data = {
            "version": [{"source": "repo/codemeta.json", "result": {"value": "0.4.3"}}],
            "releases": [{"tag": "0.4.2"}]
        }
        with patch('rsmetacheck.scripts.pitfalls.p001.normalize_version', side_effect=lambda x: x.lstrip('v')):
            with patch('rsmetacheck.scripts.pitfalls.p001.extract_metadata_source_filename', return_value="test_file"):
                results = detect_version_mismatch(somef_data, "test.json")

        assert len(results) == 1
        result = results[0]
        assert "has_pitfall" in result
        assert "has_note" in result
        assert "file_name" in result
        assert "metadata_version" in result
        assert "release_version" in result
        assert "metadata_source" in result
        assert "metadata_source_file" in result
        assert "note_text" in result
        assert "notes" in result
        assert isinstance(result["notes"], list)

    def test_multiple_metadata_sources_all_notes(self):
        """Test that multiple metadata sources each produce a separate result dict"""
        somef_data = {
            "version": [
                {"source": "repo/codemeta.json", "result": {"value": "0.4.3"}},
                {"source": "repo/pyproject.toml", "result": {"value": "0.4.3"}},
            ],
            "releases": [{"tag": "0.4.2"}]
        }
        with patch('rsmetacheck.scripts.pitfalls.p001.normalize_version', side_effect=lambda x: x.lstrip('v')):
            with patch('rsmetacheck.scripts.pitfalls.p001.extract_metadata_source_filename', side_effect=lambda x: x.split('/')[-1]):
                results = detect_version_mismatch(somef_data, "test.json")

        assert isinstance(results, list)
        assert len(results) == 2

        assert results[0]["has_note"] is True
        assert results[0]["metadata_source_file"] == "codemeta.json"
        assert results[1]["has_note"] is True
        assert results[1]["metadata_source_file"] == "pyproject.toml"

        assert "version discrepancy" in results[0]["note_text"].lower()
        assert "version discrepancy" in results[1]["note_text"].lower()

    def test_multiple_metadata_sources_pitfall_and_note(self):
        """Test pitfall from one source (version behind release) and note from another (version ahead)"""
        somef_data = {
            "version": [
                {"source": "repo/codemeta.json", "result": {"value": "0.9.0"}},
                {"source": "repo/pyproject.toml", "result": {"value": "1.0.1"}},
            ],
            "releases": [{"tag": "1.0.0"}]
        }
        with patch('rsmetacheck.scripts.pitfalls.p001.normalize_version', side_effect=lambda x: x.lstrip('v')):
            with patch('rsmetacheck.scripts.pitfalls.p001.extract_metadata_source_filename', side_effect=lambda x: x.split('/')[-1]):
                results = detect_version_mismatch(somef_data, "test.json")

        assert isinstance(results, list)
        assert len(results) == 2

        assert results[0]["has_pitfall"] is True
        assert results[0]["metadata_source_file"] == "codemeta.json"
        assert results[1]["has_note"] is True
        assert results[1]["metadata_source_file"] == "pyproject.toml"