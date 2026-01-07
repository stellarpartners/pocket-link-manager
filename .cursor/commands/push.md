Review the latest git changes, show a summary of what will be committed, and then push the changes to GitHub.

1. First, check the git status and show what files have changed
2. Display a summary of changes (modified, added, deleted files)
3. Show a brief diff summary using `git diff --stat`
4. Stage all changes with `git add -A`
5. If there are changes, commit them with an appropriate message (ask the user for a commit message or auto-generate one based on the changes)
6. Push to GitHub using `git push origin <current-branch>`

If there are no changes, inform the user that the working directory is clean.
