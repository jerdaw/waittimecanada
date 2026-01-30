#!/bin/bash
# migrate-structure.sh - Migrate repository to modern structure
# Usage: ./scripts/migrate-structure.sh

set -e  # Exit on error

echo "🚀 WaitTime Canada - Repository Structure Migration"
echo "===================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "mkdocs.yml" ]; then
    print_error "mkdocs.yml not found. Please run from project root."
    exit 1
fi

echo "This script will migrate your repository to the modern structure."
echo "It will:"
echo "  - Rename scrapers/ → backend/"
echo "  - Reorganize documentation"
echo "  - Update imports and paths"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Create backup
echo ""
echo "📦 Creating backup..."
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r scrapers frontend database docs .github "$BACKUP_DIR/" 2>/dev/null || true
print_status "Backup created in $BACKUP_DIR/"

# Phase 1: Rename directories
echo ""
echo "📁 Phase 1: Renaming directories..."

if [ -d "scrapers" ]; then
    mv scrapers backend
    print_status "Renamed scrapers/ → backend/"
else
    print_warning "scrapers/ not found, skipping"
fi

# Phase 2: Reorganize backend
echo ""
echo "🔧 Phase 2: Reorganizing backend structure..."

if [ -d "backend/src" ]; then
    # Create new structure
    mkdir -p backend/src/waittime/{core,scrapers,services,cli}

    # Move files if they exist
    if [ -d "backend/src/core" ]; then
        mv backend/src/core/* backend/src/waittime/core/ 2>/dev/null || true
    fi

    if [ -d "backend/src/scrapers" ]; then
        mv backend/src/scrapers/* backend/src/waittime/scrapers/ 2>/dev/null || true
    fi

    # Create __init__.py files
    touch backend/src/waittime/__init__.py
    touch backend/src/waittime/core/__init__.py
    touch backend/src/waittime/scrapers/__init__.py
    touch backend/src/waittime/services/__init__.py
    touch backend/src/waittime/cli/__init__.py

    print_status "Created waittime package structure"
else
    print_warning "backend/src not found, skipping package reorganization"
fi

# Move migrations
if [ -d "database" ]; then
    mkdir -p backend/migrations
    mv database/migrations/* backend/migrations/ 2>/dev/null || true
    mv database/seed backend/migrations/ 2>/dev/null || true
    print_status "Moved database/ → backend/migrations/"
fi

# Phase 3: Reorganize tests
echo ""
echo "🧪 Phase 3: Reorganizing tests..."

if [ -d "backend/tests" ]; then
    mkdir -p backend/tests/{unit,integration,e2e,fixtures}

    # Move existing tests (you'll need to categorize manually)
    print_warning "Tests directory exists but needs manual categorization"
    print_warning "Please organize tests into unit/, integration/, e2e/"
else
    print_warning "backend/tests not found, skipping"
fi

# Phase 4: Update documentation structure
echo ""
echo "📚 Phase 4: Organizing documentation..."

# Create new docs structure
mkdir -p docs/{getting-started,architecture,development,deployment,reference,adr,planning,guides,assets}

# Move existing docs if they exist
if [ -f "docs/IMPLEMENTATION.md" ]; then
    mv docs/IMPLEMENTATION.md docs/development/setup.md
    print_status "Moved IMPLEMENTATION.md → docs/development/setup.md"
fi

if [ -f "docs/DATABASE.md" ]; then
    mv docs/DATABASE.md docs/architecture/database.md
    print_status "Moved DATABASE.md → docs/architecture/database.md"
fi

if [ -f "docs/API.md" ]; then
    mv docs/API.md docs/architecture/api.md
    print_status "Moved API.md → docs/architecture/api.md"
fi

if [ -f "docs/ROADMAP.md" ]; then
    mv docs/ROADMAP.md docs/planning/roadmap.md
    print_status "Moved ROADMAP.md → docs/planning/roadmap.md"
fi

if [ -f "er-times-plan.md" ]; then
    mv er-times-plan.md docs/planning/strategic-plan.md
    print_status "Moved er-times-plan.md → docs/planning/strategic-plan.md"
fi

# Create placeholder index files
cat > docs/getting-started/index.md << 'EOF'
# Getting Started

Welcome to WaitTime Canada! This section will help you get up and running quickly.

## Quick Links

- [Quick Start](quick-start.md) - Get started in 5 minutes
- [Installation](installation.md) - Detailed installation guide
- [First Scraper](first-scraper.md) - Build your first scraper

## Prerequisites

Before you begin, ensure you have:

- Python 3.12+
- Node.js 20.x LTS
- pnpm 8.x
- A Supabase account

## Next Steps

1. Follow the [Quick Start](quick-start.md) guide
2. Review the [Architecture](../architecture/overview.md) documentation
3. Explore the [Development](../development/setup.md) guides
EOF

cat > docs/architecture/index.md << 'EOF'
# Architecture

WaitTime Canada is built on a modern, scalable architecture designed for data integrity and transparency.

## Key Components

- [Overview](overview.md) - High-level architecture
- [Data Ontology](data-ontology.md) - Metric ontology system
- [Database](database.md) - PostgreSQL schema and migrations
- [API](api.md) - REST API specification
- [Scrapers](scrapers.md) - Scraper architecture

## Architecture Principles

1. **Data Integrity** - Never normalize incomparable data
2. **Transparency** - Expose methodological differences
3. **Scalability** - Design for growth
4. **Observability** - Built-in monitoring and alerting
EOF

print_status "Created documentation structure"

# Phase 5: Update configuration files
echo ""
echo "⚙️  Phase 5: Updating configuration files..."

# Update pyproject.toml package name (basic sed replacement)
if [ -f "backend/pyproject.toml" ]; then
    sed -i.bak 's/name = "waittime-scrapers"/name = "waittime"/' backend/pyproject.toml
    sed -i.bak 's/scrapers\//backend\//' backend/pyproject.toml
    rm backend/pyproject.toml.bak
    print_status "Updated backend/pyproject.toml"
fi

# Update GitHub Actions workflows
if [ -d ".github/workflows" ]; then
    for file in .github/workflows/*.yml; do
        if [ -f "$file" ]; then
            sed -i.bak 's/scrapers\//backend\//' "$file"
            rm "$file.bak"
        fi
    done
    print_status "Updated GitHub Actions workflows"
fi

# Phase 6: Create new files
echo ""
echo "📝 Phase 6: Creating new configuration files..."

# Create .editorconfig if it doesn't exist
if [ ! -f ".editorconfig" ]; then
    cat > .editorconfig << 'EOF'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,pyi}]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{ts,tsx,js,jsx,json}]
indent_style = space
indent_size = 2

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
EOF
    print_status "Created .editorconfig"
fi

# Create VS Code settings directory
mkdir -p .vscode
if [ ! -f ".vscode/settings.json" ]; then
    cat > .vscode/settings.json << 'EOF'
{
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "python.testing.pytestEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
EOF
    print_status "Created .vscode/settings.json"
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "⚠️  IMPORTANT: Manual steps required:"
echo ""
echo "1. Update Python imports:"
echo "   - Change 'from src.core' → 'from waittime.core'"
echo "   - Change 'from src.scrapers' → 'from waittime.scrapers'"
echo ""
echo "2. Categorize tests:"
echo "   - Move tests to backend/tests/unit/, integration/, or e2e/"
echo ""
echo "3. Install MkDocs:"
echo "   - pip install mkdocs-material"
echo "   - Test with: mkdocs serve"
echo ""
echo "4. Run tests to verify:"
echo "   - cd backend && pytest"
echo "   - cd frontend && pnpm test"
echo ""
echo "5. Review and commit changes"
echo ""
echo "📦 Backup available in: $BACKUP_DIR/"
