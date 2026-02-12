# 🎧 DJ Harmonic Analyzer

A **human-friendly** Python tool that analyzes your music collection, detects musical keys and BPM, and helps you organize your library for **harmonic mixing** like professional DJs!

## ✨ **NEW: Beautiful Desert Sunset UI**

The application now features a stunning visual redesign inspired by the iconic **CAMEL-HOT** desert sunset logo! 

**Visual Features:**
- 🌅 Desert sunset gradient background (green → yellow → orange → red)
- 🐪 Enhanced CAMEL-HOT branding with professional typography
- 🎨 Golden accents and smooth transitions throughout
- 📱 Professional PyQt5 interface with modern styling

## 🎯 What Does This Do?

Imagine you have 1000+ songs and want to mix them smoothly. This tool helps you by:

1. **🔍 Analyzing** each song to find its musical key (e.g., "C Major", "A Minor")
2. **🎼 Converting** to Camelot notation (e.g., "8B", "8A") - the DJ standard
3. **📁 Organizing** your music into folders by key (all "8A" songs together!)
4. **📝 Creating** playlists of songs that sound good when mixed together

## 🚀 Quick Start

```bash
# 1️⃣ Install dependencies
pip install -r requirements.txt

# 2️⃣ Analyze a single song
python main.py analyze my_song.mp3

# 3️⃣ Organize your entire music folder
python main.py organize --input /path/to/music --output /organized

# 4️⃣ Create a harmonic playlist
python main.py playlist --input /music --output my_mix.m3u --key 8A --bpm 120 130
```

## 📖 Understanding the Camelot System

The Camelot wheel is like a clock for musical keys:

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

- **Numbers 1-12**: The 12 musical notes (like hours on a clock)
- **A**: Minor key (darker, sadder sound)
- **B**: Major key (brighter, happier sound)

**Compatible keys are next to each other!** "8A" mixes with "7A", "8A", "9A", and "8B".

## 💻 Command Reference

| Command | What It Does |
|---------|--------------|
| `analyze <file>` | Get key, BPM, and duration of a song |
| `organize --input <dir> --output <dir>` | Sort all songs into key folders |
| `playlist --input <dir> --output <file>` | Create harmonic mixing playlist |
| `find <directory>` | List all audio files found |
| `compatible <key>` | Show keys that work well together |



## ⚠️ Notes

- **Librosa required**: Install with `pip install librosa`
- **First 30 seconds**: Analysis uses the beginning of songs (usually where the key is clearest)
- **Accuracy**: Real-world key detection is complex - this is a simplified version!

## 🎓 Learn More

- **Camelot System**: [Wikipedia - Open Key Notation](https://en.wikipedia.org/wiki/Open_Key_Notation)
- **Harmonic Mixing**: [Beatmatch.info](https://www.beatmatch.info/harmonic-mixing)
- **Librosa**: [librosa.org](https://librosa.org/)

---

Made with ❤️ for DJs and music lovers!

