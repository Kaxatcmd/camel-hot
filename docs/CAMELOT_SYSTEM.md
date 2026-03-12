## Camelot Wheel System

A comprehensive guide to the Camelot wheel notation and harmonic mixing used in DJ Harmonic Analyzer.

### What is the Camelot Wheel?

The Camelot wheel is a visual and mathematical representation of musical keys as they relate to harmonic compatibilty. It's widely used in DJ mixing because it identifies which keys can be mixed together without dissonance.

```
            11B ╱ 11A
        10B ╱   \  10A
    9B ╱         \ 9A
  8B ╱             \ 8A
7B ╱                 \ 7A
6B ╱                   \ 6A
  5B                   5A
    4B               4A
      3B         3A
        2B   2A
            1B / 1A
```

### Camelot Key Notation

Each key is represented as **NUMBER + LETTER**:

- **Numbers (1-12)**: Position on the wheel (chromatic progression)
- **Letter**:
  - **A**: Major keys
  - **B**: Minor keys

### Compatible Keys

Keys are compatible if they are:

1. **Same Number** (key 8A ✓ 8B)
   - Major and relative minor
   - Always harmonically compatible

2. **Adjacent Numbers** (key 8A ✓ 9A ✓ 7A)
   - One position clockwise or counter-clockwise
   - Very compatible for smooth transitions

3. **+7 Semi-steps** (key 8A ✓ 3A via circle of fifths)
   - Advanced mixing technique
   - Requires more mixing skill

### Camelot Codes and Musical Keys

The relationship between Camelot codes and musical keys:

```
Camelot    Key        Camelot    Key
─────────────────────────────────────
1A         B Major    1B         G# Minor
2A         F# Major   2B         D# Minor
3A         C# Major   3B         A# Minor
4A         G# Major   4B         E# Minor
5A         D# Major   5B         B# Minor
6A         A# Major   6B         F# Minor
7A         F Major    7B         D Minor
8A         C Major    8B         A Minor
9A         G Major    9B         E Minor
10A        D Major    10B        B Minor
11A        A Major    11B        F# Minor
12A        E Major    12B        C# Minor
```

### Application in DJ Mixing

#### Same Key (8A - 8A)
- **Compatibility**: Perfect
- **Use Case**: Seamless blending of tracks in the same key
- **Technique**: Direct mix or long crossfade

#### Adjacent Key (8A - 9A)
- **Compatibility**: Excellent
- **Use Case**: Energy building, smooth transitions
- **Technique**: Predictable energetic shift

#### Relative Minor/Major (8A - 8B)
- **Compatibility**: Perfect
- **Use Case**: Mood changes while maintaining harmonic flow
- **Technique**: Energetic up/down mixing

#### Circle of Fifths (+7) (8A - 3A)
- **Compatibility**: Good
- **Use Case**: Professional key-shifting techniques
- **Technique**: Requires beatmatching mastery

#### Non-Adjacent (8A - 6A)
- **Compatibility**: Poor
- **Use Case**: Avoid unless creating intentional dissonance
- **Result**: Clashing, jarring sound

### Application Implementation

DJ Harmonic Analyzer uses the `utils/camelot_map.py` module to implement this system:

```python
from utils.camelot_map import (
    get_compatible_keys,      # Returns all compatible keys
    is_compatible_keys,        # Checks if two keys are compatible
    get_relative_minor,        # Major ↔ Minor conversion
    CAMELOT_MAP                # Dictionary of key mappings
)
```

#### Finding Compatible Tracks

```python
from gui.file_manager.organizer import create_playlist
from utils.camelot_map import get_compatible_keys

# Find all tracks compatible with 8A
compatible = get_compatible_keys('8A')
# Returns: ['8A', '8B', '7A', '9A', '3A']

# Create playlist of compatible tracks
playlist = create_playlist(
    input_directory='/music',
    output_file='compatible_mix.m3u',
    target_key='8A'
)
```

#### Organizing by Zone

The `ZONE` concept groups related keys:

- **Zone 8**: Keys 8A, 8B, 7A, 7B, 9A, 9B
- **Zone 3**: Keys 3A, 3B, 2A, 2B, 4A, 4B
- etc.

All keys within a zone are mutually compatible for basic mixing.

### Building Harmonic Journeys

The Camelot wheel enables building playlists that follow musical journeys:

#### Linear Journey (8A → 9A → 10A)
```python
create_harmonic_sequence_playlist(
    input_directory='/music',
    output_file='progressive_mix.m3u',
    start_key='8A',
    sequence_length=5,
    direction='forward'  # Follows 8A→9A→10A→11A→12A
)
```

#### Key-to-Key Transition (8A → 3A)
```python
create_key_to_key_playlist(
    input_directory='/music',
    output_file='transition.m3u',
    start_key='8A',
    target_key='3A'
)
# Finds harmonic path on wheel
```

### Tools: Camelot Wheel Generator

The application can generate a visual Camelot wheel image:

```python
from utils.camelot_wheel_generator import generate_camelot_wheel
generate_camelot_wheel('/path/to/output/wheel.png')
```

Generated wheel:
- Shows all 24 keys positioned around the circle
- Color-coded for major (one color) and minor (another color)
- Demonstrates harmonic relationships visually

### Camelot Map Reference

The canonical Camelot mapping is stored in `utils/camelot_map.py`:

```python
CAMELOT_MAP = {
    '#1|A': ('B', 'Major'),
    '#1|B': ('G#', 'Minor'),
    '#2|A': ('F#', 'Major'),
    '#2|B': ('D#', 'Minor'),
    # ... 24 entries total
}
```

This mapping is used for:
- Key detection result conversion
- Compatibility checking
- Playlist filtering
- File organization

### Advanced Mixing Techniques

#### 1. Energy Building Path
```
8A (135 BPM) → 9A (137 BPM) → 10A (139 BPM)
```
Energy steadily increases while remaining harmonic.

#### 2. Mood Shift
```
8A (Major, uplifting) → 8B (Minor, introspective)
```
Same chord structure, different emotional tone.

#### 3. Circle of Fifths Jump
```
8A → 3A (professional mixing technique)
```
Requires precise beatmatching and mixing finesse.

#### 4. Zone-Based Mixing
```
Stay within Zone 8 (7A, 7B, 8A, 8B, 9A, 9B)
```
All combinations work well together.

### Troubleshooting

#### "Why doesn't 8A mix with 10A?"
- They're not adjacent on the wheel
- 8A only mixes with: 8B, 7A, 9A, 3A
- Use the compatibility checker to verify

#### "Can I force-mix incompatible keys?"
- Technically yes, but it will sound dissonant
- DJ software allows it, but results are jarring
- Only advisable for experimental/intentional dissonance

#### "Which keys work with my track?"
```python
from utils.camelot_map import get_compatible_keys
compatible = get_compatible_keys('8A')
print(compatible)  # ['8A', '8B', '7A', '9A', '3A']
```

### Further Reading

- **[Mixed In Key](https://www.mixedinkey.com/camelot-wheel/)**: Official Camelot wheel documentation
- **[DJ.com Camelot Guide](https://www.dj.com/)**: Comprehensive mixing guide
- **[Harmonic Mixing](https://en.wikipedia.org/wiki/Harmonic_mixing)**: Wikipedia article on harmonic mixing

### Implementation Details

The Camelot system in DJ Harmonic Analyzer:

1. **Input**: Musical key detected via chroma analysis (e.g., "C major")
2. **Mapping**: Convert to Camelot notation (e.g., "8A")
3. **Compatibility**: Check against user's key or zone
4. **Organization**: Create folder or playlist
5. **Output**: Move/copy files or generate M3U

The entire flow is abstracted from the user - they select options, and the system handles the Camelot calculations.

---

**Camelot System Guide Version**: 2.0 (2026)
