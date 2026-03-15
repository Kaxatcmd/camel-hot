"""
Key Detection - Finding the Musical Key of a Song

This module contains the core logic for detecting the musical key
(and BPM) of an audio file.

Musical key detection works by:
1. Loading the audio file
2. Analyzing the frequency content (what notes are present)
3. Looking for patterns that match major or minor scales
4. Finding the strongest pitch profile to determine the key

Note: This is a simplified version. Real key detection is complex
and typically uses libraries like librosa or Essentia.
"""

# In a real implementation, you'd use audio processing libraries
# For this example, we'll show the structure and concepts

try:
    # Librosa is great for audio analysis
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("Tip: Install librosa for audio analysis with 'pip install librosa'")


# ─────────────────────────────────────────────────────────────────────────────
# Krumhansl-Schmuckler key profiles (standard musicology / academic standard)
# Each list has 12 values representing how strongly each chroma pitch class
# (C, C#, D … B) is associated with that key.
# ─────────────────────────────────────────────────────────────────────────────
_KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
              2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
              2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

# Note names for all 12 semitones
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

# All notes in the chromatic scale (all 12 semitones)
ALL_NOTES = NOTE_NAMES  # backward-compat alias


def _pearson_correlation(x, y):
    """Pearson correlation between two equal-length sequences."""
    import math
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denom = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) *
                      sum((yi - mean_y) ** 2 for yi in y))
    return num / denom if denom > 0 else 0.0


def _best_key_from_chroma(chroma_vector):
    """
    Use the Krumhansl-Schmuckler algorithm to find the best-matching key.

    Correlates the 12-element chroma vector against major and minor templates
    for all 12 root notes and returns the best match + confidence.

    Args:
        chroma_vector: List/array of 12 floats (chroma energies C…B)

    Returns:
        (key_name, confidence, all_scores)
          key_name  \u2014 'C Major', 'A Minor', etc.
          confidence \u2014 Pearson r of the winning template (0-1 clamped)
          all_scores \u2014 dict mapping every key name to its correlation
    """
    chroma_list = list(chroma_vector)
    best_key = "C Major"
    best_score = -2.0
    all_scores = {}

    for root_idx in range(12):
        # Rotate templates to align with this root note
        major_template = _KS_MAJOR[root_idx:] + _KS_MAJOR[:root_idx]
        minor_template = _KS_MINOR[root_idx:] + _KS_MINOR[:root_idx]

        major_r = _pearson_correlation(chroma_list, major_template)
        minor_r = _pearson_correlation(chroma_list, minor_template)

        root_name = NOTE_NAMES[root_idx]
        major_key = f"{root_name} Major"
        minor_key = f"{root_name} Minor"

        all_scores[major_key] = major_r
        all_scores[minor_key] = minor_r

        if major_r > best_score:
            best_score = major_r
            best_key = major_key
        if minor_r > best_score:
            best_score = minor_r
            best_key = minor_key

    # Pearson r is [-1, 1]; clamp positive range to use as confidence
    confidence = max(0.0, min(best_score, 1.0))
    return best_key, confidence, all_scores


def _note_to_frequency(note_name):
    """
    Convert a note name to its frequency in Hz.
    
    Middle A (A4) is defined as 440 Hz - this is the tuning standard.
    All other notes are calculated relative to this.
    
    Example:
        A4 = 440 Hz
        A5 = 880 Hz (one octave higher)
        A3 = 220 Hz (one octave lower)
    """
    # This uses the formula: frequency = 440 * 2^((n-69)/12)
    # where n is the MIDI note number for that note
    pass  # Implementation would go here


def _find_strongest_pitch(y, sr):
    """
    Find the most dominant pitch/frequency in the audio.
    
    This looks at the audio waveform and finds the frequency
    that has the most energy - that's likely the root note!
    
    Args:
        y: The audio time series (waveform)
        sr: Sample rate (samples per second)
    
    Returns:
        The frequency in Hz of the strongest pitch
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Use librosa's pitch detection
        # This gives us the fundamental frequency (F0) over time
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        # Find the strongest pitch across all time
        strongest_pitch = 0
        max_magnitude = 0
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            magnitude = magnitudes[index, t]
            
            if magnitude > max_magnitude:
                max_magnitude = magnitude
                strongest_pitch = pitches[index, t]
        
        # Se não encontrou pitch com piptrack, tenta outra abordagem
        if strongest_pitch == 0:
            # Usar spectral centroid como fallback
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            strongest_pitch = spectral_centroids.mean()
        
        return strongest_pitch if strongest_pitch > 0 else None
    
    except Exception as e:
        print(f"Erro ao detectar pitch: {e}")
        return None


def _frequency_to_note(frequency):
    """
    Convert a frequency (Hz) to a note name.
    
    Given something like 440 Hz, this tells you it's A4 (A in octave 4).
    
    Args:
        frequency: Sound frequency in Hertz
    
    Returns:
        Note name like "A4" or "C#5"
    """
    if frequency <= 0:
        return "Unknown"
    
    # Formula in reverse: n = 12 * log2(frequency/440) + 69
    # This gives us the MIDI note number
    midi_note = 12 * (frequency / 440.0).bit_length() + 69
    # Wait, that's not right. Let me fix it...
    
    # Correct formula:
    # MIDI note number = 69 + 12 * log2(frequency / 440)
    import math
    midi_note = 69 + 12 * math.log2(frequency / 440)
    midi_note = round(midi_note)
    
    # Get the octave number (middle C is C4 = MIDI note 60)
    octave = midi_note // 12 - 1
    
    # Get the note within the octave (0-11)
    note_index = midi_note % 12
    
    return f"{ALL_NOTES[note_index]}{octave}"


def detect_key_from_audio(file_path):
    """
    Detect the musical key of an audio file using Krumhansl-Schmuckler profiles.

    Analyses the full chroma vector of the track and correlates it against all
    24 major/minor templates. Also reports secondary key candidates.

    Args:
        file_path: Path to the audio file (mp3, wav, etc.)

    Returns:
        dict with:
          - 'key': The detected key name (e.g., "C Major")
          - 'camelot': The Camelot notation (e.g., "8B")
          - 'confidence': How sure we are (0-1, Pearson r of best template)
          - 'secondary_key': Second-best key candidate
          - 'secondary_camelot': Camelot code for secondary key
    """
    if not LIBROSA_AVAILABLE:
        return {
            "key": "Unknown - librosa not installed",
            "camelot": "Unknown",
            "confidence": 0.0,
            "secondary_key": None,
            "secondary_camelot": None,
        }

    try:
        # Load first 60 s for overall key; use CQT chroma (more accurate for key)
        y, sr = librosa.load(file_path, duration=60)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)  # 12-element vector

        key_name, confidence, all_scores = _best_key_from_chroma(chroma_mean)

        from utils.camelot_map import get_camelot_key
        camelot = get_camelot_key(key_name)

        # Find secondary key (for tracks near a modulation boundary)
        sorted_scores = sorted(all_scores.items(), key=lambda kv: kv[1], reverse=True)
        secondary_key = sorted_scores[1][0] if len(sorted_scores) > 1 else None
        secondary_camelot = get_camelot_key(secondary_key) if secondary_key else None

        return {
            "key": key_name,
            "camelot": camelot,
            "confidence": round(confidence, 3),
            "secondary_key": secondary_key,
            "secondary_camelot": secondary_camelot,
        }

    except Exception as e:
        print(f"Erro ao detectar tonalidade: {e}")
        return {
            "key": f"Erro ao detectar: {str(e)}",
            "camelot": "Unknown",
            "confidence": 0.0,
            "secondary_key": None,
            "secondary_camelot": None,
        }


def detect_key_segments(y, sr, segment_duration=30):
    """
    Detect the key in each time segment to find modulations.

    Divides the audio into windows of *segment_duration* seconds and runs
    the Krumhansl-Schmuckler algorithm independently on each segment.

    Args:
        y: Audio time-series (numpy array)
        sr: Sample rate
        segment_duration: Window length in seconds (default 30)

    Returns:
        list of dicts, one per segment:
          { 'start_s', 'end_s', 'key', 'camelot', 'confidence' }
    """
    if not LIBROSA_AVAILABLE:
        return []

    try:
        total_samples = len(y)
        seg_samples = int(segment_duration * sr)
        segments = []
        from utils.camelot_map import get_camelot_key

        offset = 0
        while offset < total_samples:
            end = min(offset + seg_samples, total_samples)
            seg = y[offset:end]
            if len(seg) < sr * 2:  # skip very short tails
                break

            chroma = librosa.feature.chroma_cqt(y=seg, sr=sr)
            key_name, conf, _ = _best_key_from_chroma(chroma.mean(axis=1))
            segments.append({
                "start_s": round(offset / sr, 1),
                "end_s": round(end / sr, 1),
                "key": key_name,
                "camelot": get_camelot_key(key_name),
                "confidence": round(conf, 3),
            })
            offset += seg_samples

        return segments
    except Exception as e:
        print(f"Error in segment key detection: {e}")
        return []


def detect_key_modulations(y, sr, segment_duration=30):
    """
    Detect key modulations (key changes) within a track.

    Args:
        y: Audio time-series
        sr: Sample rate
        segment_duration: Seconds per analysis window

    Returns:
        dict with:
          - 'primary_key': Most common key across segments
          - 'primary_camelot': Camelot code for primary key
          - 'key_stability': 0-1 fraction of segments matching primary key
          - 'modulations': list of dicts describing each detected key change
            { 'timestamp_s', 'from_key', 'to_key', 'from_camelot', 'to_camelot' }
          - 'segments': full segment list
    """
    if not LIBROSA_AVAILABLE:
        return {
            "primary_key": "Unknown",
            "primary_camelot": "Unknown",
            "key_stability": 0.0,
            "modulations": [],
            "segments": [],
        }

    try:
        segments = detect_key_segments(y, sr, segment_duration)
        if not segments:
            return {
                "primary_key": "Unknown",
                "primary_camelot": "Unknown",
                "key_stability": 0.0,
                "modulations": [],
                "segments": [],
            }

        # Find dominant key
        from collections import Counter
        key_counts = Counter(s["key"] for s in segments)
        primary_key = key_counts.most_common(1)[0][0]
        from utils.camelot_map import get_camelot_key
        primary_camelot = get_camelot_key(primary_key)

        matching = sum(1 for s in segments if s["key"] == primary_key)
        key_stability = matching / len(segments)

        # Detect modulation events (consecutive segments with different keys)
        modulations = []
        for i in range(1, len(segments)):
            prev = segments[i - 1]
            curr = segments[i]
            if curr["key"] != prev["key"]:
                modulations.append({
                    "timestamp_s": curr["start_s"],
                    "from_key": prev["key"],
                    "to_key": curr["key"],
                    "from_camelot": prev["camelot"],
                    "to_camelot": curr["camelot"],
                })

        return {
            "primary_key": primary_key,
            "primary_camelot": primary_camelot,
            "key_stability": round(key_stability, 2),
            "modulations": modulations,
            "segments": segments,
        }
    except Exception as e:
        print(f"Error detecting modulations: {e}")
        return {
            "primary_key": "Unknown",
            "primary_camelot": "Unknown",
            "key_stability": 0.0,
            "modulations": [],
            "segments": [],
        }


def _guess_scale_type(chroma_vector):
    """
    Guess whether a track is in a major or minor scale.
    Legacy helper kept for backward compatibility.
    Delegates to the Krumhansl-Schmuckler algorithm now.
    """
    try:
        key_name, _, _ = _best_key_from_chroma(chroma_vector)
        return "Major" in key_name
    except Exception:
        return True  # default: major


def detect_bpm(file_path):
    """
    Detect the BPM (beats per minute) of an audio file.

    Also returns a confidence score and a variability percentage that indicates
    whether the tempo is steady or fluctuating.

    Args:
        file_path: Path to the audio file

    Returns:
        BPM value as a float, or None if detection failed.
        (For extended info call detect_bpm_advanced().)
    """
    result = detect_bpm_advanced(file_path)
    return result.get("bpm") if result else None


def detect_bpm_advanced(file_path):
    """
    Advanced BPM detection with confidence and variability.

    Args:
        file_path: Path to the audio file

    Returns:
        dict with:
          - 'bpm': primary BPM (float or None)
          - 'bpm_confidence': 0-1 confidence score
          - 'bpm_variability': 0-100 % variability (0 = rock-solid, 100 = chaotic)
          - 'half_time_bpm': bpm / 2 (useful for double-time detection)
          - 'double_time_bpm': bpm * 2
    """
    if not LIBROSA_AVAILABLE:
        return {"bpm": None, "bpm_confidence": 0.0, "bpm_variability": 0.0,
                "half_time_bpm": None, "double_time_bpm": None}

    try:
        import warnings
        y, sr = librosa.load(file_path, duration=60)

        # Onset envelope for variability analysis
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Primary BPM estimate
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                tempo_arr = librosa.feature.rhythm.tempo(y=y, sr=sr)
            except AttributeError:
                tempo_arr = librosa.beat.tempo(y=y, sr=sr)

        if hasattr(tempo_arr, '__iter__'):
            bpm = float(tempo_arr[0]) if len(tempo_arr) > 0 else None
        else:
            bpm = float(tempo_arr) if tempo_arr else None

        if not bpm or bpm <= 0:
            return {"bpm": None, "bpm_confidence": 0.0, "bpm_variability": 0.0,
                    "half_time_bpm": None, "double_time_bpm": None}

        bpm = round(bpm, 1)

        # Estimate BPM confidence from onset autocorrelation peak sharpness
        try:
            ac = librosa.autocorrelate(onset_env, max_size=sr // 2)
            ac_norm = ac / (ac.max() + 1e-10)
            confidence = float(ac_norm[1:].max())
        except Exception:
            confidence = 0.7

        # Estimate variability: stdev of local BPM measured in 10 s windows
        win_samples = int(10 * sr)
        local_bpms = []
        for start in range(0, len(y) - win_samples, win_samples):
            seg = y[start:start + win_samples]
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        t = librosa.feature.rhythm.tempo(y=seg, sr=sr)
                    except AttributeError:
                        t = librosa.beat.tempo(y=seg, sr=sr)
                local_bpms.append(float(t[0]) if hasattr(t, '__iter__') else float(t))
            except Exception:
                pass

        if len(local_bpms) > 1:
            variability = float(np.std(local_bpms) / (np.mean(local_bpms) + 1e-10) * 100)
        else:
            variability = 0.0

        return {
            "bpm": bpm,
            "bpm_confidence": round(min(confidence, 1.0), 3),
            "bpm_variability": round(min(variability, 100.0), 1),
            "half_time_bpm": round(bpm / 2, 1),
            "double_time_bpm": round(bpm * 2, 1),
        }

    except Exception as e:
        print(f"Erro ao detectar BPM: {e}")
        return {"bpm": None, "bpm_confidence": 0.0, "bpm_variability": 0.0,
                "half_time_bpm": None, "double_time_bpm": None}


def analyze_track(file_path):
    """
    Complete analysis of a track - key, BPM, energy, groove, and mood.
    
    This gives you all the important musical information about
    a song in one call, including advanced features for smart transitions.
    
    Args:
        file_path: Path to the audio file
    
    Returns:
        Dictionary with:
        - file_path: Where the file is
        - key: Musical key name
        - camelot: Camelot notation
        - bpm: Beats per minute
        - duration: How long the track is (seconds)
        - confidence: Key detection confidence (0-1)
        - energy: Energy level classification (if librosa available)
        - groove: Groove type and characteristics (if librosa available)
        - mood: Mood classification and scores (if librosa available)
    
    Example:
        >>> info = analyze_track("my_song.mp3")
        >>> print(f"This song is in {info['camelot']} at {info['bpm']} BPM")
        >>> print(f"Mood: {info['mood']['primary_mood']}, Energy: {info['energy']['level']}")
        This song is in 8A at 120 BPM
        Mood: Euphoric, Energy: High
    """
def analyze_track(file_path):
    """
    Complete analysis of a track - key, BPM, energy, groove, mood, and modulations.

    Maintains backward-compatible return shape while adding extended fields:
      Required: file_path, key, camelot, bpm, duration, confidence
      Extended: energy, groove, mood, secondary_key, secondary_camelot,
                key_stability, modulations, bpm_confidence, bpm_variability,
                half_time_bpm, double_time_bpm

    Args:
        file_path: Path to the audio file

    Returns:
        Dictionary described above.
    """
    if not LIBROSA_AVAILABLE:
        return {
            "file_path": file_path,
            "key": "Unknown - librosa not installed",
            "camelot": "Unknown",
            "bpm": None,
            "duration": None,
            "error": "Install librosa: pip install librosa"
        }

    try:
        y, sr = librosa.load(file_path, duration=60)
        duration = librosa.get_duration(y=y, sr=sr)

        print(f"🎵 Analisando: {file_path}")
        print(f"   ⏱️  Duração: {duration:.2f}s")

        # ── Key detection (Krumhansl-Schmuckler) ──────────────────────────────
        print(f"   🔍 Detectando tonalidade (Krumhansl-Schmuckler)...")
        key_info = detect_key_from_audio(file_path)

        # ── Modulation analysis ───────────────────────────────────────────────
        print(f"   🔄 Analisando modulações...")
        modulation_info = detect_key_modulations(y, sr, segment_duration=30)

        # ── BPM (advanced) ────────────────────────────────────────────────────
        print(f"   ⏱️  Detectando BPM (avançado)...")
        bpm_info = detect_bpm_advanced(file_path)

        # ── Energy ────────────────────────────────────────────────────────────
        print(f"   ⚡ Detectando nível de energia...")
        from audio_analysis.energy_detection import classify_energy_level
        energy = classify_energy_level(y, sr)

        # ── Groove ────────────────────────────────────────────────────────────
        print(f"   🥁 Analisando groove...")
        from audio_analysis.groove_analysis import classify_groove_type
        groove = classify_groove_type(y, sr)

        # ── Mood ──────────────────────────────────────────────────────────────
        print(f"   😊 Classificando humor...")
        from audio_analysis.mood_classification import classify_mood
        mood = classify_mood(y, sr)

        result = {
            # ── Core fields (backward-compatible) ──────────────────────────
            "file_path": file_path,
            "key": key_info["key"],
            "camelot": key_info["camelot"],
            "bpm": bpm_info["bpm"],
            "duration": round(duration, 2),
            "confidence": key_info["confidence"],
            # ── Enhanced key fields ─────────────────────────────────────────
            "secondary_key": key_info.get("secondary_key"),
            "secondary_camelot": key_info.get("secondary_camelot"),
            "key_stability": modulation_info.get("key_stability", 1.0),
            "modulations": modulation_info.get("modulations", []),
            "key_segments": modulation_info.get("segments", []),
            # ── Enhanced BPM fields ─────────────────────────────────────────
            "bpm_confidence": bpm_info.get("bpm_confidence", 0.0),
            "bpm_variability": bpm_info.get("bpm_variability", 0.0),
            "half_time_bpm": bpm_info.get("half_time_bpm"),
            "double_time_bpm": bpm_info.get("double_time_bpm"),
            # ── Sub-analysis dicts ──────────────────────────────────────────
            "energy": energy,
            "groove": groove,
            "mood": mood,
        }

        print(f"   ✅ Análise completa!")
        print(f"      • Tonalidade: {result['key']} (conf={result['confidence']:.2f})")
        print(f"      • Camelot: {result['camelot']}")
        print(f"      • BPM: {result['bpm']} (var={result['bpm_variability']:.1f}%)")
        print(f"      • Estabilidade tonal: {result['key_stability']:.0%}")
        if modulation_info.get("modulations"):
            print(f"      • Modulações detectadas: {len(modulation_info['modulations'])}")
        if energy:
            print(f"      • Energia: {energy.get('level', 'Unknown')} "
                  f"({energy.get('numeric_score', '?')}/10)")
        if groove:
            print(f"      • Groove: {groove.get('type', 'Unknown')} "
                  f"/ Família: {groove.get('groove_family', '?')}")
        if mood:
            print(f"      • Humor: {mood.get('primary_mood', 'Unknown')}")

        return result

    except Exception as e:
        print(f"❌ Erro ao analisar {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "file_path": file_path,
            "key": f"Erro: {str(e)}",
            "camelot": "Unknown",
            "bpm": None,
            "duration": None,
        }

