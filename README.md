# 🎧 DJ Harmonic Analyzer

A professional Python application that analyzes your music collection, detects musical keys and BPM, and organizes your library for harmonic mixing—the way professional DJs do it.

**Status:** ✅ Full-featured GUI application • Cross-platform • Python 3.7+

---

## 🎯 What It Does

Imagine you have 1000+ songs and want to mix them smoothly without jarring key changes. This tool helps by:

1. **🔍 Analyzing** each song to detect its musical key (e.g., "C Major", "A Minor")
2. **🎼 Converting** to Camelot notation (e.g., "8B", "8A")—the DJ standard
3. **📁 Organizing** your music into folders by key (all "8A" songs together!)
4. **📝 Creating** playlists of songs that sound great when mixed together

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.7+** ([download](https://www.python.org/downloads/))
- **pip** (usually included with Python)

### Installation & Running

#### **Windows Users:**
```bash
# 1. Clone or download the project
cd path\to\App_projeto

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

#### **Mac & Linux Users:**
```bash
# 1. Clone or download the project
cd path/to/App_projeto

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

#### **Quick Start with Script (Mac/Linux):**
```bash
cd path/to/App_projeto
./run.sh  # Automatically sets up venv, installs deps, runs tests, and launches app
```

---

## 🎨 Features & How to Use

A beautiful PyQt5-based interface with 5 tabs:

### 1️⃣ **Analyze Tab** 🔍
Detect the key, BPM, and duration of a single song.

**Steps:**
1. Click "Browse" to select an audio file (MP3, WAV, FLAC, OGG, M4A, AIFF)
2. Click "🎵 Analyze Music"
3. View results: Key, Camelot code, BPM, duration, and confidence score

### 2️⃣ **Organize Tab** 📂
Sort your entire music library into folders by key.

**Steps:**
1. Select input folder (your music library)
2. Select output folder (where organized music goes)
3. Choose: Copy (safe) or Move (deletes originals)
4. Click "⚙️ Organize Library"
5. Result: Organized folders like `8A/`, `8B/`, `2A/`, etc.

### 3️⃣ **Playlist Tab** 📝
Create harmonic playlists (M3U format) for your DJ software.

**Steps:**
1. Select folder with analyzed songs
2. Enter playlist filename (e.g., `my_mix.m3u`)
3. **(Optional)** Set filters:
   - **Camelot Key:** Filter by key (or "Any")
   - **BPM Range:** Filter by tempo (e.g., 120–130)
   - **Limit:** Max number of songs
4. Click "📝 Create Playlist"
5. Open the M3U file in your DJ software (Serato, Virtual DJ, Traktor, etc.)

### 4️⃣ **Compatibility Tab** ✅
Learn which keys mix well together.

**Steps:**
1. Select a Camelot key from the dropdown
2. Click "🔍 View Compatibility"
3. See all compatible keys highlighted

### 5️⃣ **About Tab** ℹ️
Application info, supported formats, and quick guide.

---

## 🎼 The Camelot System (Music Key Reference)

The Camelot wheel is like a musical clock for DJs:

```
        12B    1B    2B
     11B    ════    3B
   10B   A Minor  ════   4B
     9B   (12A)   5B
        8B    7B    6B

         8A    7A    6A
       9A   (12B)   5A
     10A  E Major  ════   4A
       11A  (7B)   3A
         12A   1A    2A
```

**Key Concepts:**
- **Numbers 1–12**: The 12 musical notes (like a clock)
- **A**: Minor key (dark, sad sound)
- **B**: Major key (bright, happy sound)

**Compatibility Rules:**
- Same key or relative major/minor (e.g., 8A + 8B) = Perfect
- Adjacent keys (e.g., 8A + 9A) = Great transition
- Opposite side of wheel = Jarring (avoid)

**Example with 8A:**
- ✅ 8A (same)
- ✅ 8B (relative major)
- ✅ 7A, 9A (adjacent minor)
- ✅ 7B, 9B (adjacent major)
- ❌ 1B, 4A, 5B (incompatible)

---

## 📁 Project Structure

```
App_projeto/
├── main.py                    # Entry point (launches GUI)
├── requirements.txt           # Python dependencies
├── README.md                  # You are here
├── run.sh                     # Quick start script (Mac/Linux)
│
├── gui/
│   ├── __init__.py
│   └── main_window.py         # PyQt5 GUI implementation
│
├── audio_analysis/
│   ├── __init__.py
│   └── key_detection.py       # Audio analysis (detect key, BPM)
│
├── file_manager/
│   ├── __init__.py
│   └── organizaer.py          # File operations (organize, playlists)
│
├── utils/
│   ├── __init__.py
│   └── camelot_map.py         # Camelot wheel mapping & helpers
│
├── assets/
│   └── camel_mascot.png       # (Optional) Application logo
│
├── input_audio/               # Put your audio files here to analyze
└── output_audio/              # Organized files go here
    ├── 1A/, 1B/, 2A/, ...     # Folders by key
```

---

## 🔧 System Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.7+ |
| pip | Any recent version |
| OS | Windows, macOS, Linux |
| RAM | 2GB+ recommended |
| Storage | ~500MB for dependencies |

---

## 📦 Dependencies

The following Python packages are automatically installed via `requirements.txt`:

- **librosa** (≥0.10.0) — Audio analysis and key detection
- **PyQt5** (≥5.15.0) — Professional GUI framework

All other dependencies (NumPy, SciPy, etc.) are installed automatically.

---

## 🎵 Supported Audio Formats

✅ MP3  
✅ WAV  
✅ FLAC  
✅ OGG  
✅ M4A  
✅ AIFF  

*Other formats may work depending on your system's audio codecs.*

---

## 🆘 Troubleshooting

### **Problem: "No module named PyQt5" or "No module named librosa"**
**Solution:** Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### **Problem: Application won't start**
**Solution:** Verify Python version and dependencies:
```bash
python --version          # Should be 3.7+
pip list | grep PyQt5     # Should show PyQt5
pip list | grep librosa   # Should show librosa
```

### **Problem: Audio file analysis fails**
**Solution:** 
- Verify the file is a supported format (MP3, WAV, FLAC, etc.)
- Check file isn't corrupted (try another file)
- Ensure file path doesn't have special characters

### **Problem: Organizing takes a very long time**
**Solution:** This is normal! Audio analysis is CPU-intensive. With 1000+ files, expect 30–60 minutes. You can:
- Analyze a subset first to test
- Run overnight for large libraries
- Close other applications to free up CPU

### **Problem: Detected key seems wrong**
**Solution:** Key detection isn't perfect—it's more accurate for:
- Clear vocal/instrumental tracks
- Songs with steady harmony
- Higher quality audio
You can re-organize manually or ignore incorrect results.

### **Problem: (Mac) "PyQt5 not available"**
**Solution:** If you have both Python 2 and 3, explicitly use Python 3:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## 👨‍💻 For Developers

### Setting Up a Development Environment

```bash
# Clone/navigate to the project
cd App_projeto
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_gui.py
python test_setup.py

# Make changes and test
python main.py
```

### Key Modules

**`audio_analysis/key_detection.py`**
- `analyze_track(file_path)` — Analyzes a single file, returns: `{file_path, key, camelot, bpm, duration, confidence}`
- `detect_key_from_audio(y, sr)` — Low-level analysis function

**`file_manager/organizaer.py`**
- `find_audio_files(directory)` — Recursively finds audio files
- `organize_by_key(input_dir, output_dir, move_files=False)` — Organizes library
- `create_playlist(input_dir, output_file, key=None, bpm_min=None, bpm_max=None, limit=None)` — Creates M3U playlist

**`utils/camelot_map.py`**
- `CAMELOT_MAP` — Dictionary of all Camelot codes and their properties
- `is_compatible_keys(key1, key2)` — Checks if two keys mix well
- `get_compatible_keys(key)` — Returns all compatible keys for a given key

### Running Tests

```bash
# Test GUI components and imports
python test_gui.py

# Test analysis and core functions
python test_setup.py
```

Expected output: **3/3 tests pass** ✅

### Adding New Features

1. Update the relevant module (`audio_analysis/`, `file_manager/`, `utils/`)
2. Update GUI in `gui/main_window.py` if it's user-facing
3. Add tests to `test_gui.py` or `test_setup.py`
4. Update this README if it affects users

---

## 🎓 Learn More About Harmonic Mixing

- **Camelot System**: [Wikipedia - Open Key Notation](https://en.wikipedia.org/wiki/Open_Key_Notation)
- **Why It Works**: [Beatmatch.info - Harmonic Mixing](https://www.beatmatch.info/harmonic-mixing)
- **Audio Analysis**: [Librosa Documentation](https://librosa.org/)

---

## 📋 Version History

**v2.0** (Current)
- Full PyQt5 GUI interface
- 5-tab design
- Cross-platform support
- Professional styling

**v1.0**
- Original CLI interface
- Core analysis functionality

See `CHANGELOG.md` for detailed history.

---

## 📝 License & Credits

Made with ❤️ for DJs, music producers, and anyone who loves harmonic mixing.

**Special Thanks:**
- **librosa** team for excellent audio analysis
- **PyQt5** community for robust GUI framework
- All testers and contributors

---

## 📞 Support & Feedback

If you encounter issues:
1. Check the **Troubleshooting** section above
2. Verify all dependencies: `pip install -r requirements.txt`
3. Run tests: `python test_gui.py`
4. Check file paths don't have special characters

---

**Last Updated:** February 2026  
**Current Version:** 2.0  
**Python:** 3.7+  
**Status:** ✅ Production Ready

