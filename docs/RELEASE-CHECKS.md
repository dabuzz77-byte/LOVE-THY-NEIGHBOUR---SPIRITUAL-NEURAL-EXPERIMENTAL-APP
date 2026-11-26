# Source release checks — 23 November 2026

Passed:

- 1,210 Python source files parsed.
- 120 JSON/GeoJSON/web-manifest files parsed.
- 252 JavaScript source files parsed.
- Binary/ternary/Fourier-qutrit round trips preserved exact bytes and leading zeroes in the release checker.
- Known credential patterns screened; no credential values matched.
- Runtime databases, browser profiles, installed runtimes, compiled classes and model weights excluded.
- Every source file is below the 25 MB browser-upload threshold. Every numbered upload batch contains 100 files or fewer.

Privacy preparation replaced developer-specific user paths and email addresses in copied text, and excluded selected personal reference/audit files. This is an automated release boundary check, not a review of every image or proof of ownership of all externally authored references.

Not completed for this source-only packaging:

- A fresh dependency install and full desktop startup.
- Java rebuild: the local javac command did not return, so it was stopped. The source package includes a PATH-based JDK lookup and rebuild instructions for recipients.
- GPU acceleration, configured external providers, authenticated browser integrations and network-device checks.
- The entire historical integration test suite against a clean machine.

No files were published to GitHub or submitted to a support programme during this preparation.

## Credential cleanup — 26 November 2026

GitHub push protection detected a hard-coded API-key literal in legacy references after the initial archive upload. That literal and another hard-coded API-key literal were replaced in all matching public-source files. The source checker now screens long credential assignments, including API_KEY_SECRET. The cleaned release must pass GitHub push protection. Earlier public archive versions may remain in Git history; any real affected key should be revoked by its owner.
