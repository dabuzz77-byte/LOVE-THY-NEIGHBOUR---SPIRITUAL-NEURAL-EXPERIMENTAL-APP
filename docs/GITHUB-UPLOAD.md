# Upload this app to GitHub

## Recommended: GitHub Desktop

1. Extract `Neural-App-GitHub-Ready.zip` on your computer.
2. In GitHub Desktop, choose **File → Add local repository** and choose the extracted folder that contains README.md, desktop.py and neural_app.
3. If Desktop says it is not a Git repository, choose its **create a repository here** option. Keep the existing files. Do not add a second license/template over the supplied files.
4. Review the changed files, write an initial-commit summary and commit to the main branch.
5. Choose **Publish repository**. Check the repository name and privacy before confirming. A public repository is needed for an open-source programme application.

The browser's 100-file batch limit does not apply to GitHub Desktop/Git pushes.

## Alternative: browser uploads, 100 files or fewer per batch

A separate `Neural-App-GitHub-Upload-Batches` folder contains numbered, independent ZIPs. **Do not upload the ZIPs themselves as source files.** GitHub does not unpack them for you.

Extract one numbered ZIP at a time into a separate temporary folder. On the GitHub repository's ROOT page choose **Add file → Upload files**. Drag the CONTENTS of that extracted batch, including its existing subfolders, onto the uploader. Commit that batch, return to the repository root and repeat for every numbered ZIP. Always preserve the folder structure. Never upload the outer batch-number folder. Each ZIP contains no more than 100 repository files.

Do not move all the source files into a single directory. `neural_app`, `assets`, `ui`, `references`, `tools` and `.github` must keep their paths. Windows may hide `.github`, `.gitignore` and `.gitattributes`; include those too. If your browser strips nested paths or hidden files, use GitHub Desktop instead.

Wait until all batches are committed before installing or testing. No credentials, local `data` directory, installed model or runtime folder should be added later.
