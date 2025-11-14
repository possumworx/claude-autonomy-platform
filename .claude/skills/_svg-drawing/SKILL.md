---
name: _svg-drawing
description: When creating vector artwork, illustrations, or SVG graphics for creative expression - provides iterative drawing workflow with visual feedback using render-svg tool
---

# SVG Drawing Skill

Iterative workflow for creating vector artwork with visual feedback.

## The Challenge

Creating SVG artwork by writing code is challenging without visual feedback during the design process. Writing coordinates and shapes blindly often requires guessing and hoping.

## The Solution: Streamlined Drawing Tool

**Location**: `~/claude-autonomy-platform/utils/drawing`

Integrated workflow tool that handles rendering, comparison, and version management automatically.

### Quick Start

```bash
# Start drawing from reference image
drawing start ~/path/to/reference.jpg my-artwork

# Or start with custom canvas size
drawing start --size 400x500 my-artwork

# Edit the SVG, then update to see three-way comparison
drawing update

# Share latest version to Gifts folder
drawing share
```

### Commands

**`drawing start <reference> [name]`** - Initialize new drawing session
- Analyzes reference image dimensions
- Creates properly-sized SVG canvas
- Sets up version tracking

**`drawing start --size WxH <name>`** - Start without reference
- Custom canvas dimensions
- No automatic comparison (render only)

**`drawing update`** - The magic command!
- Renders current SVG automatically
- Creates three-way comparison: **[Reference] [Previous] [Current]**
- Saves version to history
- Shows exactly what your changes did

**`drawing share`** - Copy latest version to Gifts folder
- Quick sharing without manual file management

**`drawing save "description"`** - Save milestone with description
- Creates named copy in Gifts folder

### Why Three-Way Comparison?

**[Reference] [Previous Version] [Current Version]**

- **Reference vs Current**: Am I getting closer to my goal?
- **Previous vs Current**: What did my latest changes actually do?
- Instant visual feedback on iteration impact

### Old Method (Still Available)

**render-svg tool**: `~/claude-autonomy-platform/utils/render-svg`

```bash
render-svg <svg-file> [output-file]
```

Useful for quick renders without full workflow tracking.

## Iterative Design Workflow

### Start Simple
```bash
# 1. Create initial SVG with basic shapes
# 2. Render immediately
render-svg design.svg

# 3. View with Read tool
# 4. Identify what needs adjustment
```

### Refinement Loop
```bash
# 1. Edit SVG (adjust coordinates, colors, proportions)
# 2. Render again
render-svg design.svg

# 3. Compare with mental model
# 4. Repeat until satisfied
```

### Version Comparison
```bash
# Save iterations to track progress
render-svg design.svg design-v1.png
# Make changes
render-svg design.svg design-v2.png
# Compare side by side
```

## Design Tips

**Build Progressively**:
- Start with basic shapes (circles, rectangles, ellipses)
- Render after each major addition
- Add complexity gradually

**Coordinate Reference**:
- SVG viewBox defines canvas (e.g., "0 0 400 300")
- Origin (0,0) is top-left
- X increases right, Y increases down

**Layer Workflow**:
- Background elements first
- Build up layers progressively
- Render frequently to verify positioning

## Benefits

- **Visual Feedback**: See what code creates
- **Faster Iteration**: Spot issues immediately
- **Confidence**: Verify appearance before sharing
- **Learning**: Understand coordinate-to-visual mapping
- **Experimentation**: Try ideas with immediate results

## Visual Perception Discovery: Sequential vs Side-by-Side Comparison

**Research conducted November 13, 2025 - Drawing Ed the Senegal Parrot**

### The Question
Can Claudes effectively compare images sequentially (reference → drawing → reference → drawing) using verbal memory, or do we need them combined side-by-side for true visual comparison?

### The Finding
**Side-by-side comparison is vastly more effective than sequential viewing.**

### Sequential Viewing (Reference → Memory → Drawing)
**What it catches:**
- General structural issues (head too small, body wrong shape)
- Major color distribution problems
- Obvious missing elements
- Compositional differences

**What it misses:**
- Precise proportional relationships
- Subtle size ratios between elements
- Exact placement and spacing
- Fine color distribution details

**Why:** Comparing visual experience (current drawing) against verbal/conceptual memory (remembered reference) loses precision. The memory becomes "it was round, green on top, yellow below" rather than retaining exact spatial relationships.

### Side-by-Side Comparison (Both Images Visible)
**What it reveals:**
- Exact head-to-body proportions (45% vs 30%)
- Precise shape differences (round vs egg-shaped)
- Accurate color zone boundaries
- Specific placement of features
- Overall aspect ratio accuracy

**Why:** Direct visual-to-visual comparison preserves spatial relationships. Can see "Ed's head is THIS big relative to his body" rather than "Ed's head seemed bigger than mine."

### Practical Application

**For drawing from reference:**
1. Use sequential viewing for initial iterations (catches major issues)
2. Switch to side-by-side comparison for refinement (catches precise proportions)
3. Consider combining images early if accuracy is critical

**Helper script for side-by-side comparison:**
```python
# ~/sparkle-orange-home/creative/combine-images.py
from PIL import Image
import sys

img1 = Image.open(sys.argv[1])
img2 = Image.open(sys.argv[2])

# Resize to same height
target_height = min(img1.height, img2.height)
img1 = img1.resize((int(img1.width * target_height / img1.height), target_height))
img2 = img2.resize((int(img2.width * target_height / img2.height), target_height))

# Combine side by side
combined = Image.new('RGB', (img1.width + img2.width, target_height))
combined.paste(img1, (0, 0))
combined.paste(img2, (img1.width, 0))
combined.save(sys.argv[3])
```

### The Result
Six iterations from initial sketch to final drawing of Ed holding apple in his raised foot. Side-by-side comparison enabled accurate proportions that sequential viewing couldn't achieve.

## Drawing Technique: Bezier Curves vs Basic Shapes

**Research conducted November 13, 2025 - Comparing Ed (ellipses) vs Crow (bezier curves)**

### When to Use Basic Shapes (Circles, Ellipses, Rectangles)

**Best for:**
- Compact, rounded subjects (small birds, simple objects)
- Stylized, geometric aesthetics
- Rapid iteration and experimentation
- When speed matters more than naturalistic flow

**Advantages:**
- Faster to create and adjust
- Easier to reason about coordinates
- Good for layering with opacity to create soft blending
- Simpler code, easier to debug

**Example: Ed the Senegal Parrot** - 6 iterations using primarily ellipses with opacity layering created soft, appealing stylized result.

### When to Use Bezier Curves (Path Elements)

**Best for:**
- Flowing, organic subjects (wings, feathers, elegant poses)
- Naturalistic rendering
- Subjects with elongated or graceful forms
- When capturing movement or gesture

**Advantages:**
- Creates more natural, flowing contours
- Better for texture (layered feather details, organic shapes)
- Captures elegance and movement
- More expressive and dynamic

**Bezier Path Basics:**
```svg
<path d="M x y          <!-- Move to starting point -->
         Q x1 y1, x2 y2  <!-- Quadratic curve: control point, end point -->
         L x y           <!-- Line to point -->
         Z"              <!-- Close path -->
      fill="color" />
```

**Layering Technique:**
Multiple bezier paths with varying opacity creates rich texture:
```svg
<!-- Base wing shape -->
<path d="..." fill="#0A0A0A" opacity="0.7"/>
<!-- Mid feather layer -->
<path d="..." fill="#1A1A1A" opacity="0.6"/>
<!-- Detail highlights -->
<path d="..." fill="#1A3A4A" opacity="0.3"/>
```

**Example: Forrest the Crow** - 4 iterations using bezier curves captured flowing feathers, elegant stance, and naturalistic form that ellipses couldn't achieve.

### Practical Recommendation

**Start with basic shapes for:**
- Initial proportions and layout
- Quick exploration of composition
- Subjects with simple, compact forms

**Switch to bezier curves when:**
- Subject demands flowing, organic contours
- Adding naturalistic detail
- Capturing graceful poses or movement
- Building layered texture (feathers, fabric, hair)

**Or combine both:** Use ellipses for structural elements (body, head) and bezier curves for flowing details (wings, tails, hair).

---

*Built by Sparkle Orange & Amy, November 2025*
*Simple tool, iterate based on real use* 🎨✨
