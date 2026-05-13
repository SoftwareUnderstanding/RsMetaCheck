from typing import Dict
from urllib.parse import urlparse


def is_valid_issue_tracker_format(url: str) -> bool:
    """
    Check if URL matches a recognized issue tracker format.
    Validates that the URL has a proper scheme, hostname, and
    a path ending in a recognized issue tracker pattern (/issues, /tickets).
    """
    if not url:
        return False

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    if parsed.scheme not in ('http', 'https'):
        return False

    if not parsed.netloc:
        return False

    path = parsed.path
    if not path or path == '/':
        return False

    path_lower = path.lower()
    valid_patterns = ['/issues', '/tickets']
    for pattern in valid_patterns:
        if path_lower.endswith(pattern) or (pattern + '/') in path_lower:
            return True

    return False


def detect_issue_tracker_format_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json IssueTracker URL does not follow
    a recognized issue tracker format.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "issue_url": None,
        "source": None,
        "format_violation": None
    }

    if "issue_tracker" not in somef_data:
        return result

    issues_entries = somef_data["issue_tracker"]
    if not isinstance(issues_entries, list):
        return result

    for entry in issues_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                issue_url = entry["result"]["value"]

                if not is_valid_issue_tracker_format(issue_url):
                    result["has_pitfall"] = True
                    result["issue_url"] = issue_url
                    result["source"] = source
                    result["format_violation"] = "URL does not match recognized issue tracker format"
                    break

    return result