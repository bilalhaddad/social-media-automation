#!/bin/bash

echo "🚀 Social Media Automation - GitHub Push Script"
echo "================================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

echo "✅ Git repository found"
echo "📊 Repository status:"
git log --oneline
echo ""

echo "📋 Files ready to push: $(git ls-files | wc -l) files"
echo ""

# Check if remote exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "🔗 Current remote: $(git remote get-url origin)"
    echo ""
fi

echo "🎯 TO PUSH TO GITHUB:"
echo "===================="
echo ""
echo "1. CREATE REPOSITORY ON GITHUB:"
echo "   - Go to: https://github.com/new"
echo "   - Name: social-media-automation"
echo "   - Description: Comprehensive social media automation tool"
echo "   - Choose Public or Private"
echo "   - DO NOT initialize with README/gitignore/license"
echo "   - Click 'Create repository'"
echo ""
echo "2. AFTER CREATING, RUN THESE COMMANDS:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/social-media-automation.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. VERIFY SUCCESS:"
echo "   git remote -v"
echo "   git status"
echo ""
echo "🎉 Your social media automation tool will be live on GitHub!"
