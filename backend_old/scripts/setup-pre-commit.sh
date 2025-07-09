#!/bin/bash

echo "🚀 Setting up pre-commit hooks for strict quality enforcement..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Install the pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Create baseline for detect-secrets
echo "🔐 Creating secrets baseline..."
detect-secrets scan > .secrets.baseline || true

# Run pre-commit on all files to check current state
echo "🔍 Running pre-commit on all files (this may take a while)..."
pre-commit run --all-files || true

echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "Pre-commit will now run automatically on every commit to ensure:"
echo "  - ✓ Python code is formatted with Black"
echo "  - ✓ Python code passes flake8 linting"
echo "  - ✓ Python code passes mypy type checking"
echo "  - ✓ Python code passes bandit security checks"
echo "  - ✓ JavaScript/TypeScript code passes ESLint"
echo "  - ✓ Code is formatted with Prettier"
echo "  - ✓ No secrets are committed"
echo "  - ✓ No large files are committed"
echo "  - ✓ Commit messages follow conventional format"
echo ""
echo "To bypass pre-commit hooks (NOT RECOMMENDED), use: git commit --no-verify"