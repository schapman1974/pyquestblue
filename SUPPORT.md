# Support policy

Use GitHub Discussions for usage questions and design conversations, and GitHub Issues for
reproducible defects or feature requests. Security reports follow [SECURITY.md](SECURITY.md), never a
public issue. QuestBlue account, billing, carrier, provisioning, and provider-side service incidents
must be handled by QuestBlue support; pyquestblue cannot inspect or change provider systems.

Supported Python versions are the versions declared in `pyproject.toml` and tested in CI. A new
Python version becomes supported after it is added to the classifiers and cross-platform matrix.
Removal of a Python version is announced in a minor release and occurs no earlier than the next
major release, except when maintaining it would prevent a necessary security fix.

Public support is best effort. A clear report includes the pyquestblue and Python versions, operating
system, a minimal sanitized reproduction, expected behavior, and the full exception type. Never
attach credentials or real customer communications.
