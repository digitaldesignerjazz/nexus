# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

The `main` branch and the current 0.1 series receive security attention. Older experimental branches and tags are not actively maintained for security fixes.

## Reporting a Vulnerability

We take the security of the Nexus ecosystem seriously — mesh, blockchain bridges, agent orchestration, and the surrounding infrastructure.

**Please do not open public GitHub issues for security vulnerabilities.**

Instead, report privately:

- Prefer: GitHub Security Advisories ("Report a vulnerability" button on the repository Security tab)
- Or contact the maintainer directly via the email associated with the repository owner account

### What to include

- Description of the vulnerability and its potential impact
- Steps to reproduce (or proof-of-concept if available)
- Affected components (Python reference layer, Rust orchestration core, mesh configs, CI, etc.)
- Suggested remediation if you have one

### Response expectations

- Acknowledgement within **72 hours** (usually faster)
- Initial assessment and severity classification within **7 days**
- We will keep you informed of progress
- Coordinated disclosure is preferred; we will work with you on timing

## Security Updates

- Dependabot is configured for both version updates and security alerts
- Security-related dependency updates receive priority attention
- Critical vulnerabilities in the supported versions will be addressed as quickly as possible

## Scope Notes

This policy primarily covers the code and configuration in this repository. Related repositories in the broader digitaldesignerjazz / Esslinger ecosystem may have their own policies or inherit this one.

Thank you for helping keep the lattice resilient.
