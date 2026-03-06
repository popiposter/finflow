# GitHub CLI setup

## Why install gh locally
`gh` gives Claude and the developer a standard way to work with issues, PRs, comments, and repository metadata from the terminal.

## Windows install options
### Option 1: winget
Run PowerShell as your user and execute:
```powershell
winget install --id GitHub.cli
```

### Option 2: Scoop
If you use Scoop:
```powershell
scoop install gh
```

## Verify install
```powershell
gh --version
```

## Authenticate
```powershell
gh auth login
```
Recommended answers:
- GitHub.com
- HTTPS
- Login with a web browser

After login, check status:
```powershell
gh auth status
```

## Optional: let git use gh credential helper
```powershell
gh auth setup-git
```

## Useful commands
```powershell
gh issue list
gh issue view 1
gh pr list
gh repo view popiposter/finflow
```
