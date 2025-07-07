#!/bin/bash
# Setup pre-commit hooks for the project

set -e

echo "🔧 Setting up pre-commit hooks..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install --user pre-commit
else
    echo "✅ pre-commit is already installed"
fi

# Install the git hook scripts
echo "🪝 Installing git hooks..."
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg

# Run against all files (optional - can be slow on large repos)
read -p "Do you want to run pre-commit against all files now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🏃 Running pre-commit on all files..."
    pre-commit run --all-files || true
fi

echo "✅ Pre-commit hooks successfully installed!"
echo ""
echo "Pre-commit will now run automatically on git commit."
echo "You can manually run it with: pre-commit run --all-files"
echo ""
echo "To update hooks: pre-commit autoupdate"
echo "To skip hooks (emergency only): git commit --no-verify"