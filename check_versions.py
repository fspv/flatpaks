#!/usr/bin/env python3

import sys
import yaml
import urllib.request
import urllib.parse
import json
import re
from typing import List, Dict, Tuple

def extract_git_dependencies(data, dependencies=None):
    if dependencies is None:
        dependencies = []
    
    if isinstance(data, dict):
        if 'type' in data and data['type'] == 'git' and 'url' in data:
            url = data['url']
            tag = str(data.get('tag', 'main'))  # Convert to string
            dependencies.append((url, tag))
        
        for value in data.values():
            extract_git_dependencies(value, dependencies)
    elif isinstance(data, list):
        for item in data:
            extract_git_dependencies(item, dependencies)
    
    return dependencies

def get_repo_name(url: str) -> str:
    if url.endswith('.git'):
        url = url[:-4]
    
    parts = url.split('/')
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return parts[-1]

def parse_version(version: str) -> tuple:
    """Parse version string into sortable tuple"""
    # Remove common prefixes
    version = version.strip()
    if version.startswith('v'):
        version = version[1:]
    
    # Split into parts
    parts = []
    for part in re.split(r'[-._]', version):
        if part.isdigit():
            parts.append((0, int(part)))
        elif part == 'rc':
            parts.append((2, 0))  # rc is less than release
        elif part == 'beta':
            parts.append((3, 0))  # beta is less than rc
        elif part == 'alpha':
            parts.append((4, 0))  # alpha is less than beta
        else:
            parts.append((1, part))
    
    return tuple(parts)

def get_latest_github_tag(repo_name: str) -> str:
    try:
        api_url = f"https://api.github.com/repos/{repo_name}/tags"
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'Python-urllib/3.x')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                # Sort tags by semantic version
                tags = [tag['name'] for tag in data]
                # Filter out obvious pre-releases if there are stable versions
                stable_tags = [t for t in tags if not any(x in t.lower() for x in ['rc', 'beta', 'alpha', 'dev', 'pre'])]
                if stable_tags:
                    tags = stable_tags
                
                # Sort by parsed version
                tags.sort(key=parse_version, reverse=True)
                return tags[0]
    except Exception as e:
        return f"Error: {str(e)}"
    
    return "No tags found"

def get_latest_gitlab_tag(host: str, repo_path: str) -> str:
    try:
        encoded_path = urllib.parse.quote(repo_path, safe='')
        api_url = f"https://{host}/api/v4/projects/{encoded_path}/repository/tags"
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'Python-urllib/3.x')
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                # Sort tags by semantic version
                tags = [tag['name'] for tag in data]
                # Filter out obvious pre-releases if there are stable versions
                stable_tags = [t for t in tags if not any(x in t.lower() for x in ['rc', 'beta', 'alpha', 'dev', 'pre'])]
                if stable_tags:
                    tags = stable_tags
                
                # Sort by parsed version
                tags.sort(key=parse_version, reverse=True)
                return tags[0]
    except Exception as e:
        return f"Error: {str(e)}"
    
    return "No tags found"

def get_latest_sourcehut_tag(repo_path: str) -> str:
    try:
        api_url = f"https://git.sr.ht/~{repo_path}/refs"
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'Python-urllib/3.x')
        
        with urllib.request.urlopen(req) as response:
            content = response.read().decode()
            tag_pattern = r'refs/tags/([^\s]+)'
            tags = re.findall(tag_pattern, content)
            if tags:
                return tags[0]
    except Exception as e:
        return f"Error: {str(e)}"
    
    return "No tags found"

def get_latest_version(url: str) -> str:
    if 'github.com' in url:
        repo_name = get_repo_name(url)
        return get_latest_github_tag(repo_name)
    elif 'gitlab.freedesktop.org' in url:
        path_parts = url.split('gitlab.freedesktop.org/')[-1]
        if path_parts.endswith('.git'):
            path_parts = path_parts[:-4]
        return get_latest_gitlab_tag('gitlab.freedesktop.org', path_parts)
    elif 'git.sr.ht' in url:
        path_parts = url.split('git.sr.ht/~')[-1]
        if path_parts.endswith('.git'):
            path_parts = path_parts[:-4]
        return get_latest_sourcehut_tag(path_parts)
    elif 'bitmath.org' in url:
        return "Not supported (bitmath.org)"
    else:
        return "Unknown host"

def normalize_version(version) -> str:
    """Normalize version string for comparison"""
    # Convert to string first (in case it's a float/int from YAML)
    version = str(version).strip()
    # Remove common prefixes
    if version.startswith('v'):
        version = version[1:]
    if version.startswith('release-'):
        version = version[8:]
    return version

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_versions.py <yaml_file>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: File {yaml_file} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
    
    dependencies = extract_git_dependencies(data)
    
    has_outdated = False
    seen_repos = set()
    results = []
    errors = []
    
    for url, current_tag in dependencies:
        if url in seen_repos:
            continue
        seen_repos.add(url)
        
        latest_version = get_latest_version(url)
        
        # Log errors and unsupported repos
        if (latest_version.startswith("Error") or 
            latest_version == "No tags found" or 
            latest_version == "Unknown host" or 
            latest_version == "Not supported (bitmath.org)"):
            errors.append((url, current_tag, latest_version))
            continue
        
        # Normalize versions for comparison
        normalized_current = normalize_version(current_tag)
        normalized_latest = normalize_version(latest_version)
        
        # Only add to results if normalized versions don't match
        if normalized_current != normalized_latest:
            results.append((url, current_tag, latest_version))
            has_outdated = True
    
    if has_outdated:
        print(f"{'Repository URL':<80} {'Current Version':<20} {'Latest Version':<20}")
        print("-" * 120)
        
        for url, current_tag, latest_version in results:
            print(f"{url:<80} {current_tag:<20} {latest_version:<20}")
    
    if errors:
        print("\n\nUnsupported or error repositories:")
        print("-" * 120)
        for url, current_tag, error_msg in errors:
            print(f"{url:<80} {current_tag:<20} {error_msg:<20}")

if __name__ == "__main__":
    main()