# Start working on a feature
jj git fetch
jj new main
jj bookmark create feature/my-feature -r @

# Develop
jj status
jj diff
jj describe -m "Implement my feature"

# Create another change
jj new

# Inspect history
jj log
jj show

# Update from remote main
jj git fetch
jj rebase -d main@origin

# Push feature
jj git push --bookmark feature/my-feature

# After PR is merged
jj git fetch
jj new main@origin

# Undo a jj operation
jj undo

# Abandon current change
jj abandon

# moving main to head
jj bookmark move main --to @
