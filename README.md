# upgrade-ubuntu

Scripts to help with upgrading to a different major version of Ubuntu.

- `pre_upgrade.py` gets a list of package repositories that may need updating after you upgrade.
- `post_upgrade.py` updates your repository sources files.

When you will upgrade to a new major version of Ubuntu, follow these steps:

1. Run `python3 pre_upgrade.py` and save its output for later.
2. [Upgrade to the new version of Ubuntu](https://ubuntu.com/tutorials/upgrading-ubuntu-desktop#1-before-you-start).
3. Run `sudo python3 post_upgrade.py` to make sure the repository sources files are fully upgraded. Use the name of the version you upgraded from, such as "jammy" in `sudo python3 post_upgrade.py jammy`. The script requires `sudo` to make changes to the sources files in `/etc/apt`.
4. Read the previously saved output of `pre_upgrade.py` and figure out if anything needs to be done with it. Some packages may not work correctly until you uninstall and reinstall them.
