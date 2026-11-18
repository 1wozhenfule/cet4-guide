param([Parameter(Mandatory=$true)][string]$RepoUrl)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".git")) { throw "当前目录不是 git 仓库" }

git remote remove origin 2>$null
git remote add origin $RepoUrl
Write-Host "推送到 $RepoUrl ..." -ForegroundColor Cyan
git push -u origin main

Write-Host ""
Write-Host "推送成功。最后一步（网页上点两下）：" -ForegroundColor Green
Write-Host "  仓库 Settings → Pages → Source 选 Deploy from a branch"
Write-Host "  Branch 选 main，目录选 / (root)，Save"
Write-Host "  约 1 分钟后访问 https://<用户名>.github.io/<仓库名>/"
