# Security Policy

## Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
USE AT YOUR OWN RISK.

Aserehe comes with no guarantees of security or regular security updates.
Users should be aware that they use this software at their own risk.

## Security Considerations

Aserehe itself has a small codebase that is thoroughly tested.
It primarily relies on widely used Python packages.

### Dependency Management

The dependencies are configured to accept minor and patch version updates
automatically.
Major version updates of dependencies (which may include security patches)
require manual updates to Aserehe.
Aserehe uses pip-audit in GitHub Workflows to regularly check for known
vulnerabilities in dependencies.

### Expected Security Profile

Due to the minimal nature of aserehe's own codebase, direct vulnerabilities are
not expected
Main security considerations would likely come from dependencies
Users should be aware that security patches in new major versions of
dependencies will not be automatically incorporated.

## Reporting Security Issues

If you discover a security vulnerability, we encourage you to:

1. Fork the repository
2. Create a fix for the security issue
3. Submit a Pull Request.

Alternatively, you can create an issue in the GitHub repository if you prefer
not to submit a fix directly.

## Best Practices for Users

1. Keep your Python environment up to date
2. Regularly check for updates in project dependencies
3. Consider using dependency scanning tools in your own environment
4. Be aware of the security implications of using any third-party software
