@echo off
echo ---------------------------------------------------
echo  Amami News Map - GitHub Upload Helper
echo ---------------------------------------------------
echo.
echo This script will help you upload your code to GitHub.
echo.

WHERE git >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed or not in your PATH.
    echo Please install Git for Windows from: https://git-scm.com/download/win
    echo After installing, restart your computer and run this script again.
    pause
    exit /b
)

if not exist .git (
    echo Initializing Git repository...
    git init
)

echo Adding files...
git add .

echo Committing files...
git commit -m "Initial commit of Amami News Map"

echo.
set REPO_URL=https://github.com/nelsonmzsm/amaminewsmap.git
echo Target Repository: %REPO_URL%

echo.
echo Setting remote origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo Renaming branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
echo (You may be asked to sign in to GitHub in a browser window)
git push -u origin main

echo.
echo ---------------------------------------------------
if %ERRORLEVEL% EQU 0 (
    echo  Upload Successful!
    echo  You can now proceed to Render.com to deploy.
) else (
    echo  Upload Failed. Please check the error messages above.
)
echo ---------------------------------------------------
pause
