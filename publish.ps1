param(
    [Parameter(Mandatory = $true)][string]$RepoUrl,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".git")) { throw "当前目录不是 git 仓库" }

# 解析仓库地址，兼容 https 与 ssh 两种写法
$clean = $RepoUrl.Trim() -replace '\.git$', ''
if ($clean -match '^git@github\.com:(?<u>[^/]+)/(?<r>[^/]+)$') {
    $user = $Matches.u; $repo = $Matches.r
}
elseif ($clean -match 'github\.com/(?<u>[^/]+)/(?<r>[^/]+)$') {
    $user = $Matches.u; $repo = $Matches.r
}
else { throw "无法解析仓库地址：$RepoUrl" }

$htmlUrl = "https://github.com/$user/$repo"
$pagesUrl = "https://$user.github.io/$repo/"
Write-Host "仓库：$htmlUrl" -ForegroundColor Cyan
Write-Host "站点：$pagesUrl" -ForegroundColor Cyan

function Write-Utf8NoBom($path, $text) {
    [System.IO.File]::WriteAllText($path, $text,
        (New-Object System.Text.UTF8Encoding($false)))
}

# README 里的在线地址占位符
$readme = [System.IO.File]::ReadAllText((Join-Path $PSScriptRoot "README.md"))
$readme = $readme.Replace("{{PAGES_URL}}", $pagesUrl)
Write-Utf8NoBom (Join-Path $PSScriptRoot "README.md") $readme

# 每个页面侧栏的 GitHub 链接
Get-ChildItem -Path $PSScriptRoot -Filter *.html | ForEach-Object {
    $t = [System.IO.File]::ReadAllText($_.FullName)
    $t = $t.Replace('href="https://github.com/"', ('href="' + $htmlUrl + '"'))
    Write-Utf8NoBom $_.FullName $t
}

if ($DryRun) {
    Write-Host "DryRun：已写入链接，未提交、未推送。" -ForegroundColor Yellow
    exit 0
}

git remote remove origin 2>$null
git remote add origin $RepoUrl
git add -A
git commit -m "chore: 填入在线地址与仓库链接" --quiet
if ($LASTEXITCODE -ne 0) { Write-Host "没有需要提交的改动，继续推送" }

git push -u origin main

Write-Host ""
Write-Host "推送成功。最后一步（网页上点两下）：" -ForegroundColor Green
Write-Host "  仓库 Settings -> Pages -> Source 选 Deploy from a branch"
Write-Host "  Branch 选 main，目录选 / (root)，Save"
Write-Host "  约 1 分钟后访问 $pagesUrl"