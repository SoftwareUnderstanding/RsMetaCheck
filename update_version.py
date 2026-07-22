import json
import re

VERSION_FILE = "src/rsmetacheck/__init__.py"
PYPROJECT_TOML = "pyproject.toml"
CODEMETA_JSON = "codemeta.json"


def get_version(file_path):
    with open(file_path) as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"')
    return None


def update_pyproject_toml(new_version):
    with open(PYPROJECT_TOML) as f:
        content = f.read()

    if "{version-file}" in content:
        new_content = content.replace("{version-file}", new_version)
    else:
        new_content = re.sub(
            r'^(version\s*=\s*)"[^"]*"',
            rf'\1"{new_version}"',
            content,
            flags=re.MULTILINE,
        )

    with open(PYPROJECT_TOML, "w") as f:
        f.write(new_content)


def update_codemeta_json(new_version):
    with open(CODEMETA_JSON) as f:
        data = json.load(f)

    data["version"] = new_version

    with open(CODEMETA_JSON, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    new_version = get_version(VERSION_FILE)
    if not new_version:
        raise ValueError(
            f"Could not read version from '{VERSION_FILE}'. "
            'Ensure it contains a line like: __version__ = "x.y.z"'
        )

    update_pyproject_toml(new_version)
    update_codemeta_json(new_version)
    print(f"Version synced to {new_version}")


if __name__ == "__main__":
    main()
