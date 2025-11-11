from typing import Dict


def detect_citation_missing_reference_publication_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when CITATION.cff doesn't have referencePublication even though it's referenced in codemeta.json.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "codemeta_has_reference": False,
        "citation_cff_has_reference": False,
        "citation_cff_exists": False
    }

    if "citation" not in somef_data:
        return result

    citation_entries = somef_data["citation"]
    if not isinstance(citation_entries, list):
        return result

    codemeta_citation_value = None
    citation_cff_citation_value = None
    citation_cff_exists_in_somef = False

    for entry in citation_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if technique == "code_parser" and "codemeta.json" in source:
            if "result" in entry and "value" in entry["result"]:
                codemeta_citation_value = entry["result"]["value"]
                result["codemeta_has_reference"] = True
        elif "CITATION.cff" in source:
            citation_cff_exists_in_somef = True
            result["citation_cff_exists"] = True
            if "result" in entry and "value" in entry["result"]:
                citation_cff_citation_value = entry["result"]["value"]

    if not citation_cff_exists_in_somef:
        citation_cff_sources = ["authors", "title", "description", "version", "license"]
        for category in citation_cff_sources:
            if category in somef_data:
                entries = somef_data[category]
                if isinstance(entries, list):
                    for entry in entries:
                        source = entry.get("source", "")
                        if "CITATION.cff" in source:
                            citation_cff_exists_in_somef = True
                            result["citation_cff_exists"] = True
                            break

    if (codemeta_citation_value and
            citation_cff_exists_in_somef and
            (not citation_cff_citation_value or citation_cff_citation_value != codemeta_citation_value)):

        if citation_cff_citation_value:
            if ("doi.org" in codemeta_citation_value or "http" in codemeta_citation_value):
                if not ("doi.org" in citation_cff_citation_value or "http" in citation_cff_citation_value):
                    result["has_pitfall"] = True
                elif codemeta_citation_value not in citation_cff_citation_value and citation_cff_citation_value not in codemeta_citation_value:
                    result["has_pitfall"] = True
        else:
            result["has_pitfall"] = True

    return result