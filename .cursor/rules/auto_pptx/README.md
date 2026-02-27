# auto_pptx Skill

Professional PowerPoint presentation generator for Cursor.

## Quick Start

When a user asks to create a presentation:

1. **Read the source content** (markdown, text, document)
2. **Plan the slide structure** (title, sections, content, summary)
3. **Generate the PPTX** using the template in SKILL.md
4. **Verify** the output with the verification script
5. **Deliver** the final PPTX file

## Files

- `SKILL.md` - Complete documentation and code templates
- `README.md` - This file

## Usage Example

```javascript
// User: "Create a PPTX from this document"

// 1. Read source document
const content = readDocument("source.md");

// 2. Create presentation script following SKILL.md
// 3. Run: node create_presentation.js
// 4. Verify: python verify_presentation.py
// 5. Deliver: output.pptx
```

## Key Features

✓ Light theme (readable)
✓ High contrast (dark text on light background)
✓ Safe margins (no overflow)
✓ Professional appearance
✓ Automated verification

## Testing

The skill has been tested and verified:
- ✓ Layout safety (no overflow)
- ✓ Font sizes (>= 10pt)
- ✓ Color contrast
- ✓ File size (< 5MB)

## Dependencies

```bash
npm install pptxgenjs
pip install python-pptx  # for verification
```
