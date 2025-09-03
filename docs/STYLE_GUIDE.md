# EcoMate Documentation Style Guide

> Standardized formatting, terminology, and style guidelines for all EcoMate documentation.

## Document Structure

### Header Format
All documentation files must follow this header structure:

```markdown
# Document Title

> Brief description of the document's purpose and scope.

## Table of Contents (for long documents)
- [Section 1](#section-1)
- [Section 2](#section-2)

## Introduction/Overview
[Content starts here]
```

### Section Hierarchy
- `#` - Document title (only one per document)
- `##` - Main sections
- `###` - Subsections
- `####` - Sub-subsections (use sparingly)

## Terminology Standards

### Technical Terms
- **Person Equivalent (PE)**: Always use "PE" abbreviation after first mention
- **Liters per Day**: Use "L/day" or "kL/day" consistently
- **Biochemical Oxygen Demand**: Use "BOD₅" with subscript
- **Total Suspended Solids**: Use "TSS"
- **Dissolved Oxygen**: Use "DO"
- **Moving Bed Biofilm Reactor**: Use "MBBR" after first mention
- **Membrane Bioreactor**: Use "MBR" after first mention
- **Conventional Activated Process**: Use "CAP" after first mention

### Company References
- **Company Name**: Always "EcoMate" (not "Ecomate" or "ECO-MATE")
- **Products**: "EcoMate wastewater treatment systems"
- **API**: "EcoMate API" or "the API"

### Geographic References
- **Region**: "Southern Africa" or "Southern African"
- **Country**: "South Africa" (full name)

## Formatting Standards

### Lists
- Use `-` for unordered lists
- Use `1.` for ordered lists
- Maintain consistent indentation (2 spaces)
- Use parallel structure in list items

### Code Blocks
- Always specify language for syntax highlighting
- Use descriptive comments
- Include expected output where relevant

```python
# Example API call
response = api.get_system_status("ECO-001-ZA")
print(response.json())
# Expected output: {"status": "operational", "flow_rate": 125.5}
```

### Tables
- Use consistent column alignment
- Include units in headers where applicable
- Use `|---|` for left alignment, `|---:|` for right alignment

| Parameter | Value | Unit |
|-----------|------:|------|
| Flow Rate | 125.5 | L/min |
| Efficiency | 97.2 | % |

### Emphasis
- **Bold**: For important terms, UI elements, and emphasis
- *Italic*: For technical terms on first mention, file names
- `Code`: For code snippets, file paths, and technical values

### Links
- Use descriptive link text (not "click here")
- Internal links: `[Link Text](relative/path.md)`
- External links: `[Link Text](https://example.com)`

## Content Guidelines

### Writing Style
- Use active voice
- Write in present tense
- Use clear, concise language
- Avoid jargon without explanation
- Include examples and practical applications

### Technical Specifications
- Always include units
- Use metric system (SI units)
- Provide ranges where applicable
- Include tolerance values

### Code Examples
- Provide complete, working examples
- Include error handling
- Add comments explaining complex logic
- Show expected responses

### Images and Diagrams
- Use descriptive alt text
- Include captions with figure numbers
- Reference figures in text
- Use consistent styling and colors

## File Naming Conventions

### Documentation Files
- Use lowercase with hyphens: `installation-guide.md`
- Be descriptive but concise
- Group related files in directories

### Directory Structure
```
docs/
├── index.md
├── getting-started/
├── products/
│   └── wastewater/
├── operations/
├── marketing/
├── suppliers/
├── api/
├── support/
└── about/
```

## Quality Checklist

Before publishing documentation, verify:

- [ ] Header follows standard format
- [ ] Terminology is consistent
- [ ] Links work correctly
- [ ] Code examples are tested
- [ ] Grammar and spelling are correct
- [ ] Images have alt text
- [ ] Tables are properly formatted
- [ ] Cross-references are accurate

## Review Process

1. **Self-Review**: Author checks against style guide
2. **Technical Review**: Subject matter expert validates content
3. **Editorial Review**: Check for style and consistency
4. **Final Approval**: Merge after all reviews complete

## Tools and Resources

### Markdown Linting
- Use markdownlint for consistency
- Configure rules in `.markdownlint.json`

### Spell Checking
- Use spell checker with technical dictionary
- Maintain project-specific word list

### Link Validation
- Regularly check for broken links
- Use automated link checking in CI/CD

---

*This style guide is a living document. Updates should be reviewed and approved by the documentation team.*