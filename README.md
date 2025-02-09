# Aserehe

Aserehe is a Python CLI tool for managing semantic versioning and conventional
commits with a focus on simplicity.
It provides a minimalistic codebase and straightforward installation, making it
an ideal choice for developers who prefer clean, efficient solutions without
unnecessary complexity.

[![image](https://img.shields.io/pypi/v/aserehe.svg)](https://pypi.python.org/pypi/aserehe)
[![image](https://img.shields.io/pypi/l/aserehe.svg)](https://pypi.python.org/pypi/aserehe)
[![image](https://img.shields.io/pypi/pyversions/aserehe.svg)](https://pypi.python.org/pypi/aserehe)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v0.json)](https://github.com/astral-sh/ruff)

## Table of Contents

- [Quickstart](#quickstart)
  - [Installation](#installation)
  - [Usage](#usage)
- [Comparison with Similar Tools](#comparison-with-similar-tools)
- [Project Goals](#project-goals)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Quickstart

### Installation

`aserehe` is distributed on [PyPI](https://pypi.org/project/aserehe/).
The recommended way to install and run `aserehe` is using `uvx`
(see [uv](https://github.com/astral-sh/uv)) or
`pipx` (see [pipx](https://github.com/pypa/pipx)).

```console
uvx aserehe --help
```

```console
pipx run aserehe --help
```

### Usage

#### Conventional Commit Check

Check if commit messages in a Git repository follow
the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```console
aserehe check
```

Optionally, you can specify a Git revision range to check:

```console
aserehe check --rev-range HEAD~5..HEAD
```

You can also check a single commit message from standard input:

```console
echo "feat: add new feature" | aserehe check --from-stdin
```

### Semantic Versioning

`aserehe` can be used to get current version and infer next
[Semantic Version](https://semver.org/) based on conventional commit messages
since the current version.
The versions are expected to be defined as Git tags.

```console
$ aserehe version
1.0.0
$ git commit -m "feat: add new feature"
$ aserehe version --next
1.1.0
```

#### Current Version

The current version is determined by finding the highest semantic version tag
that is an ancestor of the current `HEAD` in the Git repository.
If no such tag exists, the version defaults to `0.0.0`.

#### Next Version

The next version is inferred based on conventional commit messages since
the current version.
The rules for version bumping are as follows:

- **For versions 0.x.x (initial development)**:

  - Breaking changes bump the minor version.
  - Features and fixes bump the patch version.

- **For versions 1.x.x and above (stable)**:
  - Breaking changes bump the major version.
  - Features bump the minor version.
  - Fixes bump the patch version.

If there are no commits since the current version or no version-impacting
changes, the next version remains the same as the current version.

## Comparison with Similar Tools

<!-- markdownlint-disable MD013 -->

| Tool                                                                                              | Commit Validation | Version Inference | Changelog Generation | Release Automation | Hooks/Plugins | Customization                             | Complexity | Implementation     |
| ------------------------------------------------------------------------------------------------- | ----------------- | ----------------- | -------------------- | ------------------ | ------------- | ----------------------------------------- | ---------- | ------------------ |
| [**Cocogitto**](https://github.com/cocogitto/cocogitto)                                           | ✓                 | ✓                 | ✓                    | ✓                  | ✓             | High - Custom commit types, scopes, hooks | Medium     | Rust               |
| [**Convco**](https://github.com/convco/convco)                                                    | ✓                 | ✓                 | ✓                    | -                  | -             | Medium - Basic commit validation rules    | Low        | Rust               |
| [**Semantic Release**](https://github.com/semantic-release/semantic-release)                      | ✓                 | ✓                 | ✓                    | ✓                  | ✓             | High - Extensive plugin system            | High       | JavaScript/Node.js |
| [**Python Semantic Release**](https://github.com/python-semantic-release/python-semantic-release) | ✓                 | ✓                 | ✓                    | ✓                  | ✓             | High - Complex configuration              | High       | Python             |
| [**Git Cliff**](https://github.com/orhun/git-cliff)                                               | -                 | -                 | ✓                    | -                  | -             | High - Custom templates                   | Medium     | Rust               |
| [**Aserehe**](https://github.com/lukany/aserehe)                                                  | ✓                 | ✓                 | -                    | -                  | -             | None - Fixed rules                        | Very Low   | Python             |

<!-- markdownlint-enable MD013 -->

Among these tools, Convco is the closest to Aserehe in its philosophy
of simplicity, though it offers additional features like changelog generation.
For most projects, other tools are likely better default choices due to their
maturity and comprehensive feature sets.
If you need a full-featured release automation system, Semantic Release
or Python Semantic Release provide battle-tested solutions.
For changelog generation specifically, Git Cliff stands out as an excellent
dedicated tool with powerful templating capabilities.
However, these tools can introduce significant complexity - whether through
extensive configuration options, steep learning curves, or heavy dependencies.

Aserehe takes a deliberately different approach. Its main advantages are:

- **Pure Python Implementation**: Built entirely in Python, making it easy
  to understand and extend for Python developers
- **Minimal Codebase**: Focuses on reusing battle-tested Python packages rather
  than reinventing functionality
- **Minimal Configuration**: Provides sensible defaults with minimal
  configuration needed
- **Building Block Philosophy**: Instead of prescribing a complete release
  process, it provides just the essential tools (commit validation and version
  inference) that you can integrate into your own workflows.
  It is a helper for your release process, not a complete solution.

This makes Aserehe particularly suitable for Python projects where developers
want to maintain full control over their release process while keeping
the tooling simple and maintainable.

## Project Goals

Aserehe aims to have a minimalistic codebase and straightforward installation,
making it an ideal choice for developers who prefer clean, efficient solutions
without unnecessary complexity.

## Examples

### Semantic Release using GitHub Actions

The example below shows how Aserehe can be integrated into a custom release workflow.
This is just one possible pattern - you can adapt it to your needs or create
entirely different workflows.
The key is that Aserehe provides the building blocks (commit validation
and version inference) while leaving you in control of the release process.

```yaml
########################################################
# semantic-release.yaml
########################################################
name: Semantic Release

on:
  push:
    branches:
      - main

jobs:
  semantic-release:
    runs-on: ubuntu-latest
    concurrency: # avoid concurrent releases
      group: semantic-release
      cancel-in-progress: false
    permissions:
      actions: write # needed for triggering release workflow
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # needed for next version inference
      - name: Get current and next versions
        id: versions
        run: |
          current_version=$(pipx run aserehe version)
          next_version=$(pipx run aserehe version --next)
          echo "current=$current_version" >> $GITHUB_OUTPUT
          echo "next=$next_version" >> $GITHUB_OUTPUT
      - name: Trigger release workflow
        if: steps.versions.outputs.current != steps.versions.outputs.next
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh workflow run release.yaml \
            -f version=${{ steps.versions.outputs.next }}
```

<!-- markdownlint-disable MD013 -->

```yaml
########################################################
# release.yaml
########################################################
name: Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version to release (e.g., 1.2.3)"
        required: true
        type: string

env:
  GITCLIFF_VERSION: 2.7.0
  CHANGELOG_FILE: CHANGELOG.md
  FULL_CHANGELOG_FILE: FULL_CHANGELOG.md

jobs:
  release:
    runs-on: ubuntu-latest
    concurrency:
      group: release
      cancel-in-progress: false
    permissions:
      id-token: write # needed for PyPI publishing
      contents: write # needed for creating releases
    environment:
      name: production
    steps:
      - name: Validate version format
        run: |
          if ! [[ ${{ github.event.inputs.version }} =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Error: Version must be in format major.minor.patch (e.g., 1.2.3)"
            exit 1
          fi
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # needed for changelog generation
      - uses: ./.github/actions/setup-python-env
      - name: Set tag environment variable
        run: |
          echo "RELEASE_TAG=v${{ github.event.inputs.version }}" >> $GITHUB_ENV
      - name: Release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          ########################################
          # Generate changelogs
          ########################################
          git_cliff_command="npx git-cliff@${{ env.GITCLIFF_VERSION }} --tag=${{ env.RELEASE_TAG }}"
          $git_cliff_command --unreleased > ${{ env.CHANGELOG_FILE }}
          $git_cliff_command > ${{ env.FULL_CHANGELOG_FILE }}
          ########################################
          # Create GitHub Release
          ########################################
          gh release create \
            ${{ env.RELEASE_TAG }} \
            --title ${{ env.RELEASE_TAG }} \
            --notes-file ${{ env.CHANGELOG_FILE }} \
            ${{ env.FULL_CHANGELOG_FILE }}
          ########################################
          # Build package
          ########################################
          sed -i "s/^version = .*/version = \"${{ github.event.inputs.version }}\"/" pyproject.toml
          uv build
      - name: Publish
        uses: pypa/gh-action-pypi-publish@release/v1
```

<!-- markdownlint-enable MD013 -->

## Contributing

We welcome contributions! Please see our
[contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the terms of the MIT license.
See the [LICENSE](LICENSE) file for details.

## Contact

For support or inquiries, please contact [Jan Lukány](mailto:lukany.jan@gmail.com).
