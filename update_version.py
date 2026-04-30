import re

def get_version(file_path):
    """get version file __init__.py .

    Args:
        file_path (str): __init__py.

    Returns:
        str: version.
    """

    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"')


def update_version(toml_path, version_file):
    with open(toml_path, 'r') as f:
        content = f.read()

    new_version = get_version(version_file)
    if not new_version or new_version == "unknown":
        raise ValueError(
            f"Could not read a valid version from '{version_file}'. "
            "Ensure it contains a line like: __version__ = \"x.y.z\""
        )

    new_content = content.replace("{version-file}", new_version)

    with open(toml_path, 'w') as f:
        f.write(new_content)


update_version("pyproject.toml", "src/rsmetacheck/__init__.py")
