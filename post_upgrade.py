import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from utils import get_current_version_name


now = datetime.now()
today: str = f"{now.year}-{str(now.month).zfill(2)}-{str(now.day).zfill(2)}"


def main():
    parser = argparse.ArgumentParser(
        prog="post-upgrade",
        description="Updates your repository sources files",
    )
    parser.add_argument("prev_version_name", type=str)

    args = parser.parse_args()
    prev_version_name: str = args.prev_version_name
    if " " in prev_version_name:
        print('Error: enter only the first part of the new version\'s name, such as "jammy"')
        sys.exit(1)

    version_name: str = get_current_version_name()
    if version_name == prev_version_name:
        print("Error: enter the name of the version you upgraded from, not the current version")
        sys.exit(1)

    print("Updating sources files")
    srcs_list: Path = Path("/etc/apt/sources.list")
    srcs_list_d: Path = Path("/etc/apt/sources.list.d/")

    update_sources_file(srcs_list, version_name, prev_version_name)
    for path in srcs_list_d.iterdir():
        if path.is_file():
            update_sources_file(path, version_name, prev_version_name)


def update_sources_file(file: Path, version_name: str, prev_version_name: str) -> None:
    """Changes a sources file from an old version of Ubuntu to the current version"""
    contents: str = file.read_text(encoding="utf8")

    # replace the old version name with the current version name
    new_contents: str = re.sub(
        pattern=rf"^(deb.+){prev_version_name}(.+)",
        repl=rf"#\1{prev_version_name}\2\n\1{version_name}\2",
        string=contents,
        flags=re.MULTILINE,
    )
    if contents == new_contents:
        print(f"Skipping file that has no {prev_version_name} repository definitions: {file}")
        return

    # make a backup of the file
    backups_folder: Path = Path(file.parent / "backups")
    try:
        backups_folder.mkdir(mode=0o755, exist_ok=True)
    except PermissionError:
        print(
            "Error: permission denied. Run this script with sudo. You may need to use the full"
            " path of the executable, such as"
        )
        print("\tsudo /home/chris/.local/bin/uv post_upgrade.py jammy")
        print(
            "You can find the full path of whichever executable you're using to run Python by"
            " using `which`, such as `which uv`."
        )
        sys.exit(1)
    backup: Path = backups_folder / f"{today}_{file.name}.bak"
    backup.touch(mode=0o644, exist_ok=True)
    backup.write_text(contents, encoding="utf8")
    print(f"Backup of {file.name} created at {backup}")

    # create a temporary file with the new contents
    temp: Path = Path(f"{file}.tmp")
    temp.touch(mode=0o644, exist_ok=True)
    temp.write_text(new_contents, encoding="utf8")

    # rename the temporary file to replace the original file
    temp.replace(file)
    print(f"Updated {file}")


if __name__ == "__main__":
    main()
