# Contributing to Agent Action Manifest

Thank you for your interest in contributing.

## How to contribute

1. Fork the repository and create your branch from `main`.
2. Install the development environment:

   ```bash
   pip install -e ".[dev]"
   ```

3. Make your changes.
4. Run the test suite before submitting:

   ```bash
   pytest
   aam check-examples
   ```

5. Open a pull request with a clear description of the change and why it is needed.

## Guidelines

- Keep changes focused and minimal.
- Match the existing code style.
- Add or update tests for any changed behavior.
- Update documentation if you change public APIs or add new features.
- Do not introduce new dependencies without discussion.

## Public-safe language

This is a public repository. Do not introduce private or internal terminology in source code, comments, tests, docs, examples, schemas, or package metadata.

Permitted terminology includes: agent action manifest, action declaration, tool action, authority requirement, review requirement, reliance requirement, payload policy, redaction hint, action inventory, action type, policy posture, runtime control, agent governance, action proposal, control plane, manifest validation.

## Reporting issues

Please open a GitHub issue with a clear description of the problem and steps to reproduce.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
