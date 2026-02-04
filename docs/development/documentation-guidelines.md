# Documentation Guidelines

This project follows a "Documentation-as-Code" philosophy. Documentation should be treat with the same rigor as code.

## Principles

1. **Accuracy**: Documentation must match the current state of the codebase.
2. **Conciseness**: Avoid fluff. Use bullet points and tables for readability.
3. **Traceability**: Link back to ADRs or implementation plans when relevant.
4. **Clinical Tone**: Maintain a professional, physician-innovator tone (CanMEDS focus).

## File Locations

- **Architecture**: `docs/architecture/`
- **ADRs**: `docs/adr/`
- **Guides**: `docs/guides/`
- **Planning**: `docs/planning/`
- **Implementation Summaries**: `docs/implementation/`

## Markdown Standards

- Use GitHub Flavored Markdown (GFM).
- All code blocks must have language tags.
- Headers should follow logical hierarchy (# -> ## -> ###).
- Use clickable file links: `[filename](file:///path/to/file)`.

## Review Process

- Documentation updates should be included in the same PR as code changes.
- Large architectural changes require an ADR.
- Before launch, a final documentation review (like `docs/final-documentation-review.md`) must be performed.

## Attribution

- **CRITICAL**: ONLY human contributors may be listed in documentation.
- Do NOT attribute any work to AI assistants, agents, or automated tools.
