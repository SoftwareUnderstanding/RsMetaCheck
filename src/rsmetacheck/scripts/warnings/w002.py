from typing import Dict, Optional, Tuple
from datetime import datetime
import re


def extract_latest_release_date(somef_data: Dict) -> Optional[str]:
    """
    Extract the date of the latest release from the releases field in SoMEF output.
    The latest release is the first element in the releases list.
    Returns the release date string or None if not found.
    """
    if "releases" not in somef_data:
        return None

    releases = somef_data["releases"]
    if not isinstance(releases, list) or not releases:
        return None

    latest_release = releases[0]
    if not isinstance(latest_release, dict):
        return None

    result = latest_release.get("result")
    if not isinstance(result, dict):
        return None

    if "date_published" in result and result["date_published"]:
        return result["date_published"]

    return None


def extract_codemeta_date_modified(somef_data: Dict) -> Optional[Dict[str, str]]:
    """
    Extract dateModified from codemeta.json in SoMEF output.
    Returns a dict with source and date, or None if not found.
    """
    if "date_updated" not in somef_data:
        return None

    date_entries = somef_data["date_updated"]
    if not isinstance(date_entries, list):
        return None

    for entry in date_entries:
        if "source" in entry:
            source = entry["source"]
            if "codemeta.json" in source:
                if "result" in entry and "value" in entry["result"]:
                    return {
                        "source": source,
                        "date": entry["result"]["value"]
                    }
        elif "technique" in entry and entry["technique"] == "code_parser":
            if "result" in entry and "value" in entry["result"]:
                return {
                    "source": "codemeta.json (code_parser)",
                    "date": entry["result"]["value"]
                }

    return None


def normalize_date_for_comparison(date_string: str) -> Optional[datetime]:
    """
    Normalize different date formats to datetime objects for comparison.
    Handles formats like:
    - "2025-02-05T18:00:24Z"
    - "2023-11-17"
    - "2022-03-11T19:01:51.720Z"
    """
    if not date_string:
        return None

    date_string = date_string.strip()

    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",  # "2025-02-05T18:00:24Z"
        "%Y-%m-%dT%H:%M:%S.%fZ",  # "2022-03-11T19:01:51.720Z"
        "%Y-%m-%d",  # "2023-11-17"
        "%Y-%m-%dT%H:%M:%S",  # Without Z
        "%Y-%m-%dT%H:%M:%S.%f",  # With microseconds, no Z
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', date_string)
    if date_match:
        try:
            return datetime.strptime(date_match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    return None


def calculate_date_difference_days(date1: datetime, date2: datetime) -> int:
    """
    Calculate the difference in days between two datetime objects.
    Returns absolute difference in days.
    """
    diff = abs((date1 - date2).days)
    return diff


def detect_outdated_datemodified(
    somef_data: Dict,
    file_name: str,
    stale_after_days: int = 1,
) -> Dict:
    """
    Detect outdated dateModified in codemeta.json warning for a single repository.
    Compares codemeta.json dateModified against the date of the latest release.
    Returns detection result with warning info.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "latest_release_date": None,
        "codemeta_date": None,
        "codemeta_source": None,
        "difference_days": 0,
        "latest_release_date_parsed": None,
        "codemeta_date_parsed": None
    }

    latest_release_date = extract_latest_release_date(somef_data)

    codemeta_data = extract_codemeta_date_modified(somef_data)

    if not latest_release_date or not codemeta_data:
        return result

    result["latest_release_date"] = latest_release_date
    result["codemeta_date"] = codemeta_data["date"]
    result["codemeta_source"] = codemeta_data["source"]

    release_date_parsed = normalize_date_for_comparison(latest_release_date)
    codemeta_date_parsed = normalize_date_for_comparison(codemeta_data["date"])

    if not release_date_parsed or not codemeta_date_parsed:
        return result

    result["latest_release_date_parsed"] = release_date_parsed.isoformat()
    result["codemeta_date_parsed"] = codemeta_date_parsed.isoformat()

    difference_days = calculate_date_difference_days(release_date_parsed, codemeta_date_parsed)
    result["difference_days"] = difference_days

    if release_date_parsed > codemeta_date_parsed and difference_days > stale_after_days:
        result["has_warning"] = True

    return result