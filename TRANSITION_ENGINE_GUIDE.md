# Transition Scoring Engine - Implementation Guide

## 🎯 Overview

The Transition Scoring Engine is a comprehensive system for intelligent DJ track analysis and compatibility evaluation. It extends the basic harmonic analysis with advanced features for smooth transitions.

## ✨ Key Features

### 1. 🥇 Energy Level Detection (`audio_analysis/energy_detection.py`)

Analyzes the dynamic character of tracks:

- **Spectral Brightness**: How bright/dark the sound is (0-1)
  - Bright: Cymbal crashes, bright synths (> 0.65)
  - Neutral: Balanced frequency content (0.35-0.65)
  - Dark: Basses, sub-bass heavy (< 0.35)

- **Loudness/Intensity**: RMS energy level
  - High: Loud, aggressive tracks
  - Medium: Standard production
  - Low: Quiet, intimate tracks

- **Energy Dynamics**: How energy evolves
  - Ascending: Build-ups, crescendos
  - Descending: Breakdowns, fade-outs
  - Stable: Consistent energy throughout

- **Spectral Richness**: Complexity of harmonic content
  - Dense: Lots of simultaneous sounds
  - Medium: Balanced instrumentation
  - Minimal: Sparse, simple arrangements

**Usage:**
```python
from audio_analysis.energy_detection import classify_energy_level
import librosa

y, sr = librosa.load("track.mp3")
energy = classify_energy_level(y, sr)
# {
#   "level": "High",
#   "brightness": "Bright",
#   "density": "Dense",
#   "overall_score": 0.78
# }
```

### 2. 🥈 Groove/Rhythm Analysis (`audio_analysis/groove_analysis.py`)

Detects rhythm patterns and percussion characteristics:

- **Kick Detection**: Presence and regularity of kick drums
  - kick_presence: How likely a kick drum is present (0-1)
  - kick_regularity: How quantized/regular the kicks are (0-1)

- **Percussion Density**: How busy the drums are
  - Busy/Dense: Lots of hi-hats and percussion layers
  - Sparse: Minimal percussion elements

- **Swing Detection**: Human-feel vs perfectly quantized
  - Low swing: Perfect timing, quantized
  - Medium swing: Natural groove feeling
  - High swing: Loose, very human-like timing

- **Groove Classification**:
  - **Driving**: Strong regular kick, structured rhythm
  - **Rolling**: Smooth, bouncing groove
  - **Breaky**: Syncopated, complex patterns
  - **Minimal**: Sparse, simple beat structure

**Usage:**
```python
from audio_analysis.groove_analysis import classify_groove_type
import librosa

y, sr = librosa.load("track.mp3")
groove = classify_groove_type(y, sr)
# {
#   "type": "Driving",
#   "kick_presence": 0.92,
#   "kick_regularity": 0.87,
#   "percussion_density": 0.71,
#   "swing": 0.25
# }
```

### 3. 🥉 Mood Classification (`audio_analysis/mood_classification.py`)

Emotionally intelligent track classification:

- **Major vs Minor**: Tonal quality
  - Major: Bright, happy, positive
  - Minor: Dark, introspective, moody

- **Aggressiveness**: Intensity and attack
  - Soft/mellow: Low aggressiveness
  - Intense/forceful: High aggressiveness

- **Harmonic Tension**: Dissonance levels
  - Consonant: Relaxing, stable harmonies
  - Dissonant: Tense, complex harmonies

- **Mood Classes**:
  - **Dark**: Minor key, low brightness, high tension
  - **Euphoric**: Major key, high brightness, low tension
  - **Melancholic**: Minor key, introspective, not aggressive
  - **Aggressive**: High intensity, fast attack, tense
  - **Chill**: Low energy, relaxing, floating
  - **Driving**: Forward momentum, rhythmic, energetic

**Usage:**
```python
from audio_analysis.mood_classification import classify_mood
import librosa

y, sr = librosa.load("track.mp3")
mood = classify_mood(y, sr)
# {
#   "primary_mood": "Euphoric",
#   "all_moods": {
#     "Dark": 0.05,
#     "Euphoric": 0.68,
#     "Melancholic": 0.08,
#     "Aggressive": 0.12,
#     "Chill": 0.04,
#     "Driving": 0.03
#   },
#   "brightness": 0.82
# }
```

## 🎛️ Transition Scoring Engine (`utils/transition_scoring.py`)

The core engine that combines all analyses for intelligent DJ transitions.

### Transition Score Breakdown

The overall transition score (0-1) is calculated from:

1. **Harmonic Score** (25%): Camelot wheel compatibility
   - Perfect match: 1.0
   - Compatible: 0.85-0.95
   - Relative major/minor: 0.75+
   - Incompatible: < 0.4

2. **Energy Score** (20%): Spectral and loudness shift
   - Similar levels: > 0.8
   - Moderate shift: 0.6-0.8
   - Large shift: < 0.6

3. **Groove Score** (20%): Rhythm pattern compatibility
   - Same type: 1.0
   - Compatible types: 0.7-0.9
   - Incompatible: < 0.5

4. **Mood Score** (20%): Emotional alignment
   - Same mood: 1.0
   - Compatible moods: 0.6-0.9
   - Conflicting moods: < 0.4

5. **BPM Score** (15%): Tempo compatibility
   - Same tempo: 1.0
   - Within 10%: > 0.8
   - Half/double tempo: 0.9
   - Large difference: < 0.4

### Score Interpretation

- **🟢 0.85+**: Excellent transition - seamless mix
- **🟢 0.70-0.84**: Good transition - minor adjustments may help
- **🟡 0.55-0.69**: Acceptable - some care needed
- **🟠 0.40-0.54**: Possible - plan ahead, use effects
- **🔴 < 0.40**: Difficult - significant gear work required

**Usage:**
```python
from utils.transition_scoring import calculate_transition_score
from audio_analysis.key_detection import analyze_track

track1 = analyze_track("track1.mp3")
track2 = analyze_track("track2.mp3")

transition = calculate_transition_score(track1, track2)
# {
#   "overall_score": 0.82,
#   "harmonic_score": 0.85,
#   "energy_score": 0.78,
#   "groove_score": 0.88,
#   "mood_score": 0.75,
#   "bpm_score": 0.92,
#   "recommendation": "🟢 Good transition",
#   "notes": [
#     "✓ Harmonic compatibility excellent",
#     "✓ Groove patterns compatible",
#     "~ Slight energy shift needed",
#     ...
#   ]
# }
```

## 📊 Integration with Main App

The enhanced `analyze_track()` function in `key_detection.py` now returns:

```python
{
    # Original fields
    "file_path": "track.mp3",
    "key": "G Major",
    "camelot": "9A",
    "bpm": 128,
    "duration": 240.5,
    "confidence": 0.92,
    
    # New advanced features
    "energy": {
        "level": "High",
        "loudness": 0.85,
        "brightness": "Bright",
        "brightness_score": 0.72,
        "density": "Dense",
        "richness_score": 0.68,
        "overall_score": 0.75
    },
    "groove": {
        "type": "Driving",
        "kick_presence": 0.88,
        "kick_regularity": 0.82,
        "percussion_density": 0.65,
        "swing": 0.20
    },
    "mood": {
        "primary_mood": "Euphoric",
        "all_moods": {...},
        "is_major": True,
        "brightness": 0.72,
        "aggressiveness": 0.35,
        "tension": 0.28
    }
}
```

## 🎓 Practical Use Cases

### 1. Building DJ Sets

```python
from utils.transition_scoring import find_best_transitions_for_track
from audio_analysis.key_detection import analyze_track

current_track = analyze_track("current.mp3")
candidate_tracks = [
    analyze_track(f"track{i}.mp3") for i in range(1, 11)
]

best_next = find_best_transitions_for_track(current_track, candidate_tracks)
for result in best_next[:5]:  # Top 5 transitions
    print(f"{result['score']:.2f} - {result['recommendation']}")
    # 0.87 - 🟢 Good transition
    # 0.82 - 🟢 Good transition
    # 0.71 - 🟢 Good transition
    # ...
```

### 2. Auto-DJ Playlist Generation

```python
from file_manager.organizaer import find_audio_files
from utils.transition_scoring import find_best_transitions_for_track

music_folder = "path/to/music"
tracks = find_audio_files(music_folder)
analyses = [analyze_track(t) for t in tracks if t.endswith('.mp3')]

# Start with the first track
playlist = [analyses[0]]

for _ in range(10):  # Generate 10 track sequence
    possible_next = find_best_transitions_for_track(playlist[-1], analyses)
    # Filter out already used tracks
    unused = [t for t in possible_next if t['index'] not in [a['file_path'] for a in playlist]]
    if unused:
        next_track = unused[0]['index']
        playlist.append(analyses[next_track])
```

## 🔧 Advanced Configuration

### Tuning Weights

Edit `transition_scoring.py` `calculate_transition_score()` to adjust emphasis:

```python
# Current weights (total = 1.0)
overall_score = (
    harmonic_score * 0.25 +   # Harmonic matching priority
    energy_score * 0.20 +     # Energy smoothness
    groove_score * 0.20 +     # Rhythm compatibility
    mood_score * 0.20 +       # Mood alignment
    bpm_score * 0.15          # Tempo matching
)

# For harmonic-focused mixing:
overall_score = (
    harmonic_score * 0.40 +   # Increased
    energy_score * 0.15 +
    groove_score * 0.15 +
    mood_score * 0.15 +
    bpm_score * 0.15
)
```

### Custom Compatibility Rules

Override mood/groove compatibility matrices:

```python
# In mood_classification.py analyze_mood_compatibility()
compatibility_map = {
    ("Euphoric", "Driving"): 0.95,  # Custom: very compatible
    # ... customize as needed
}
```

## 📈 Performance Notes

- **Analysis time**: ~2-3 seconds per track (depends on CPU)
- **Memory**: ~50-100MB per loaded track
- **Offline**: All analysis is purely local, no internet required
- **Formats**: Works with MP3, WAV, FLAC, OGG, and more (via librosa)

## 🐛 Troubleshooting

**"Unknown" mood/groove/energy values**
- Ensure librosa is installed: `pip install librosa`
- Track may be too short or corrupted
- Try with a different track to test

**Transition scores seem off**
- Check BPM detection accuracy (print `track['bpm']`)
- Verify Camelot key detection (print `track['camelot']`)
- Some edge case tracks may need manual override

**Slow analysis**
- Loading full 60-second tracks; adjust duration parameter if needed
- Consider batch analysis with progress updates in UI

## 📚 Files Summary

| File | Purpose |
|------|---------|
| `audio_analysis/energy_detection.py` | Energy level and brightness detection |
| `audio_analysis/groove_analysis.py` | Rhythm and percussion analysis |
| `audio_analysis/mood_classification.py` | Emotional character classification |
| `utils/transition_scoring.py` | Transition compatibility engine |
| `audio_analysis/key_detection.py` | Updated to integrate all features |

---

**Version**: 1.0  
**Date**: February 2026  
**Status**: Active & Maintained
