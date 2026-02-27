---
name: auto_pptx
description: "Automatically create professional PowerPoint presentations from markdown or text content. Use this skill whenever the user asks to create slides, PPTX files, presentations, or convert documents to PowerPoint format."
---

# Auto PPTX - Professional Presentation Generator

## Overview

This skill creates professional PowerPoint presentations from markdown documents or text content. It uses `pptxgenjs` to generate PPTX files with clean, readable designs and proper layout.

## When to Use

- User requests to create a PPTX/presentation from content
- User wants to convert markdown/docs to slides
- User asks for "slides", "PowerPoint", "presentation", or "PPTX"
- User needs visual summaries of documents

## Quick Start

```bash
# 1. Install dependency (if not already installed)
npm install pptxgenjs

# 2. Create presentation script and run
node create_presentation.js
```

## Step-by-Step Workflow

### Step 1: Analyze Source Content

Read the source document and identify:
- Main title and subtitle
- Section/chapter divisions
- Key points for each section
- Tables, lists, and data to visualize
- Natural slide breaks

### Step 2: Plan Slide Structure

Create a slide outline:
1. **Title Slide** - Main title + subtitle
2. **Table of Contents** - All sections
3. **Section Dividers** - For each major section
4. **Content Slides** - Key information with visuals
5. **Summary** - Key takeaways
6. **Closing** - Thank you / Q&A

### Step 3: Create Presentation Script

Use this template structure:

```javascript
const pptxgen = require("pptxgenjs");

let pres = new pptxgen();

// Light theme colors (high contrast, readable)
const COLORS = {
  bgMain: "F8F9FA",        // Light gray background
  bgContent: "FFFFFF",     // White content boxes
  textMain: "212121",      // Almost black text
  textSecondary: "424242", // Dark gray
  primary: "1976D2",       // Blue primary
  chart1: "1976D2",        // Blue
  chart2: "7B1FA2",        // Purple
  chart3: "00796B",        // Teal
  chart4: "D32F2F",        // Red
  chart5: "F57C00"         // Orange
};

const FONTS = {
  header: "Arial Black",
  body: "Calibri"
};

// Set layout
pres.layout = 'LAYOUT_16x9';

// Background function
function addBackground(slide) {
  slide.background = { color: COLORS.bgMain };
}

// Title slide
function addTitleSlide(pres, title, subtitle) {
  let slide = pres.addSlide();
  slide.background = { color: COLORS.bgMain };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 1.5, y: 1.5, w: 7, h: 2.5,
    fill: { color: COLORS.bgContent },
    line: { color: COLORS.primary, width: 2 },
    rectRadius: 0.1
  });
  
  slide.addText(title, {
    x: 1.7, y: 1.8, w: 6.6, h: 1.2,
    fontSize: 36, fontFace: FONTS.header,
    color: COLORS.primary, bold: true, align: "center"
  });
  
  slide.addText(subtitle, {
    x: 1.7, y: 2.9, w: 6.6, h: 0.6,
    fontSize: 18, fontFace: FONTS.body,
    color: COLORS.textSecondary, align: "center"
  });
  
  return slide;
}

// Section slide
function addSectionSlide(pres, num, title, icon) {
  let slide = pres.addSlide();
  addBackground(slide);
  
  slide.addText(num, {
    x: 0.5, y: 1, w: 2, h: 1.5,
    fontSize: 80, fontFace: FONTS.header,
    color: "BDBDBD", bold: true
  });
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.5, w: 0.15, h: 1.2,
    fill: { color: COLORS.primary }
  });
  
  slide.addText(title, {
    x: 1, y: 2.6, w: 6.5, h: 1,
    fontSize: 32, fontFace: FONTS.header,
    color: COLORS.textMain, bold: true
  });
  
  return slide;
}

// Content slide
function addContentSlide(pres, title) {
  let slide = pres.addSlide();
  addBackground(slide);
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 0.35, w: 0.12, h: 0.4,
    fill: { color: COLORS.primary }
  });
  
  slide.addText(title, {
    x: 0.85, y: 0.35, w: 8.5, h: 0.4,
    fontSize: 24, fontFace: FONTS.header,
    color: COLORS.textMain, bold: true
  });
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 0.9, w: 8.8, h: 4.3,
    fill: { color: COLORS.bgContent },
    line: { color: COLORS.primary, width: 1.5, transparency: 60 },
    rectRadius: 0.1
  });
  
  return slide;
}

// ============================================
// CREATE YOUR SLIDES HERE
// ============================================

// Slide 1: Title
addTitleSlide(pres, "Your Title", "Your Subtitle");

// Slide 2: TOC
let toc = addContentSlide(pres, "目录");

// ... add more slides ...

// ============================================
// SAVE
// ============================================

pres.writeFile({ fileName: "Your_Presentation.pptx" })
  .then(() => console.log("✓ Presentation saved!"))
  .catch(err => console.error("✗ Error:", err));
```

### Step 4: Design Principles

#### Color Scheme (Light Theme)

**Backgrounds:**
- Main: `F8F9FA` (light gray, easy on eyes)
- Content: `FFFFFF` (pure white, clean)
- Accent: `E3F2FD` (very light blue)

**Text:**
- Main: `212121` (almost black, maximum readability)
- Secondary: `424242` (dark gray, hierarchy)
- Muted: `757575` (medium gray, subtle)

**Colors:**
- Primary: `1976D2` (professional blue)
- Charts: Blue, Purple, Teal, Red, Orange

#### Layout Rules

**Safe Margins (CRITICAL):**
- Horizontal: 0.6" to 9.4" (content within 9.4" width)
- Vertical: 0.4" to 5.2" (content within 4.8" height)
- Slide size: 10" × 5.625" (16:9)

**Font Sizes:**
- Title slide: 36pt (title), 18pt (subtitle)
- Section titles: 32pt
- Content titles: 24pt
- Body text: 14-16pt
- Small text: >= 10pt (NEVER smaller)

**Content Boxes:**
- Width: 8.8" max
- Height: 4.3" max
- Padding: 0.2" minimum
- Border: 1.5pt with 60% transparency

#### Visual Elements

**Tables:**
- Use for comparisons, lists, data
- Alternating row colors
- Header row with bold white text on colored background
- Border: 1pt gray

**Shapes:**
- Rectangles for content boxes
- Rounded corners (rectRadius: 0.08-0.1)
- Shadows for depth (optional)
- Transparency: 85-90% for colored boxes

**Icons:**
- Use emoji for visual interest
- Size: 24-28pt
- Place in circles or next to titles

### Step 5: Quality Assurance

#### Automated Check

Create a verification script:

```python
from pptx import Presentation
import os

pptx_path = "Your_Presentation.pptx"
prs = Presentation(pptx_path)

print(f"Slides: {len(prs.slides)}")

# Check for layout issues
issues = 0
for i, slide in enumerate(prs.slides, 1):
    for shape in slide.shapes:
        if hasattr(shape, 'left'):
            right = shape.left.inches + shape.width.inches
            bottom = shape.top.inches + shape.height.inches
            if right > 9.6 or bottom > 5.25:
                issues += 1
                print(f"Slide {i}: Overflow at ({right:.2f}, {bottom:.2f})")

if issues == 0:
    print("✓ All content within safe margins!")
else:
    print(f"✗ Found {issues} layout issues")
```

#### Manual Checklist

- [ ] All text is readable (>= 10pt)
- [ ] No text overflow (right < 9.6", bottom < 5.25")
- [ ] Consistent color scheme
- [ ] High contrast (dark text on light background)
- [ ] Section dividers between major sections
- [ ] Title and closing slides included
- [ ] File size reasonable (< 5MB)

### Step 6: Common Patterns

#### Table of Contents

```javascript
const tocItems = [
  { num: "01", title: "First Section", color: COLORS.chart1 },
  { num: "02", title: "Second Section", color: COLORS.chart2 },
  { num: "03", title: "Third Section", color: COLORS.chart3 }
];

tocItems.forEach((item, i) => {
  const y = 1.2 + i * 0.8;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.9, y: y, w: 8.2, h: 0.6,
    fill: { color: item.color, transparency: 90 },
    line: { color: item.color, width: 1.5 }
  });
  slide.addText(item.num, {
    x: 1.1, y: y, w: 0.6, h: 0.6,
    fontSize: 20, bold: true, color: item.color, align: "center"
  });
  slide.addText(item.title, {
    x: 1.8, y: y, w: 7, h: 0.6,
    fontSize: 18, color: COLORS.textMain, align: "left"
  });
});
```

#### Two-Column Comparison

```javascript
let slide = addTwoColumn(pres, "Comparison Title", COLORS.success, COLORS.error);

// Left column (green)
slide.addText("✅ Advantages", {
  x: 0.85, y: 1.15, w: 3.7, h: 0.35,
  fontSize: 15, bold: true, color: COLORS.success
});

// Right column (red)
slide.addText("❌ Disadvantages", {
  x: 5.45, y: 1.15, w: 3.7, h: 0.35,
  fontSize: 15, bold: true, color: COLORS.error
});
```

#### Grid Layout (3+2 for 5 items)

```javascript
const positions = [{c:0,r:0}, {c:1,r:0}, {c:2,r:0}, {c:0,r:1}, {c:1,r:1}];

items.forEach((item, i) => {
  const pos = positions[i];
  const x = 0.85 + pos.c * 2.85;
  const y = 1.15 + pos.r * 1.6;
  
  // Add card at (x, y)
});
```

### Step 7: Dependencies

**Required:**
```bash
npm install pptxgenjs
```

**Optional (for verification):**
```bash
pip install python-pptx
```

### Step 8: File Organization

```
project/
├── .cursor/
│   └── rules/
│       └── auto_pptx/
│           └── SKILL.md
├── create_presentation.js    # Generation script
├── verify_presentation.py    # Verification script
└── output.pptx               # Generated presentation
```

## Examples

### Example 1: Simple Document to PPTX

**Input:** `document.md` with 3 sections

**Output:** 8-slide presentation
1. Title
2. Table of Contents
3. Section 1 divider
4. Section 1 content
5. Section 2 divider
6. Section 2 content
7. Section 3 divider
8. Section 3 content + Summary

### Example 2: Technical Report

**Input:** Technical report with data

**Output:** 
- Title slide
- Executive summary
- Data visualization slides (charts/tables)
- Methodology
- Results
- Conclusion

## Troubleshooting

### Text Overflow

**Problem:** Text extends beyond slide edge

**Solution:**
- Reduce font size
- Shorten text content
- Split into multiple slides
- Use text wrapping (add `\n`)

### Low Contrast

**Problem:** Hard to read text

**Solution:**
- Use darker text colors
- Use lighter background
- Increase font size
- Add white background box behind text

### File Too Large

**Problem:** PPTX > 5MB

**Solution:**
- Reduce image sizes
- Use fewer high-transparency shapes
- Simplify complex diagrams
- Remove unused slides

## Best Practices

1. **Always use light background + dark text** for maximum readability
2. **Keep fonts >= 10pt** - smaller is unreadable
3. **Use safe margins** - 0.6" to 9.4" horizontal, 0.4" to 5.2" vertical
4. **Limit colors** - 5 chart colors max, consistent palette
5. **One idea per slide** - don't overcrowd
6. **Use visuals** - icons, charts, tables break up text
7. **Consistent spacing** - use grid system
8. **Test before delivery** - always run verification script

## Testing

After creating a presentation, ALWAYS run verification:

```bash
# Generate
node create_presentation.js

# Verify
python verify_presentation.py

# Check output
# ✓ Should show: "All content within safe margins!"
# ✓ Should show: Slide count matches expected
```

## License

This skill is part of the Cursor rules system.
