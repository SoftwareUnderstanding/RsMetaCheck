import json
import re
import sys

VERSION_FILE = "src/rsmetacheck/__init__.py"
PYPROJECT_TOML = "pyproject.toml"
CODEMETA_JSON = "codemeta.json"


def get_init_version():
    with open(VERSION_FILE) as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"')


def get_toml_version():
    with open(PYPROJECT_TOML) as f:
        for line in f:
            m = re.match(r'^version\s*=\s*"([^"]*)"', line)
            if m:
                return m.group(1)


def get_codemeta_version():
    with open(CODEMETA_JSON) as f:
        data = json.load(f)
    return data.get("version")


def main():
    versions = {
        VERSION_FILE: get_init_version(),
        PYPROJECT_TOML: get_toml_version(),
        CODEMETA_JSON: get_codemeta_version(),
    }

    canonical = versions[VERSION_FILE]
    errors = []

    for file_path, ver in versions.items():
        if ver != canonical:
            errors.append(f"{file_path}: {ver!r} (expected {canonical!r})")

    if errors:
        print("Version mismatch detected:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)

    print(f"All version files agree on {canonical}")


if __name__ == "__main__":
    main()
