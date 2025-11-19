# Testing GitHub Actions with act

This document describes how to test the auto-update-sway.yml workflow using `act`.

## Prerequisites

1. Install Docker (required for act to work)
2. Install act: https://github.com/nektos/act

## Testing the Workflow

### List all jobs in the workflow

```bash
act -l -W .github/workflows/auto-update-sway.yml
```

### Test the check-and-update job only

This tests the version checking and update logic without building the flatpak:

```bash
act workflow_dispatch -j check-and-update -W .github/workflows/auto-update-sway.yml
```

### Test the full workflow (requires significant resources)

⚠️ Warning: This will attempt to build the flatpak, which requires significant disk space and time.

```bash
act workflow_dispatch -W .github/workflows/auto-update-sway.yml
```

### Dry run (shows what would execute without running)

```bash
act workflow_dispatch -W .github/workflows/auto-update-sway.yml --dryrun
```

## Manual Testing Without Docker

If Docker is not available, you can test the components manually:

### Test the update script

```bash
# Install dependencies
pip install ruamel.yaml

# Test the update script (will check for updates to ALL dependencies)
python3 update_sway_version.py org.swaywm.sway/org.swaywm.sway.yaml

# The script will:
# - Check all 31 git dependencies
# - Report which ones need updates
# - Filter out suspicious version tags
# - Update the YAML file if needed

# Exit codes:
# 0 = updates were made
# 1 = already up to date
# 2 = error occurred
```

### Validate workflow YAML syntax

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto-update-sway.yml'))"
```

### Test with an older version

```bash
# Backup the current file
cp org.swaywm.sway/org.swaywm.sway.yaml org.swaywm.sway/org.swaywm.sway.yaml.backup

# Temporarily set to an older version
sed -i "s/tag: '1.11'/tag: '1.10'/" org.swaywm.sway/org.swaywm.sway.yaml

# Run update (should detect and update to 1.11)
python3 update_sway_version.py org.swaywm.sway/org.swaywm.sway.yaml

# Restore backup
mv org.swaywm.sway/org.swaywm.sway.yaml.backup org.swaywm.sway/org.swaywm.sway.yaml
```

## Workflow Validation Results

### ✅ Validated Components

1. **Workflow YAML Syntax**: Valid GitHub Actions YAML
2. **Update Script Logic**: Successfully detects new versions and updates the manifest
3. **Exit Codes**: Properly returns 0 for updates, 1 for no-update, 2 for errors
4. **Version Detection**: Correctly fetches latest stable version from GitHub API
5. **Version Comparison**: Properly normalizes and compares versions

### ⚠️ Components Requiring Docker

The following components require a full GitHub Actions environment or Docker to test:

1. **Flatpak Build**: Building the actual flatpak requires the flatpak-builder container
2. **Artifact Upload/Download**: Requires GitHub Actions environment
3. **Git Commit & Push**: Can be tested locally but requires proper git setup
4. **Release Creation**: Requires GitHub API access

## Workflow Overview

The workflow consists of 3 jobs:

1. **check-and-update**: Checks for new sway version and updates the YAML if needed
2. **build-flatpak**: Builds the flatpak if an update was detected (runs in container)
3. **commit-and-release**: Commits changes and creates a GitHub release if build succeeded

## Schedule

The workflow runs automatically on the 1st of every month at 00:00 UTC.
It can also be triggered manually via workflow_dispatch.

## How It Works

1. The workflow checks the latest versions of all git dependencies (sway, wlroots, wayland, etc.)
2. Compares each dependency with the current version in org.swaywm.sway.yaml
3. If any updates are detected:
   - Updates all outdated dependencies in the YAML file
   - Filters out suspicious version tags (e.g., platform-specific suffixes)
   - Builds the flatpak
   - If build succeeds:
     - Commits the updated YAML to the repository
     - Creates a GitHub release with the built flatpak attached

## Troubleshooting

### act fails with Docker errors

Make sure Docker is running:
```bash
docker ps
```

### Update script fails to fetch latest version

Check your internet connection and GitHub API rate limits:
```bash
curl -s https://api.github.com/repos/swaywm/sway/tags | head
```

### Build fails

Check the flatpak build logs in the GitHub Actions UI.
The build requires significant resources and may timeout on slower systems.
