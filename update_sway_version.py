#!/usr/bin/env python3
"""
Script to check for new versions of all git dependencies and update the manifest file.
Returns exit code 0 if updates were made, 1 if already up to date, 2 on error.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, Union

from ruamel.yaml import YAML


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
        print(f"Warning: Error fetching GitHub tag for {repo_name}: {e}", file=sys.stderr)
        return ""

    return ""


def get_latest_gitlab_tag(host: str, repo_path: str) -> str:
    """Get the latest stable tag from GitLab repository"""
    try:
        encoded_path = urllib.parse.quote(repo_path, safe="")
        api_url = f"https://{host}/api/v4/projects/{encoded_path}/repository/tags"
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
        print(f"Warning: Error fetching GitLab tag for {host}/{repo_path}: {e}", file=sys.stderr)
        return ""

    return ""


def get_latest_sourcehut_tag(repo_path: str) -> str:
    """Get the latest tag from SourceHut repository"""
    try:
        api_url = f"https://git.sr.ht/~{repo_path}/refs"
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", "Python-urllib/3.x")

        with urllib.request.urlopen(req) as response:
            content = response.read().decode()
            tag_pattern = r"refs/tags/([^\s]+)"
            tags = re.findall(tag_pattern, content)
            if tags:
                return tags[0]
    except Exception as e:
        print(f"Warning: Error fetching SourceHut tag for {repo_path}: {e}", file=sys.stderr)
        return ""

    return ""


def get_repo_name(url: str) -> str:
    """Extract repository name from URL"""
    if url.endswith(".git"):
        url = url[:-4]

    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return parts[-1]


def get_latest_version(url: str) -> str:
    """Get latest version for a git repository"""
    if "github.com" in url:
        repo_name = get_repo_name(url)
        return get_latest_github_tag(repo_name)
    elif "gitlab.freedesktop.org" in url:
        path_parts = url.split("gitlab.freedesktop.org/")[-1]
        if path_parts.endswith(".git"):
            path_parts = path_parts[:-4]
        return get_latest_gitlab_tag("gitlab.freedesktop.org", path_parts)
    elif "git.sr.ht" in url:
        sourcehut_path = url.split("git.sr.ht/~")[-1]
        if sourcehut_path.endswith(".git"):
            sourcehut_path = sourcehut_path[:-4]
        return get_latest_sourcehut_tag(sourcehut_path)
    else:
        return ""


def normalize_version(version: Union[str, int, float]) -> str:
    """Normalize version string for comparison"""
    version = str(version).strip()
    if version.startswith("v"):
        version = version[1:]
    if version.startswith("release-"):
        version = version[8:]
    return version


def is_valid_version_upgrade(current_tag: str, new_tag: str) -> bool:
    """
    Check if upgrading from current_tag to new_tag makes sense.
    Filter out suspicious tags like platform-specific suffixes.
    """
    # Skip if new tag has platform suffix that current doesn't have
    platform_suffixes = ["-gitlab", "-github", "-git"]
    current_normalized = normalize_version(current_tag)
    new_normalized = normalize_version(new_tag)

    for suffix in platform_suffixes:
        if new_normalized.endswith(suffix) and not current_normalized.endswith(suffix):
            return False

    return True


def update_git_sources_recursive(data: Any, updates: Dict[str, str]) -> bool:
    """
    Recursively find and update git sources in the data structure.
    Returns True if any updates were made.
    """
    updated = False

    if isinstance(data, dict):
        if data.get("type") == "git" and "url" in data and "tag" in data:
            url = data["url"]
            current_tag = str(data["tag"])

            if url in updates:
                new_tag = updates[url]
                if current_tag != new_tag:
                    data["tag"] = new_tag
                    updated = True

        for value in data.values():
            if update_git_sources_recursive(value, updates):
                updated = True

    elif isinstance(data, list):
        for item in data:
            if update_git_sources_recursive(item, updates):
                updated = True

    return updated


def extract_git_dependencies(data: Union[Dict, List, Any]) -> List[Tuple[str, str]]:
    """Extract all git dependencies from the YAML data"""
    dependencies = []

    if isinstance(data, dict):
        if data.get("type") == "git" and "url" in data:
            url = data["url"]
            tag = str(data.get("tag", "main"))
            dependencies.append((url, tag))

        for value in data.values():
            dependencies.extend(extract_git_dependencies(value))

    elif isinstance(data, list):
        for item in data:
            dependencies.extend(extract_git_dependencies(item))

    return dependencies


def update_all_versions(yaml_file: str) -> bool:
    """
    Check for new versions of all dependencies and update the YAML file if needed.
    Returns True if any updates were made, False if already up to date.
    """
    # Read the YAML file with ruamel.yaml to preserve formatting
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    try:
        with open(yaml_file, "r") as f:
            data = yaml.load(f)
    except Exception as e:
        print(f"Error reading YAML file: {e}", file=sys.stderr)
        sys.exit(2)

    # Extract all git dependencies
    dependencies = extract_git_dependencies(data)

    if not dependencies:
        print("No git dependencies found in YAML", file=sys.stderr)
        sys.exit(2)

    print(f"Found {len(dependencies)} git dependencies to check")
    print()

    # Check each dependency for updates
    updates = {}
    any_updates = False

    for url, current_tag in dependencies:
        latest_version = get_latest_version(url)

        if not latest_version:
            print(f"⚠️  {url}: Could not fetch latest version (current: {current_tag})")
            continue

        current_normalized = normalize_version(current_tag)
        latest_normalized = normalize_version(latest_version)

        if current_normalized != latest_normalized:
            # Check if this is a valid upgrade
            if not is_valid_version_upgrade(current_tag, latest_version):
                print(f"⏭️  {url}: Skipping {current_tag} → {latest_version} (suspicious tag)")
                continue

            print(f"🔄 {url}: {current_tag} → {latest_version}")
            updates[url] = latest_version
            any_updates = True
        else:
            print(f"✓  {url}: {current_tag} (up to date)")

    if not any_updates:
        print("\n✅ All dependencies are up to date!")
        return False

    print(f"\n📦 Updating {len(updates)} dependencies...")

    # Update all git sources
    update_git_sources_recursive(data, updates)

    # Write back the YAML file
    try:
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)
        print(f"✅ Successfully updated manifest file")
        return True
    except Exception as e:
        print(f"Error writing YAML file: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_sway_version.py <yaml_file>")
        sys.exit(2)

    yaml_file = sys.argv[1]
    updated = update_all_versions(yaml_file)

    # Exit code 0 if updated, 1 if no update needed
    sys.exit(0 if updated else 1)


if __name__ == "__main__":
    main()
