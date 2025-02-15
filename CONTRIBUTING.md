# Contributing to Aserehe

Thank you for your interest in contributing to Aserehe! This document provides guidelines for contributing to the project.

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. This leads to more readable messages that are easy to follow when looking through the project history and helps us generate changelogs automatically.

Only commits in `main` branch must follow the Conventional Commits format.
All the pull requests to `main` must have a title that matches the Conventional Commits format.
PRs are merged using the squash and merge strategy.
PR title is used as the squashed commit message.
PR description is used as the squashed commit description.
GitHub Actions will check if the PR title matches the Conventional Commits format.

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Make your changes and commit them (no need to follow the Conventional Commits format).
3. Update the README.md with details of changes if applicable.
4. Add or update tests as needed.
5. Make sure your code lints and tests pass.
6. Submit a pull request to the `main` branch.

## Development Setup

1. Clone the repository
2. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
3. Install dependencies via `uv sync`.
4. Run tests via `uv run pytest`.
5. Optionally run other code checks as defined in GitHub Workflow [check-code](.github/workflows/check-code.yml).

## Code of Conduct

This project follows a Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Questions or Need Help?

Feel free to open an issue or contact the maintainers if you have any questions or need help.
