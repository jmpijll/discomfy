# DisComfy Wiki Publishing Script
# Automates publishing wiki documentation to GitHub

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "publish"
)

Write-Host "=== DisComfy Wiki Publisher ===" -ForegroundColor Cyan
Write-Host ""

$wikiDocsPath = "wiki-docs"
$wikiRepoPath = "..\discomfy.wiki"
$repoUrl = "https://github.com/jmpijll/discomfy.wiki.git"

function Initialize-Wiki {
    Write-Host "Initializing wiki..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "IMPORTANT: You need to create the first wiki page manually!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Green
    Write-Host "1. Go to: https://github.com/jmpijll/discomfy/wiki" -ForegroundColor White
    Write-Host "2. Click 'Create the first page'" -ForegroundColor White
    Write-Host "3. Title: Home" -ForegroundColor White
    Write-Host "4. Content: Copy from wiki-docs/Home.md" -ForegroundColor White
    Write-Host "5. Click 'Save Page'" -ForegroundColor White
    Write-Host ""
    Write-Host "After creating the first page, run this script again with '-Action publish'" -ForegroundColor Yellow
    Write-Host ""
    
    # Open browser to wiki
    Start-Process "https://github.com/jmpijll/discomfy/wiki"
}

function Publish-Wiki {
    Write-Host "Publishing wiki documentation..." -ForegroundColor Yellow
    Write-Host ""
    
    # Check if wiki-docs exists
    if (-not (Test-Path $wikiDocsPath)) {
        Write-Host "ERROR: wiki-docs directory not found!" -ForegroundColor Red
        Write-Host "Please run this script from the discomfy root directory." -ForegroundColor Red
        exit 1
    }
    
    # Clone wiki repository if not exists
    if (-not (Test-Path $wikiRepoPath)) {
        Write-Host "Cloning wiki repository..." -ForegroundColor Green
        Set-Location ..
        
        try {
            git clone $repoUrl 2>&1 | Out-Null
            Write-Host "✓ Wiki repository cloned" -ForegroundColor Green
        } catch {
            Write-Host "ERROR: Failed to clone wiki repository!" -ForegroundColor Red
            Write-Host "Make sure you've initialized the wiki (run with -Action init)" -ForegroundColor Red
            Set-Location discomfy
            exit 1
        }
        
        Set-Location discomfy
    } else {
        Write-Host "✓ Wiki repository exists" -ForegroundColor Green
    }
    
    # Copy wiki files
    Write-Host ""
    Write-Host "Copying wiki files..." -ForegroundColor Green
    
    $files = Get-ChildItem -Path $wikiDocsPath -Filter "*.md" -Exclude "README.md"
    foreach ($file in $files) {
        Copy-Item -Path $file.FullName -Destination $wikiRepoPath -Force
        Write-Host "  Copied: $($file.Name)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "✓ Files copied successfully" -ForegroundColor Green
    
    # Commit and push
    Write-Host ""
    Write-Host "Committing changes..." -ForegroundColor Green
    
    Set-Location $wikiRepoPath
    
    git add *.md
    $commitMessage = "Update wiki documentation`n`n- Comprehensive guides added`n- All pages updated`n- Examples and troubleshooting included"
    git commit -m $commitMessage
    
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    
    try {
        git push origin master
        Write-Host ""
        Write-Host "✓ Wiki published successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "View your wiki at: https://github.com/jmpijll/discomfy/wiki" -ForegroundColor Cyan
        
        # Open browser to wiki
        Start-Process "https://github.com/jmpijll/discomfy/wiki"
        
    } catch {
        Write-Host ""
        Write-Host "ERROR: Failed to push to GitHub!" -ForegroundColor Red
        Write-Host "You may need to authenticate with GitHub:" -ForegroundColor Yellow
        Write-Host "  Run: gh auth login" -ForegroundColor White
    }
    
    Set-Location ..\discomfy
}

function Update-Wiki {
    Write-Host "Updating wiki documentation..." -ForegroundColor Yellow
    
    if (-not (Test-Path $wikiRepoPath)) {
        Write-Host "ERROR: Wiki repository not found!" -ForegroundColor Red
        Write-Host "Run with '-Action publish' first to set up the wiki." -ForegroundColor Red
        exit 1
    }
    
    # Pull latest changes
    Write-Host ""
    Write-Host "Pulling latest changes..." -ForegroundColor Green
    Set-Location $wikiRepoPath
    git pull origin master
    Set-Location ..\discomfy
    
    # Copy updated files
    Write-Host ""
    Write-Host "Copying updated files..." -ForegroundColor Green
    
    $files = Get-ChildItem -Path $wikiDocsPath -Filter "*.md" -Exclude "README.md"
    foreach ($file in $files) {
        Copy-Item -Path $file.FullName -Destination $wikiRepoPath -Force
        Write-Host "  Updated: $($file.Name)" -ForegroundColor White
    }
    
    # Commit and push
    Write-Host ""
    Write-Host "Committing updates..." -ForegroundColor Green
    
    Set-Location $wikiRepoPath
    
    git add *.md
    git commit -m "Update wiki documentation - $(Get-Date -Format 'yyyy-MM-dd')"
    
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    git push origin master
    
    Write-Host ""
    Write-Host "✓ Wiki updated successfully!" -ForegroundColor Green
    
    Set-Location ..\discomfy
}

# Main script logic
switch ($Action.ToLower()) {
    "init" {
        Initialize-Wiki
    }
    "publish" {
        Publish-Wiki
    }
    "update" {
        Update-Wiki
    }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host ""
        Write-Host "Usage:" -ForegroundColor Yellow
        Write-Host "  .\publish-wiki.ps1 -Action init      # Initialize wiki (first time)" -ForegroundColor White
        Write-Host "  .\publish-wiki.ps1 -Action publish   # Publish wiki (default)" -ForegroundColor White
        Write-Host "  .\publish-wiki.ps1 -Action update    # Update existing wiki" -ForegroundColor White
        exit 1
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green

