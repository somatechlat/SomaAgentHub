# SomaAgentHub Documentation (English)

![Version](https://img.shields.io/badge/version-1.0.0-blue)

This directory contains the English version of the SomaAgentHub documentation.

## Language Support

Currently supported languages:
- **English (en)** - Primary language, complete documentation
- **German (de)** - Placeholder for future translation

## Translation Guidelines

When translating documentation:

1. **Maintain Structure**: Keep the same file structure and naming
2. **Preserve Technical Terms**: Keep service names, ports, and commands in English
3. **Update Links**: Ensure relative links work within the translated structure
4. **Version Consistency**: All translations should reference the same version

## File Mapping

| English File | Purpose | Translation Priority |
|--------------|---------|---------------------|
| `README.md` | Project overview | High |
| `user-manual/` | End-user documentation | High |
| `technical-manual/` | Operations and deployment | Medium |
| `development-manual/` | Developer guides | Medium |
| `onboarding-manual/` | New contributor guides | Low |

## Contributing Translations

To contribute translations:

1. Create language directory: `docs/i18n/{language-code}/`
2. Copy English structure
3. Translate content while preserving technical accuracy
4. Test all links and references
5. Submit pull request with translation

## Technical Considerations

- **Code Examples**: Keep code blocks in English
- **API Endpoints**: Do not translate URL paths or parameter names
- **Configuration**: Keep YAML/JSON configuration examples unchanged
- **Commands**: Keep shell commands and Kubernetes resources in English