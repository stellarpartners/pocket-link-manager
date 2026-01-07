# Documentation

Comprehensive documentation for the Pocket Link Manager project.

## Quick Links

- **[Main README](../README.md)** - Project overview, installation, and quick start
- **[Python Version Guide](PYTHON_VERSION.md)** - Python compatibility and version requirements
- **[Migration Plan](Plan.md)** - Pocket to Obsidian migration strategy (project-specific)

## Module Documentation

### Core Modules

- **[Database Module](../database/README.md)** - Database models, queries, and import functionality
- **[Web Module](../web/README.md)** - Flask web application and routes
- **[Extractor Module](../extractor/README.md)** - Content extraction and URL processing utilities

### Scripts & Tools

- **[Scripts Directory](../scripts/README.md)** - Utility scripts for crawling, analysis, and import
- **[Tools Directory](../tools/README.md)** - Root-level utility tools
- **[Tests Directory](../tests/README.md)** - Test suite documentation

## Documentation by Topic

### Getting Started

1. **Installation**: See [Main README - Installation](../README.md#installation)
2. **Quick Start**: See [Main README - Quick Start](../README.md#quick-start)
3. **Python Requirements**: See [Python Version Guide](PYTHON_VERSION.md)

### Development

- **Project Structure**: See [Main README - Project Structure](../README.md#project-structure)
- **Configuration**: See [Main README - Configuration](../README.md#configuration)
- **Code Quality**: See [Main README - Development](../README.md#development)

### Usage Guides

- **Web Interface**: See [Web Module README](../web/README.md)
- **Content Extraction**: See [Extractor Module README](../extractor/README.md)
- **Database Operations**: See [Database Module README](../database/README.md)
- **Scripts**: See [Scripts README](../scripts/README.md)

### Advanced Topics

- **Python Compatibility**: See [Python Version Guide](PYTHON_VERSION.md)
- **Migration Planning**: See [Migration Plan](Plan.md) (project-specific)

## Documentation Structure

```
docs/
├── README.md              # This file - documentation index
├── PYTHON_VERSION.md      # Python version compatibility guide
└── Plan.md                # Pocket to Obsidian migration plan

[Module READMEs]
├── database/README.md     # Database module documentation
├── web/README.md          # Web module documentation
├── extractor/README.md    # Extractor module documentation
├── scripts/README.md      # Scripts documentation
├── tools/README.md        # Tools documentation
└── tests/README.md        # Tests documentation
```

## Contributing to Documentation

When adding new features or modules:

1. Update the relevant module README
2. Add examples to the main README if it's a major feature
3. Update this index if adding new documentation sections
4. Keep documentation consistent with code changes

## Finding Information

- **New to the project?** Start with the [Main README](../README.md)
- **Setting up development?** See [Development section](../README.md#development)
- **Using a specific module?** Check the module's README
- **Running into issues?** See [Troubleshooting](../README.md#troubleshooting)
