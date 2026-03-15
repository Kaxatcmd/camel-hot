"""
Mood Classification - Detecting Emotional Character of Tracks

This module classifies track mood based on:
- Major vs Minor tonality
- Spectral brightness (dark = less bright, euphoric = bright)
- Aggressiveness (attack/intensity of sounds)
- Harmonic tension (dissonance vs consonance)

Mood categories: Dark, Euphoric, Melancholic, Aggressive, Chill, Driving,
                 Romantic, Intense, Trance

Extended metrics: danceability (0-100), emotional_impact (0-100), genre_hint
"""

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


def detect_major_minor(y, sr):
    """
    Detect if track is major (happy) or minor (sad) scale.
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        dict with:
        - is_major: Boolean, True if major
        - confidence: 0-1, how sure we are
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Calculate chroma features
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        
        # Normalize
        chroma_norm = chroma_mean / (chroma_mean.sum() + 1e-10)
        
        # Major scale pattern (0=C, 4=E major third, 7=G fifth)
        # Minor scale pattern (0=C, 3=Eb minor third, 7=G fifth)
        
        # Score based on 3rd degree (major=pos, minor=neg)
        major_score = chroma_norm[4] - chroma_norm[3]
        
        # Normalize to 0-1
        confidence = abs(major_score)
        is_major = major_score > 0
        
        return {
            "is_major": is_major,
            "confidence": min(confidence, 1.0),
            "major_score": major_score
        }
    except Exception as e:
        logger.error(f"Error detecting major/minor: {e}")
        return None


def detect_aggressiveness(y, sr):
    """
    Detect how aggressive/intense a track sounds.
    
    Aggressive tracks have:
    - Fast attack on percussive elements
    - Distorted/harsh timbres
    - High spectral flux (rapid changes)
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        aggressiveness_score: 0-1, where 1 is very aggressive
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Calculate spectral flux (rate of change in spectrum)
        S = librosa.feature.melspectrogram(y=y, sr=sr)
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Compute spectral flux (difference between consecutive frames)
        flux = np.sqrt(np.sum(np.diff(S_db, axis=1) ** 2, axis=0))
        
        # High flux = aggressive
        aggressiveness = flux.mean()
        
        # Normalize (typical range 0-200)
        aggressiveness = min(aggressiveness / 200, 1.0)
        
        # Also consider attack time of onsets
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        try:
            # Librosa 0.11+ requires all keyword arguments including wait and delta
            onset_frames = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.0, wait=10)
        except (TypeError, AttributeError):
            # Fallback: if peak_pick not available, use simple threshold
            onset_frames = np.where(onset_env > onset_env.mean())[0]
        
        if len(onset_frames) > 0:
            # Steepness of onset peaks
            peaks_energy = onset_env[onset_frames]
            attack_steepness = peaks_energy.mean()
            attack_steepness = min(attack_steepness, 1.0)
        else:
            attack_steepness = 0.3
        
        # Combine metrics
        final_aggressiveness = aggressiveness * 0.6 + attack_steepness * 0.4
        
        return min(final_aggressiveness, 1.0)
    except Exception as e:
        logger.error(f"Error detecting aggressiveness: {e}")
        return 0.5


def detect_harmonic_tension(y, sr):
    """
    Detect level of harmonic tension in the track.
    
    High tension: dissonant chords, complex harmonies
    Low tension: consonant chords, simple harmonies
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        tension_score: 0-1, where 1 is very tense/dissonant
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Analyze chroma vector for dissonance
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        
        # Normalize
        chroma_norm = chroma_mean / (chroma_mean.sum() + 1e-10)
        
        # Calculate entropy of chroma (more spread = more tension)
        # Entropy: -sum(p * log(p))
        entropy = -np.sum(chroma_norm * np.log(chroma_norm + 1e-10))
        
        # Entropy range for 12 notes: 0 to log(12) ≈ 2.48
        # Normalize
        tension = entropy / np.log(12)
        
        # Additional: detect dissonant intervals
        # Dissonant = tritones, minor seconds, major sevenths
        dissonant_intervals = [1, 6, 11]  # semitone distances
        dissonant_energy = 0
        
        for interval in dissonant_intervals:
            dissonant_energy += chroma_norm[interval]
        
        dissonance_score = dissonant_energy / len(dissonant_intervals)
        
        # Combine metrics
        final_tension = tension * 0.5 + dissonance_score * 0.5
        
        return min(final_tension, 1.0)
    except Exception as e:
        logger.error(f"Error detecting tension: {e}")
        return 0.5


def detect_brightness(y, sr):
    """
    Detect spectral brightness (high-frequency content).
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        brightness_score: 0-1, where 1 is very bright
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        brightness = spectral_centroid.mean() / (sr / 2)
        return min(brightness, 1.0)
    except Exception as e:
        logger.error(f"Error detecting brightness: {e}")
        return 0.5


def detect_danceability(y, sr):
    """
    Estimate danceability on a 0-100 scale.

    Combines beat clarity, onset regularity, tempo fitness,
    and bass-line prominence — key predictors of urge to dance.

    Returns:
        danceability: int 0-100
    """
    if not LIBROSA_AVAILABLE:
        return 50

    try:
        import warnings
        # Beat clarity from onset strength autocorrelation
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        ac = librosa.autocorrelate(onset_env, max_size=sr // 2)
        ac_norm = ac / (ac.max() + 1e-10)
        beat_clarity = float(ac_norm[1:].max())

        # Tempo fitness: tempos 80-140 BPM are most danceable
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                tempo_arr = librosa.feature.rhythm.tempo(y=y, sr=sr)
            except AttributeError:
                tempo_arr = librosa.beat.tempo(y=y, sr=sr)
        bpm = float(tempo_arr[0]) if hasattr(tempo_arr, '__iter__') else float(tempo_arr)
        if 80 <= bpm <= 140:
            tempo_fit = 1.0
        elif 60 <= bpm < 80 or 140 < bpm <= 175:
            tempo_fit = 0.7
        else:
            tempo_fit = 0.4

        # Onset regularity: small coefficient of variation of intervals
        try:
            onset_frames = librosa.util.peak_pick(onset_env,
                           pre_max=3, post_max=3, pre_avg=3, post_avg=3,
                           delta=0.0, wait=10)
        except (TypeError, AttributeError):
            onset_frames = np.where(onset_env > onset_env.mean())[0]
        if len(onset_frames) > 4:
            intervals = np.diff(librosa.frames_to_time(onset_frames, sr=sr))
            cv = float(np.std(intervals) / (np.mean(intervals) + 1e-6))
            regularity = max(0.0, 1.0 - cv * 2)
        else:
            regularity = 0.5

        score = (beat_clarity * 0.40 + tempo_fit * 0.35 + regularity * 0.25) * 100
        return int(round(min(score, 100)))
    except Exception as e:
        logger.error(f"Error detecting danceability: {e}")
        return 50


def detect_emotional_impact(aggressiveness, tension, brightness, is_major):
    """
    Estimate the emotional impact of the track on a 0-100 scale.

    High-impact tracks have strong emotional polarity (very bright/dark,
    very tense/relaxed, high aggressiveness).

    Returns:
        emotional_impact: int 0-100
    """
    try:
        # Distance from "neutral" (0.5) in each dimension drives impact
        bright_polar   = abs(brightness - 0.5) * 2        # 0-1
        tension_polar  = abs(tension - 0.5) * 2            # 0-1
        # Aggressiveness directly contributes
        agg_contrib    = aggressiveness                     # 0-1
        # Minor mode increases emotional weight
        mode_bonus     = 0.2 if not is_major else 0.0

        raw = (bright_polar * 0.30 + tension_polar * 0.30 +
               agg_contrib * 0.30 + mode_bonus) / 1.10     # normalise
        return int(round(min(raw * 100, 100)))
    except Exception:
        return 50


def detect_genre_hint(y, sr, brightness, perc_density_proxy, bpm=None):
    """
    Provide a broad genre hint based on spectral and rhythmic features.

    Returns one of: Electronic, Acoustic, Orchestral, Hip-Hop, Jazz-Blues,
                    Heavy/Metal, Pop, Ambient

    Args:
        y: Audio time series
        sr: Sample rate
        brightness: 0-1 spectral brightness score
        perc_density_proxy: 0-1 inferred from high-freq content
        bpm: Optional BPM value
    """
    if not LIBROSA_AVAILABLE:
        return "Unknown"

    try:
        # Zero-crossing rate: high = noisy/percussive, low = tonal
        zcr = float(librosa.feature.zero_crossing_rate(y)[0].mean())

        # Spectral flatness: 1 = noise-like (distortion, synths), 0 = tonal
        flatness = float(librosa.feature.spectral_flatness(y=y)[0].mean())

        # Spectral rolloff (85 % energy concentration)
        rolloff = float(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)[0].mean())
        rolloff_ratio = rolloff / (sr / 2)

        if zcr < 0.03 and brightness < 0.35 and not bpm:
            return "Orchestral"
        if zcr < 0.04 and brightness < 0.45:
            return "Acoustic"
        if bpm and bpm < 80 and brightness < 0.45 and perc_density_proxy < 0.35:
            return "Jazz-Blues"
        if bpm and bpm < 90 and zcr > 0.08 and flatness > 0.05:
            return "Hip-Hop"
        if flatness > 0.08 and zcr > 0.12:
            return "Heavy/Metal"
        if bpm and bpm > 120 and brightness > 0.50 and perc_density_proxy > 0.45:
            return "Electronic"
        if brightness < 0.25 and perc_density_proxy < 0.25:
            return "Ambient"
        return "Pop"
    except Exception as e:
        logger.error(f"Error detecting genre hint: {e}")
        return "Unknown"


def classify_mood(y, sr):
    """
    Classify track mood with expanded categories and new metrics.

    Mood classes: Dark, Euphoric, Melancholic, Aggressive, Chill, Driving,
                  Romantic, Intense, Trance

    Args:
        y: Audio time series
        sr: Sample rate

    Returns:
        dict with:
          - primary_mood: Most likely mood label
          - all_moods: dict of score for each mood (0-1 normalised)
          - is_major: bool
          - aggressiveness: 0-1
          - brightness: 0-1
          - tension: 0-1
          - danceability: int 0-100
          - emotional_impact: int 0-100
          - genre_hint: str (e.g. "Electronic")
    """
    if not LIBROSA_AVAILABLE:
        return None

    try:
        major_info     = detect_major_minor(y, sr)
        aggressiveness = detect_aggressiveness(y, sr)
        tension        = detect_harmonic_tension(y, sr)
        brightness     = detect_brightness(y, sr)

        if major_info is None:
            return None

        is_major       = major_info["is_major"]
        aggressiveness = aggressiveness if aggressiveness is not None else 0.5
        tension        = tension        if tension        is not None else 0.5
        brightness     = brightness     if brightness     is not None else 0.5

        mood_scores = {
            "Dark":       0.0,
            "Euphoric":   0.0,
            "Melancholic": 0.0,
            "Aggressive": 0.0,
            "Chill":      0.0,
            "Driving":    0.0,
            "Romantic":   0.0,
            "Intense":    0.0,
            "Trance":     0.0,
        }

        # ── Scoring rules ──────────────────────────────────────────────────────
        mood_scores["Dark"] = (
            (0.5 if not is_major else 0) +
            (1.0 - brightness) * 0.5 +
            tension * 0.3
        ) / 2.5

        mood_scores["Euphoric"] = (
            (0.5 if is_major else 0) +
            brightness * 0.5 +
            (1.0 - tension) * 0.3
        ) / 2.5

        mood_scores["Melancholic"] = (
            (0.5 if not is_major else 0) +
            (1.0 - brightness) * 0.3 +
            tension * 0.5 * (1.0 - aggressiveness)
        ) / 2.5

        mood_scores["Aggressive"] = (
            aggressiveness * 0.6 +
            tension * 0.4
        ) / 2.0

        mood_scores["Chill"] = (
            (1.0 - aggressiveness) * 0.4 +
            (1.0 - tension) * 0.3 +
            (1.0 - abs(brightness - 0.5)) * 0.3
        ) / 2.0

        mood_scores["Driving"] = (
            brightness * 0.3 +
            aggressiveness * 0.4 +
            max(0, 1.0 - tension) * 0.3
        ) / 2.0

        # Romantic: major, lower aggressiveness, medium-high brightness, low tension
        mood_scores["Romantic"] = (
            (0.5 if is_major else 0.1) +
            (1.0 - aggressiveness) * 0.4 +
            brightness * 0.3 +
            (1.0 - tension) * 0.2
        ) / 2.5

        # Intense: very high aggressiveness, high tension, any mode
        mood_scores["Intense"] = (
            aggressiveness * 0.7 +
            tension * 0.3
        ) / 1.5

        # Trance: minor, medium brightness, low-medium tension, low aggressiveness
        mood_scores["Trance"] = (
            (0.4 if not is_major else 0.1) +
            (1.0 - aggressiveness) * 0.35 +
            (1.0 - abs(brightness - 0.45)) * 0.30 +
            (1.0 - tension) * 0.25
        ) / 2.0

        # Normalise
        total = sum(mood_scores.values())
        if total > 0:
            for m in mood_scores:
                mood_scores[m] = round(mood_scores[m] / (total + 1e-10), 4)

        primary_mood = max(mood_scores, key=mood_scores.get)

        # ── Extended metrics ───────────────────────────────────────────────────
        danceability    = detect_danceability(y, sr)
        emotional_impact = detect_emotional_impact(aggressiveness, tension,
                                                    brightness, is_major)
        # Genre hint: use raw RMS as proxy for percussion density
        rms_proxy = float(librosa.feature.rms(y=y)[0].mean())
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                t = librosa.feature.rhythm.tempo(y=y, sr=sr)
            except AttributeError:
                t = librosa.beat.tempo(y=y, sr=sr)
        bpm_val = float(t[0]) if hasattr(t, '__iter__') else float(t)
        genre_hint = detect_genre_hint(y, sr, brightness, rms_proxy, bpm=bpm_val)

        return {
            "primary_mood":     primary_mood,
            "all_moods":        mood_scores,
            "is_major":         is_major,
            "aggressiveness":   round(float(aggressiveness), 3),
            "brightness":       round(float(brightness), 3),
            "tension":          round(float(tension), 3),
            "danceability":     danceability,
            "emotional_impact": emotional_impact,
            "genre_hint":       genre_hint,
        }
    except Exception as e:
        logger.error(f"Error classifying mood: {e}")
        return None


def analyze_mood_compatibility(mood1, mood2):
    """
    Analyze how compatible two moods are for transition.

    Incorporates the expanded mood set and danceability/emotional-impact proximity.

    Args:
        mood1, mood2: Output dicts from classify_mood()

    Returns:
        compatibility_score: 0-1, where 1 is very compatible
    """
    if mood1 is None or mood2 is None:
        return 0.5

    try:
        prim1 = mood1.get("primary_mood", "Chill")
        prim2 = mood2.get("primary_mood", "Chill")

        # Extended compatibility matrix (9 moods × 9 moods)
        # Format: (from, to) → 0-1 score
        C = {
            # same-mood diagonal = 1.0
            ("Dark",        "Dark"):        1.00,
            ("Dark",        "Euphoric"):    0.30,
            ("Dark",        "Melancholic"): 0.90,
            ("Dark",        "Aggressive"):  0.70,
            ("Dark",        "Chill"):       0.55,
            ("Dark",        "Driving"):     0.45,
            ("Dark",        "Romantic"):    0.35,
            ("Dark",        "Intense"):     0.65,
            ("Dark",        "Trance"):      0.75,

            ("Euphoric",    "Dark"):        0.30,
            ("Euphoric",    "Euphoric"):    1.00,
            ("Euphoric",    "Melancholic"): 0.40,
            ("Euphoric",    "Aggressive"):  0.55,
            ("Euphoric",    "Chill"):       0.70,
            ("Euphoric",    "Driving"):     0.85,
            ("Euphoric",    "Romantic"):    0.80,
            ("Euphoric",    "Intense"):     0.50,
            ("Euphoric",    "Trance"):      0.65,

            ("Melancholic", "Dark"):        0.90,
            ("Melancholic", "Euphoric"):    0.40,
            ("Melancholic", "Melancholic"): 1.00,
            ("Melancholic", "Aggressive"):  0.45,
            ("Melancholic", "Chill"):       0.80,
            ("Melancholic", "Driving"):     0.40,
            ("Melancholic", "Romantic"):    0.70,
            ("Melancholic", "Intense"):     0.45,
            ("Melancholic", "Trance"):      0.60,

            ("Aggressive",  "Dark"):        0.70,
            ("Aggressive",  "Euphoric"):    0.55,
            ("Aggressive",  "Melancholic"): 0.45,
            ("Aggressive",  "Aggressive"):  1.00,
            ("Aggressive",  "Chill"):       0.15,
            ("Aggressive",  "Driving"):     0.80,
            ("Aggressive",  "Romantic"):    0.20,
            ("Aggressive",  "Intense"):     0.90,
            ("Aggressive",  "Trance"):      0.40,

            ("Chill",       "Dark"):        0.55,
            ("Chill",       "Euphoric"):    0.70,
            ("Chill",       "Melancholic"): 0.80,
            ("Chill",       "Aggressive"):  0.15,
            ("Chill",       "Chill"):       1.00,
            ("Chill",       "Driving"):     0.30,
            ("Chill",       "Romantic"):    0.75,
            ("Chill",       "Intense"):     0.20,
            ("Chill",       "Trance"):      0.65,

            ("Driving",     "Dark"):        0.45,
            ("Driving",     "Euphoric"):    0.85,
            ("Driving",     "Melancholic"): 0.40,
            ("Driving",     "Aggressive"):  0.80,
            ("Driving",     "Chill"):       0.30,
            ("Driving",     "Driving"):     1.00,
            ("Driving",     "Romantic"):    0.45,
            ("Driving",     "Intense"):     0.75,
            ("Driving",     "Trance"):      0.70,

            ("Romantic",    "Dark"):        0.35,
            ("Romantic",    "Euphoric"):    0.80,
            ("Romantic",    "Melancholic"): 0.70,
            ("Romantic",    "Aggressive"):  0.20,
            ("Romantic",    "Chill"):       0.75,
            ("Romantic",    "Driving"):     0.45,
            ("Romantic",    "Romantic"):    1.00,
            ("Romantic",    "Intense"):     0.25,
            ("Romantic",    "Trance"):      0.60,

            ("Intense",     "Dark"):        0.65,
            ("Intense",     "Euphoric"):    0.50,
            ("Intense",     "Melancholic"): 0.45,
            ("Intense",     "Aggressive"):  0.90,
            ("Intense",     "Chill"):       0.20,
            ("Intense",     "Driving"):     0.75,
            ("Intense",     "Romantic"):    0.25,
            ("Intense",     "Intense"):     1.00,
            ("Intense",     "Trance"):      0.50,

            ("Trance",      "Dark"):        0.75,
            ("Trance",      "Euphoric"):    0.65,
            ("Trance",      "Melancholic"): 0.60,
            ("Trance",      "Aggressive"):  0.40,
            ("Trance",      "Chill"):       0.65,
            ("Trance",      "Driving"):     0.70,
            ("Trance",      "Romantic"):    0.60,
            ("Trance",      "Intense"):     0.50,
            ("Trance",      "Trance"):      1.00,
        }

        base = C.get((prim1, prim2), 0.5)

        # Adjustment: similarity of continuous features
        brightness_diff  = abs(mood1.get("brightness", 0.5)     - mood2.get("brightness", 0.5))
        aggressive_diff  = abs(mood1.get("aggressiveness", 0.5) - mood2.get("aggressiveness", 0.5))
        dance_diff       = abs(mood1.get("danceability", 50)     - mood2.get("danceability", 50)) / 100.0

        similarity = (1.0 - brightness_diff  * 0.15 -
                           aggressive_diff   * 0.15 -
                           dance_diff        * 0.10)

        final = base * 0.70 + similarity * 0.30
        return round(min(max(final, 0.0), 1.0), 3)
    except Exception as e:
        logger.error(f"Error analyzing mood compatibility: {e}")
        return 0.5
