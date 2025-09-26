import subprocess


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
