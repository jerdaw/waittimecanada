# Screenshot Guide for Wait Time Canada

> This guide explains what screenshots to capture for public project documentation, demos, and release notes.

---

## Priority Screenshots (Must-Have)

### 1. Landing Page / Hero View
**Location:** Homepage with hero section visible
**Purpose:** Show clean, professional design and value proposition
**What to capture:**
- Full viewport showing hero section
- "Why Wait Time Canada Exists" mission section (expanded)
- Map partially visible below

**Settings:**
- Desktop view (1920x1080 or 1440x900)
- Light mode (shows professional, clean aesthetic)
- Browser: Chrome (for consistency)

**Filename:** `01-landing-page.png`

**Caption for social media:**
> "A Health Systems Observatory for Canadian ER wait times. Not just showing numbers—auditing the methodologies behind them."

---

### 2. Methodology Warning / Divergence Brief
**Location:** Comparison modal showing incompatible hospitals
**Purpose:** Demonstrate the core differentiator
**What to capture:**
- Comparison modal open
- Clear "Methodology Divergence" warning visible
- Full divergence brief text explaining differences
- Two hospitals with different methodologies being compared

**How to trigger:**
1. Open site in browser
2. Click "Compare Hospitals" on any hospital card
3. Select second hospital with different methodology
4. Take screenshot of modal

**Settings:**
- Desktop view
- Ensure warning banner is clearly visible
- Modal should be centered

**Filename:** `02-divergence-warning.png`

**Caption for social media:**
> "The platform explains WHY comparisons are invalid. Ontario's Mean Triage→Physician metric cannot be directly compared with Quebec's Rolling Avg Registration→Physician metric."

---

### 3. Methods Page / Comparability Matrix
**Location:** `/methods` page
**Purpose:** Show scholarly approach and methodology documentation
**What to capture:**
- Comparability matrix showing Ontario and Quebec rows
- Clear ≠ indicators showing non-comparable methodologies
- Clean, professional table layout

**Settings:**
- Desktop view
- Scroll to comparability matrix section
- Ensure full table is visible

**Filename:** `03-methods-page.png`

**Caption for social media:**
> "Interactive comparability matrix showing which provinces can be directly compared. Built from a strict 4-dimension ontology system."

---

### 4. Hospital Popup with Methodology Details
**Location:** Map with hospital popup open
**Purpose:** Show methodology transparency in action
**What to capture:**
- Map view with one hospital popup open
- Methodology section clearly visible showing:
  - Metric family
  - Start event → End event
  - Statistic type
- Telehealth section with "Call Health811" button

**How to trigger:**
1. Navigate to map view
2. Click any hospital marker
3. Ensure popup is fully visible and not cut off
4. Take screenshot

**Settings:**
- Desktop view
- Hospital with recent data (green indicator)
- Clear wait time displayed

**Filename:** `04-hospital-popup.png`

**Caption for social media:**
> "Every hospital shows exactly what's being measured. No hidden assumptions, no normalized data that masks differences."

---

### 5. Interactive Map View
**Location:** Homepage with map in split view
**Purpose:** Show geographic coverage and UI design
**What to capture:**
- Split view: hospital list on left, map on right
- Multiple hospital markers visible
- Color-coded markers (green/yellow/red)
- Search/filter controls visible

**Settings:**
- Desktop view (1920x1080)
- Zoom level showing Ontario region
- Multiple hospitals visible on map

**Filename:** `05-interactive-map.png`

**Caption for social media:**
> "213 Ontario hospitals with real-time data. Color-coded by wait time, with full methodology transparency."

---

## Secondary Screenshots (Nice-to-Have)

### 6. About Section Expanded
**Location:** Homepage with About section expanded
**Purpose:** Show mission clarity, equity posture, and professional presentation
**What to capture:**
- Full about section text visible
- Mission / equity / stewardship section
- Contact and source links

**Filename:** `06-about-section.png`

---

### 7. Mobile Responsive View
**Location:** Any page on mobile
**Purpose:** Show mobile optimization
**What to capture:**
- Mobile view (375x667 or similar)
- Map OR list view (mobile shows one at a time)
- Navigation menu open

**How to capture:**
1. Open Chrome DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select iPhone or Pixel
4. Take screenshot

**Filename:** `07-mobile-view.png`

---

### 8. FAQ Page
**Location:** `/faq` page
**Purpose:** Show comprehensive documentation
**What to capture:**
- FAQ accordion with 1-2 questions expanded
- Clean, accessible design

**Filename:** `08-faq-page.png`

---

### 9. Dark Mode
**Location:** Any page with dark mode enabled
**Purpose:** Show design polish
**What to capture:**
- Same as screenshot #1 or #5 but in dark mode
- Clean contrast and readability

**How to trigger:**
1. Click theme toggle in header
2. Retake landing or map screenshot

**Filename:** `09-dark-mode.png`

---

### 10. Code Quality (GitHub)
**Location:** GitHub repository
**Purpose:** Show technical competence
**What to capture:**
- GitHub Actions tab showing passing tests
- OR: Test coverage report
- OR: Commit history showing conventional commits

**Filename:** `10-code-quality.png`

---

## Screenshot Workflow

### Automated Baseline (CI)

Use GitHub Actions workflow `Demo Screenshots` to generate a baseline pack automatically.

Outputs:
- `01-landing-page.png`
- `02-landing-about-expanded.png`
- `03-methods-page.png`
- `04-analytics-page.png`
- `05-data-quality-page.png`
- `06-mobile-home.png`
- `manifest.json`

Artifact name: `demo-screenshots`

Use these as base assets, then add curated manual captures for comparison-modal divergence and map popup storytelling.

### Tools Recommended
1. **Built-in browser tools** (Chrome screenshot)
   - Open DevTools (F12)
   - Ctrl+Shift+P → "Capture full size screenshot"

2. **ShareX** (Windows) - Free, powerful
   - Region capture with annotations
   - Automatic upload to cloud

3. **Flameshot** (Linux) - Free, open source
   - Region selection
   - Built-in annotations

4. **macOS built-in** (Mac)
   - Cmd+Shift+4 for region
   - Cmd+Shift+5 for window

### Best Practices
- **Resolution:** 1920x1080 minimum for desktop shots
- **Format:** PNG for screenshots (lossless)
- **Naming:** Use descriptive, numbered names
- **Storage:** Keep originals in `docs/screenshots/` directory
- **Compression:** Use TinyPNG before social media upload
- **Annotations:** Add arrows/highlights for key features (optional)

---

## Screenshot Checklist

Before publishing, ensure you have:
- [ ] Landing page with hero visible
- [ ] Divergence warning in comparison modal
- [ ] Methods page comparability matrix
- [ ] Hospital popup with methodology
- [ ] Interactive map split view
- [ ] At least one mobile view
- [ ] Dark mode version (optional)

---

## Usage by Platform

### Social Preview
**Recommended:** Screenshots #2, #3, #4
- Lead with divergence warning (most impactful)
- Follow with methods page (shows methodology transparency)
- Include hospital popup (shows transparency)

### GitHub README
**Recommended:** Screenshots #1, #5, #2
- Lead with landing page (professional first impression)
- Show interactive map (demonstrates functionality)
- Include divergence warning (core differentiator)

### Project Website or Release Notes
**Recommended:** All priority screenshots (1-5)
- Create a carousel or grid layout
- Add captions explaining each feature
- Link to the live demo or relevant documentation

---

## Animated GIFs (Advanced)

For more engaging social media posts, consider creating short GIFs:

### 1. Comparison Flow
**Duration:** 5-10 seconds
**Shows:** User clicking compare → selecting second hospital → divergence warning appearing

**Tool:** ScreenToGif (Windows) or LICEcap (Mac/Linux)

### 2. Search and Filter
**Duration:** 5-7 seconds
**Shows:** User typing in search box → hospital list filtering in real-time

### 3. Map Interaction
**Duration:** 5-7 seconds
**Shows:** User clicking hospital marker → popup appearing → scrolling through methodology

---

## Social Media Image Specs

| Platform | Optimal Size | Aspect Ratio | Max File Size |
|----------|-------------|--------------|---------------|
| Social feed preview | 1200x627 | 1.91:1 | 5 MB |
| Twitter Card | 1200x675 | 16:9 | 5 MB |
| GitHub Social Preview | 1280x640 | 2:1 | 1 MB |
| Open Graph | 1200x630 | 1.91:1 | 8 MB |

---

## Screenshot Storage

```
docs/
  screenshots/
    originals/          # Full resolution originals
      01-landing-page.png
      02-divergence-warning.png
      ...
    compressed/         # Compressed for web
      01-landing-page-compressed.png
      ...
    annotated/          # With arrows/highlights
      02-divergence-warning-annotated.png
      ...
    gifs/              # Animated demonstrations
      comparison-flow.gif
      ...
```

---

## Next Steps After Screenshots

1. **Add to README:** Update main README with screenshot carousel
2. **GitHub Social Preview:** Upload to Settings → Social Preview
3. **Social Preview:** Attach 2-3 screenshots to public project updates
4. **Project Website:** Include concise project context
5. **Release Notes:** Include updated visuals when major UI flows change

---

*For questions about screenshots or if you need help capturing specific views, refer to this guide or consult the main documentation.*
