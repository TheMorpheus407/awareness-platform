#!/bin/bash

# Script to help push changes to GitHub when authentication is needed

echo "GitHub Push Helper"
echo "=================="
echo ""
echo "Since GitHub CLI authentication is not available, you have several options:"
echo ""
echo "Option 1: Use HTTPS with Personal Access Token"
echo "1. Create a personal access token at: https://github.com/settings/tokens"
echo "2. Run: git remote set-url origin https://YOUR_TOKEN@github.com/TheMorpheus407/awareness-platform.git"
echo "3. Run: git push origin main"
echo ""
echo "Option 2: Use SSH"
echo "1. Add your SSH key to GitHub: https://github.com/settings/keys"
echo "2. Run: git remote set-url origin git@github.com:TheMorpheus407/awareness-platform.git"
echo "3. Run: git push origin main"
echo ""
echo "Option 3: Use GitHub Desktop or another Git GUI"
echo ""
echo "Current status:"
git status --short
echo ""
echo "Commits ready to push:"
git log origin/main..HEAD --oneline