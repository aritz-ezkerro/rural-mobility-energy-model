<#
.SYNOPSIS
  End-of-session helper: stage, check for large files, commit using the work
  log convention, and push.

.EXAMPLE
  .\src\scripts\sync.ps1 -Start "12:02" -Title "Remove a file" -Tasks "Remove a useless file","Update sync.ps1 script"

#>
param(
  [Parameter(Mandatory = $true)][string]$Start,
  [Parameter(Mandatory = $true)][string]$Title,
  [string[]]$Tasks = @(),
  [int]$MaxSizeMB = 50
)

$ErrorActionPreference = "Stop"

# 1. Stage everything that is not gitignored
git add .

# 2. Refuse to commit large files (GitHub rejects anything over 100 MB)
$limit = $MaxSizeMB * 1MB
$large = git diff --cached --name-only |
  ForEach-Object { Get-Item -LiteralPath $_ -ErrorAction SilentlyContinue } |
  Where-Object { $_.Length -gt $limit }

if ($large) {
  Write-Host "Stopped: these staged files exceed $MaxSizeMB MB:" -ForegroundColor Red
  $large | ForEach-Object { Write-Host ("  {0}  ({1:N1} MB)" -f $_.FullName, ($_.Length / 1MB)) }
  Write-Host "Move them to data/raw or data/interim (gitignored) and run again."
  git reset | Out-Null
  exit 1
}

# 3. Nothing to commit?
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "Nothing to commit."
  exit 0
}

# 4. Commit with the bracketed start-time convention
$subject = "[$Start] $Title"
if ($Tasks.Count -gt 0) {
  $body = ($Tasks | ForEach-Object { "- $_" }) -join "`n"
  git commit -m $subject -m $body
} else {
  git commit -m $subject
}

# 5. Integrate the bot's log.md commit, then push
git pull --rebase
git push

Write-Host "Done. Run 'git pull' later to receive the updated log.md." -ForegroundColor Green