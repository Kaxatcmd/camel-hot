# 🐪 CAMEL-HOT Logo Setup Guide

## How to Add the New Logo to Your Application

The GUI has been updated to support the stunning desert sunset CAMEL-HOT logo. Here's how to set it up:

### Option 1: Automatic Image Detection (Recommended)

The application automatically looks for logo images in the following order:

1. `assets/camel_mascot.png` (PNG format - **preferred**)
2. `assets/camel_mascot.jpg` (JPEG format)
3. `assets/camel_mascot.jpeg` (JPEG format)
4. `assets/camel_mascot.svg` (SVG format - legacy)

### Option 2: Save the Logo Image

1. **Save the image** you uploaded to your computer
2. **Choose your format:**
   - PNG (recommended) - Best quality, transparent background support
   - JPEG - Good for photographs
   - SVG - Scalable vector graphics

3. **Place the file** in the `assets/` folder with one of these names:
   - `camel_mascot.png`
   - `camel_mascot.jpg`
   - `camel_mascot.jpeg`

4. **Restart the application** - it will automatically detect and load the logo

### Directory Structure

```
/home/elgz/Desktop/Vibe_coding_spot/App_projeto/
├── assets/
│   ├── camel_mascot.png        ← PUT YOUR LOGO HERE
│   └── camel_mascot.svg        (old SVG, optional)
├── gui/
│   └── main_window.py
├── main.py
└── ...
```

---

## Visual Improvements Implemented ✨

### 1. **Desert Sunset Background**
- Stunning gradient background matching the CAMEL-HOT logo
- Colors flow from deep green 🟢 → golden yellow 🟡 → vibrant orange 🟠 → warm red 🔴
- Creates an immersive, professional atmosphere

### 2. **Enhanced Title Styling**
- Bold, modern font matching the logo design
- "CAMEL-HOT" in the signature camel silhouette style
- Subtitle: "Harmonic Music Analyzer" in orange
- New tagline: "Mix by Harmony, Not by Chance" in green

### 3. **Updated Color Scheme**
| Element | Color | Hex | Purpose |
|---------|-------|-----|---------|
| Primary Green | Deep Desert Green | `#1a4d2e` | Logo base |
| Accent Yellow | Golden Hour | `#f4d03f` | Highlights |
| Accent Orange | Sunset Orange | `#ff9500` | Interactive elements |
| Accent Red | Deep Red | `#c1440e` | Emphasis |

### 4. **UI Component Updates**
- **Logo Container:** Enhanced with white background, golden border, and subtle shadow
- **Input Fields:** Golden borders (`#e8d841`) with orange focus states
- **Buttons:** Gradient effects matching desert sunset theme
- **Checkboxes & Radio Buttons:** Animated gradient selections
- **Separator Line:** Beautiful gradient of all desert sunset colors
- **Tab Widget:** Golden borders and smooth transitions

---

## Color Palette Reference

Use these colors if you need to create additional assets or customize further:

```
🟢 Deep Green:    #1a4d2e (left side of sunset)
🟢 Medium Green:  #3d6e40 (transition)
🟡 Golden Yellow: #f4d03f (midpoint)
🟠 Bright Orange: #ff9500 (right side)
🔴 Sunset Red:    #f07c1e (horizon)
🔴 Deep Red:      #c1440e (far right)
```

---

## Testing the New Look

After placing the logo image:

```bash
cd /home/elgz/Desktop/Vibe_coding_spot/App_projeto
source venv/bin/activate
python main.py
```

You should see:
1. ✅ Beautiful desert sunset gradient background
2. ✅ Your CAMEL-HOT logo displayed prominently
3. ✅ Enhanced title with matching branding
4. ✅ Golden/orange accents throughout the UI
5. ✅ Smooth transitions and professional appearance

---

## Supported Image Formats

| Format | Extension | Quality | Transparency |
|--------|-----------|---------|--------------|
| PNG | `.png` | Excellent | ✅ Yes |
| JPEG | `.jpg` / `.jpeg` | Good | ❌ No |
| SVG | `.svg` | Perfect | ✅ Yes |

**Recommendation:** Use **PNG** format for best results with the transparent background support.

---

## If Logo Is Not Loading

If the logo doesn't appear:

1. **Check file exists:** Verify the file is in `/assets/` folder
2. **Check filename:** Must be exactly `camel_mascot.png` (or `.jpg`/`.jpeg`/`.svg`)
3. **Check format:** File must be a valid image (not corrupted)
4. **Check path:** Make sure you're in the correct project directory

If all else fails, the app will display a placeholder camel emoji 🐪 and continue working normally!

---

## Logo Display Details

- **Logo Size:** 100x100 pixels (automatically scaled)
- **Container:** 110x110 pixels with 10px padding
- **Border:** 3px solid golden (`#e8d841`)
- **Border Radius:** 12px (rounded corners)
- **Shadow:** Subtle drop shadow for depth
- **Background:** Translucent white (95% opacity)

---

## Additional Notes

- The gradient background is applied to the entire window
- All text labels have transparent backgrounds to show the gradient
- Input fields and buttons have semi-transparent backgrounds for contrast
- The separator line (under the header) displays the full sunset gradient
- Tab containers have white backgrounds for readability

---

**Status:** ✅ GUI fully updated and ready for logo image  
**Version:** 2.2.0 (Visual Redesign)  
**Date:** February 2026

---

Need help? Check that your image file is properly saved and restart the application!
