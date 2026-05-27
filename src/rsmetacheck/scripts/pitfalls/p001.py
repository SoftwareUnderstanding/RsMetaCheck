import re
from typing import Dict, Optional, List
from rsmetacheck.utils.pitfall_utils import normalize_version
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def _parse_version_components(version_str: str) -> tuple:
    cleaned = re.sub(r"[-_.]?(dev|alpha|beta|rc|pre|post|a|b)\d*.*", "", version_str, flags=re.IGNORECASE)
    parts = re.findall(r"\d+", cleaned)
    components = [int(p) for p in parts[:3]]
    while len(components) < 3:
        components.append(0)
    return tuple(components)


def _version_diff_significant(v1: str, v2: str, threshold: int = 2) -> bool:
    c1 = _parse_version_components(v1)
    c2 = _parse_version_components(v2)
    for a, b in zip(c1, c2):
        if abs(a - b) >= threshold:
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

def detect_version_mismatch(
    somef_data: Dict,
    file_name: str,
    ahead_significant_diff: int = 2,
) -> list:
    """
    Detect version mismatches between metadata files and the latest release.
    Returns a single result with all mismatched sources merged into one evidence message.

    - Metadata version > release by >= 2 in any component: pitfall
    - Metadata version > release by < 2: note
    - Metadata version < release: pitfall
    - Metadata version == release: no issue
    """
    metadata_versions = extract_version_from_metadata(somef_data)
    release_version = extract_latest_release_version(somef_data)

    if not metadata_versions or not release_version:
        return []

    normalized_release_version = normalize_version(release_version)

    pitfall_sources = []
    note_sources = []
    all_mismatches = []

    for md_info in metadata_versions:
        metadata_version = normalize_version(md_info["version"])
        metadata_source_file = extract_metadata_source_filename(md_info["source"])

        if metadata_version == normalized_release_version:
            continue

        all_mismatches.append({
            "source_file": metadata_source_file,
            "source": md_info["source"],
            "metadata_version": metadata_version,
        })

        if _metadata_ahead_of_release(metadata_version, normalized_release_version):
            if _version_diff_significant(
                metadata_version,
                normalized_release_version,
                threshold=ahead_significant_diff,
            ):
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
                note_sources.append(metadata_source_file)
        else:
            pitfall_sources.append(metadata_source_file)

    if not all_mismatches:
        return []

    has_any_pitfall = len(pitfall_sources) > 0
    has_any_note = len(note_sources) > 0

    all_source_files = [m["source_file"] for m in all_mismatches]

    # Build notes for any ahead-by-small-amount sources
    notes = []
    note_text = None
    for m in all_mismatches:
        m_version = m["metadata_version"]
        if _metadata_ahead_of_release(m_version, normalized_release_version) and not _version_diff_significant(m_version, normalized_release_version):
            text = f"Version discrepancy: {m['source_file']} version '{m_version}' is ahead of release version '{normalized_release_version}'"
            notes.append({
                "metadata_source_file": m["source_file"],
                "metadata_version": m_version,
                "release_version": normalized_release_version,
                "note_text": text
            })
            if note_text is None:
                note_text = text

    result = {
        "has_pitfall": has_any_pitfall,
        "has_note": (not has_any_pitfall and has_any_note),
        "file_name": file_name,
        "mismatched_sources": all_mismatches,
        "metadata_source_files": all_source_files,
        "release_version": normalized_release_version,
        "note_text": note_text,
        "notes": notes,
        "metadata_version": all_mismatches[0]["metadata_version"] if all_mismatches else None,
        "metadata_source_file": all_mismatches[0]["source_file"] if all_mismatches else None,
        "metadata_source": all_mismatches[0]["source"] if all_mismatches else None,
    }

    return [result]
