import re
from typing import Dict, Optional, List, Union
from rsmetacheck.utils.pitfall_utils import normalize_version
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def _parse_version_components(version_str: str) -> tuple:
    cleaned = re.sub(r"[-_.]?(dev|alpha|beta|rc|pre|post|a|b)\d*.*", "", version_str, flags=re.IGNORECASE)
    parts = re.findall(r"\d+", cleaned)
    components = [int(p) for p in parts[:3]]
    while len(components) < 3:
        components.append(0)
    return tuple(components)


def _version_diff_significant(v1: str, v2: str) -> bool:
    c1 = _parse_version_components(v1)
    c2 = _parse_version_components(v2)
    for a, b in zip(c1, c2):
        if abs(a - b) >= 2:
            return True
    return False


def _metadata_ahead_of_release(metadata_version: str, release_version: str) -> bool:
    mc = _parse_version_components(metadata_version)
    rc = _parse_version_components(release_version)
    return mc > rc


def extract_version_from_metadata(somef_data: Dict) -> list:
    """
    Extract versions from all metadata files (codemeta.json, DESCRIPTION, etc.) in SoMEF output.
    Returns a list of dicts with source and version.
    Handles source being a single string or a list of strings (SoMEF aggregates when same value
    appears in multiple files).
    """
    if "version" not in somef_data:
        return []

    version_entries = somef_data["version"]
    if not isinstance(version_entries, list):
        return []

    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    results = []

    for entry in version_entries:
        if "source" in entry:
            sources = entry["source"]
            if not isinstance(sources, list):
                sources = [sources]
            for source in sources:
                if any(meta_file in source for meta_file in metadata_sources):
                    if "result" in entry and "value" in entry["result"]:
                        results.append({
                            "source": source,
                            "version": entry["result"]["value"]
                        })
        elif "result" in entry and "source" in entry["result"]:
            sources = entry["result"]["source"]
            if not isinstance(sources, list):
                sources = [sources]
            for source in sources:
                if any(meta_file in source for meta_file in metadata_sources):
                    if "value" in entry["result"]:
                        results.append({
                            "source": source,
                            "version": entry["result"]["value"]
                        })

    return results


def extract_latest_release_version(somef_data: Dict) -> Optional[str]:
    """
    Extract the version from the latest release (first element in releases array).
    """
    if "releases" not in somef_data:
        return None

    releases = somef_data["releases"]
    if not isinstance(releases, list) or len(releases) == 0:
        return None

    latest_release = releases[0]

    if isinstance(latest_release, dict):
        if "tag" in latest_release:
            return latest_release["tag"]
        elif "result" in latest_release and isinstance(latest_release["result"], dict):
            if "tag" in latest_release["result"]:
                return latest_release["result"]["tag"]

    return None

def detect_version_mismatch(somef_data: Dict, file_name: str) -> list:
    """
    Detect version mismatches between metadata files and the latest release.
    Checks all metadata files and returns one result dict per metadata source
    that has an inconsistency.

    - Metadata version > release by >= 2 in any component: pitfall
    - Metadata version > release by < 2: note (best practice to prepare ahead)
    - Metadata version < release: pitfall (metadata was not updated)
    - Metadata version == release: no issue
    """
    metadata_versions = extract_version_from_metadata(somef_data)
    release_version = extract_latest_release_version(somef_data)

    if not metadata_versions or not release_version:
        return []

    normalized_release_version = normalize_version(release_version)
    results = []

    for md_info in metadata_versions:
        metadata_version = normalize_version(md_info["version"])
        metadata_source_file = extract_metadata_source_filename(md_info["source"])

        if metadata_version == normalized_release_version:
            continue

        if _metadata_ahead_of_release(metadata_version, normalized_release_version):
            if _version_diff_significant(metadata_version, normalized_release_version):
                results.append({
                    "has_pitfall": True,
                    "has_note": False,
                    "file_name": file_name,
                    "metadata_version": metadata_version,
                    "release_version": normalized_release_version,
                    "metadata_source": md_info["source"],
                    "metadata_source_file": metadata_source_file,
                    "note_text": None,
                    "notes": []
                })
            else:
                note_text = f"Version discrepancy: {metadata_source_file} version '{metadata_version}' is ahead of release version '{normalized_release_version}'"
                results.append({
                    "has_pitfall": False,
                    "has_note": True,
                    "file_name": file_name,
                    "metadata_version": metadata_version,
                    "release_version": normalized_release_version,
                    "metadata_source": md_info["source"],
                    "metadata_source_file": metadata_source_file,
                    "note_text": note_text,
                    "notes": [{
                        "metadata_source_file": metadata_source_file,
                        "metadata_version": metadata_version,
                        "release_version": normalized_release_version,
                        "note_text": note_text
                    }]
                })
        else:
            results.append({
                "has_pitfall": True,
                "has_note": False,
                "file_name": file_name,
                "metadata_version": metadata_version,
                "release_version": normalized_release_version,
                "metadata_source": md_info["source"],
                "metadata_source_file": metadata_source_file,
                "note_text": None,
                "notes": []
            })

    return results