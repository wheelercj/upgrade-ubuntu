import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


now = datetime.now()
today: str = f"{now.year}-{str(now.month).zfill(2)}-{str(now.day).zfill(2)}"


def main():
    parser = argparse.ArgumentParser(
        prog="upgrade-ubuntu",
        description="Scripts to help with upgrading to a different major version of Ubuntu",
    )
    parser.add_argument("new_version_name", type=str)

    args = parser.parse_args()
    new_version_name: str = args.new_version_name
    if " " in new_version_name:
        print('Error: enter only the first part of the new version\'s name, such as "noble"')
        sys.exit(1)

    version_name: str = get_current_version_name()
    if version_name == new_version_name:
        print("Error: enter the name of the version to change to, not the current version")
        sys.exit(1)

    print(f"Upgrading from {version_name} to {new_version_name}")

    print("Getting a list of the manually installed packages")
    showmanual_res: subprocess.CompletedProcess = subprocess.run(
        ["apt-mark showmanual"],
        check=True,
        shell=True,
        capture_output=True,
        text=True,
    )
    assert isinstance(showmanual_res.stdout, str), f"{type(showmanual_res.stdout).__name__ = }"
    manually_installed: list[str] = showmanual_res.stdout.strip().splitlines()
    print(f"Found {len(manually_installed)} manually installed packages")

    print("Getting source repositories")
    srcs_list: Path = Path("/etc/apt/sources.list")
    srcs_list_d: Path = Path("/etc/apt/sources.list.d/")

    print("Updating sources files")
    update_sources_file(srcs_list, version_name, new_version_name)
    for path in srcs_list_d.iterdir():
        if path.is_file():
            update_sources_file(path, version_name, new_version_name)

    print("Indexing /var/lib/apt/lists")
    apt_lists_pkg_urls: dict[str, str] = index_apt_lists()
    print(f"Found {len(apt_lists_pkg_urls)} package repository URLs in /var/lib/apt/lists")

    print("Mapping manually installed packages to source repositories")
    chosen_pkg_urls: dict[str, str] = dict()
    for pkg in manually_installed:
        url: str | None = get_pkg_url(pkg, apt_lists_pkg_urls)
        if url:
            chosen_pkg_urls[pkg] = url
    print(f"Found {len(chosen_pkg_urls)} manually installed package repository URLs")

    print()
    for pkg, url in chosen_pkg_urls.items():
        print(f"{pkg}:\n\t{url}")


def get_current_version_name() -> str:
    """Gets the name of the current version of Ubuntu"""
    release_res: subprocess.CompletedProcess = subprocess.run(
        ["lsb_release -a"],
        check=True,
        shell=True,
        capture_output=True,
        text=True,
    )
    assert isinstance(release_res.stdout, str), f"{type(release_res.stdout).__name__ = }"

    version_name: str = ""
    for line in release_res.stdout.splitlines():
        if line.startswith("Codename:"):
            version_name = line.split()[1]
            break
    assert version_name

    return version_name


def update_sources_file(file: Path, version_name: str, new_version_name: str) -> None:
    """Changes a sources file to use a new version of Ubuntu"""
    contents: str = file.read_text(encoding="utf8")

    # replace the current version name with the new version name
    new_contents: str = re.sub(
        pattern=rf"^(deb.+){version_name}(.+)",
        repl=rf"#\1{version_name}\2\n\1{new_version_name}\2",
        string=contents,
        flags=re.MULTILINE,
    )
    if contents == new_contents:
        print(f"Skipping file that has no {version_name} repository definitions: {file}")
        return

    # make a backup of the file
    backups_folder: Path = Path(file.parent / "backups")
    backups_folder.mkdir(exist_ok=True)
    backup: Path = backups_folder / f"{today}_{file.name}.bak"
    backup.write_text(contents, encoding="utf8")
    print(f"Backup of {file.name} created at {backup}")

    # create a temporary file with the new contents
    temp: Path = Path(f"{file}.tmp")
    temp.write_text(new_contents, encoding="utf8")

    # rename the temporary file to replace the original file
    temp.replace(file)


def index_apt_lists() -> dict[str, str]:
    """Maps package names to package repository URLs using the data in /var/lib/apt/lists"""
    # creating this dictionary is important because some of the files in /var/lib/apt/lists are
    # massive and take a long time to process
    m: dict[str, str] = dict()

    for path in Path("/var/lib/apt/lists").iterdir():
        if not path.is_file():
            continue

        try:
            lines: list[str] = path.read_text(encoding="utf8").splitlines()
        except PermissionError:
            continue

        i: int = 0
        while i < len(lines):
            while i < len(lines) and not lines[i].startswith("Package: "):
                i += 1
            if i >= len(lines):
                break
            pkg_name: str = lines[i].split()[1]

            no_url: bool = False
            while i < len(lines) and not lines[i].startswith("Vcs-Browser: "):
                if lines[i] == "":
                    no_url = True
                    break
                i += 1
            if no_url or i >= len(lines):
                continue
            pkg_url: str = lines[i].split()[1]

            m[pkg_name] = pkg_url

    return m


def get_pkg_url(pkg_name: str, apt_lists_pkg_urls: dict[str, str]) -> str | None:
    """Attempts to get the repository URL of a package"""
    if pkg_name in apt_lists_pkg_urls:
        return apt_lists_pkg_urls[pkg_name]

    policy_res: subprocess.CompletedProcess = subprocess.run(
        [f"apt policy {pkg_name}"],
        check=True,
        shell=True,
        capture_output=True,
        text=True,
    )
    assert isinstance(policy_res.stdout, str)
    policy: list[str] = policy_res.stdout.strip().splitlines()

    repo_pattern: re.Pattern = re.compile(r"^\s*\d+ (?P<url>https?://\S+).*")
    for line in policy:
        match: re.Match | None = repo_pattern.match(line)
        if match:
            return match["url"]


if __name__ == "__main__":
    main()
