#!/usr/bin/env python3
"""
Script to check for new sway version and update the manifest file.
Returns exit code 0 if update was made, 1 if already up to date, 2 on error.
"""

import json
import re
import sys
import urllib.request
from typing import Tuple

import yaml


def parse_version(version: str) -> Tuple:
    """Parse version string into sortable tuple"""
    version = version.strip()
    if version.startswith("v"):
        version = version[1:]

    parts = []
    for part in re.split(r"[-._]", version):
        if part.isdigit():
            parts.append((0, int(part)))
        elif part == "rc":
            parts.append((2, 0))
        elif part == "beta":
            parts.append((3, 0))
        elif part == "alpha":
            parts.append((4, 0))
        else:
            parts.append((1, part))

    return tuple(parts)


def get_latest_github_tag(repo_name: str) -> str:
    """Get the latest stable tag from GitHub repository"""
    try:
        api_url = f"https://api.github.com/repos/{repo_name}/tags"
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", "Python-urllib/3.x")

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                tags = [tag["name"] for tag in data]
                # Filter out pre-releases
                stable_tags = [
                    t
                    for t in tags
                    if not any(
                        x in t.lower() for x in ["rc", "beta", "alpha", "dev", "pre"]
                    )
                ]
                if stable_tags:
                    tags = stable_tags

                tags.sort(key=parse_version, reverse=True)
                return tags[0]
    except Exception as e:
        print(f"Error fetching latest tag: {e}", file=sys.stderr)
        return ""

    return ""


def normalize_version(version: str) -> str:
    """Normalize version string for comparison"""
    version = str(version).strip()
    if version.startswith("v"):
        version = version[1:]
    if version.startswith("release-"):
        version = version[8:]
    return version


def update_sway_version(yaml_file: str) -> bool:
    """
    Check for new sway version and update the YAML file if needed.
    Returns True if update was made, False if already up to date.
    """
    # Read the YAML file
    try:
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading YAML file: {e}", file=sys.stderr)
        sys.exit(2)

    # Find the sway module
    sway_module = None
    for module in data.get("modules", []):
        if module.get("name") == "sway":
            sway_module = module
            break

    if not sway_module:
        print("Error: Could not find sway module in YAML", file=sys.stderr)
        sys.exit(2)

    # Get current sway version
    current_tag = None
    for source in sway_module.get("sources", []):
        if source.get("type") == "git" and "swaywm/sway" in source.get("url", ""):
            current_tag = str(source.get("tag", ""))
            break

    if not current_tag:
        print("Error: Could not find sway git source", file=sys.stderr)
        sys.exit(2)

    # Get latest version from GitHub
    latest_tag = get_latest_github_tag("swaywm/sway")
    if not latest_tag:
        print("Error: Could not fetch latest sway version", file=sys.stderr)
        sys.exit(2)

    # Normalize versions for comparison
    current_normalized = normalize_version(current_tag)
    latest_normalized = normalize_version(latest_tag)

    print(f"Current sway version: {current_tag}")
    print(f"Latest sway version: {latest_tag}")

    if current_normalized == latest_normalized:
        print("Already up to date!")
        return False

    # Update the version
    for source in sway_module.get("sources", []):
        if source.get("type") == "git" and "swaywm/sway" in source.get("url", ""):
            source["tag"] = latest_tag
            break

    # Write back the YAML file
    try:
        with open(yaml_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, width=120)
        print(f"Updated sway version to {latest_tag}")
        return True
    except Exception as e:
        print(f"Error writing YAML file: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_sway_version.py <yaml_file>")
        sys.exit(2)

    yaml_file = sys.argv[1]
    updated = update_sway_version(yaml_file)

    # Exit code 0 if updated, 1 if no update needed
    sys.exit(0 if updated else 1)


if __name__ == "__main__":
    main()
