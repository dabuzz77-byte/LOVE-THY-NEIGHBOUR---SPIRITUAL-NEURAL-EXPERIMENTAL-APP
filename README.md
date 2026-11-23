# Neural App — Souls Over Digits

A local research and learning workspace combining animated lessons, prayer, stochastic visualisations, experimental reasoning tools, Python/Java calculation modules and optional language-model assistants.

**Mission:** Love thy neighbour. Share knowledge freely and put the welfare of people and other living beings before financial value.

## What is in this repository

- `neural_app/`: application backend, reasoning experiments and integrated calculation modules.
- `ui/` and `assets/`: browser interface, animated diagrams, lesson illustrations and source-linked studies.
- `references/`: public lesson/reference material and engine catalogues.
- `preserved/`: selected legacy source code used by the integrated sections.
- `tests/`: existing project tests; `tools/verify_source.py` is the independent release check.
- `connectors/`: optional browser-extension source, with no installed browser profiles.

This is the **full application source edition**, rather than the lessons-only website export. Local data, account keys, chat databases, cookies, browser profiles, learned personal state, model weights and installed dependency runtimes are not included. A new installation starts with its own data.

## Quick start — Windows

1. Install Python **3.12** and a JDK **21 or newer**, with `java` and `javac` available on PATH. Microsoft Edge WebView2 is needed for the desktop window.
2. Extract/clone this repository into a folder you can write to.
3. Run **`Setup Neural App.cmd`**. It creates `.venv`, installs the declared Python packages, downloads the listed Java dependencies and rebuilds the app's Java classes. Internet access is needed for setup.
4. Run **`Start Neural App.cmd`**. The same local interface is normally available at `http://127.0.0.1:8797/` while the app runs.
5. For the browser interface without a desktop window: `.venv\Scripts\python.exe desktop.py --headless`.

Ollama and local language models are optional separate installations. Each user configures their own providers and credentials. GPU acceleration and platform-specific external tools are optional and require their own installations. Setup may need adjustments for a different OS; the integrated desktop/Java paths target Windows.

## Checks and practical limits

Run `python tools/verify_source.py` for syntax, package privacy boundaries, required files and lossless transport checks. The existing test suite covers additional scenarios, but many tests require optional dependencies or configured services. See **docs/RELEASE-CHECKS.md** for what was actually verified for this release.

The stochastic streams generate and transform data. Reasoning tools apply explicit algorithms and optional model inference. Their usefulness is assessed from observed task results. The repository does not include proprietary hosted-model weights or an implicit connection to external AI services.

The lessons preserve the author's spiritual framework and interfaith prayer mission. Authored spiritual interpretations and illustrative animations are presented alongside their source-linked studies.

## Local permissions and data

The app includes command execution, file tools and optional network integrations. Review and configure these capabilities for your own machine before enabling them. Existing application checks and permission gates remain intact. Default web access is loopback-only; do not expose the desktop server directly to the public internet. `data/` and provider credentials are deliberately ignored by Git.

## Uploading to GitHub

**Recommended:** use GitHub Desktop to add this folder as a local repository and publish it. This avoids the browser's 100-file upload batch limit. See **docs/GITHUB-UPLOAD.md** for the numbered-browser-batch alternative.

Creating a repository is separate from applying to support programmes. No application, credit award or external review is implied by this release.

## License and third-party material

The author's original contributions retain their **CC0 1.0** dedication, already present in the project. This applies only to rights the author owns. Read **LICENSE** and **THIRD_PARTY_NOTICES.md**. Existing third-party source, religious translations, images, fonts, quotations and trademarks retain their own terms. JFreeSVG is GPL-3.0-or-later; combining/distributing it carries the corresponding GPL obligations. Dependency binaries are obtained separately during setup, not bundled in this source package.
