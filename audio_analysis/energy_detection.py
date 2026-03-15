"""
Energy Level Detection - Analyzing Harmonic and Dynamic Energy in Tracks

This module detects the energy characteristics of audio files:
- Spectral brightness and intensity
- Dynamic range and loudness
- Energy envelope and peaks
- Spectral richness and complexity

Uses librosa for offline analysis.
"""

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 0-10 numeric energy scale with descriptors (per prompt Section B.4)
# ─────────────────────────────────────────────────────────────────────────────
_ENERGY_DESCRIPTORS = [
    (0.0, 0.08,  0,  "Ambient/Minimal"),
    (0.08, 0.18, 1,  "Sparse/Minimal"),
    (0.18, 0.28, 2,  "Subdued"),
    (0.28, 0.38, 3,  "Calm"),
    (0.38, 0.48, 4,  "Moderate"),
    (0.48, 0.56, 5,  "Balanced"),
    (0.56, 0.64, 6,  "Energetic"),
    (0.64, 0.72, 7,  "High Energy"),
    (0.72, 0.82, 8,  "Intense"),
    (0.82, 0.92, 9,  "Peak Energy"),
    (0.92, 1.01, 10, "Maximum Intensity"),
]


def _score_to_numeric(score):
    """Convert a 0-1 overall score to (numeric_score 0-10, descriptor str)."""
    for low, high, num, label in _ENERGY_DESCRIPTORS:
        if low <= score < high:
            return num, label
    return 10, "Maximum Intensity"


def detect_spectral_brightness(y, sr):
    """
    Detect how bright/brilliant a track sounds (high-frequency content).
    
    Bright sounds have more energy in high frequencies (e.g., cymbals, bright synths).
    Dark sounds have more energy in low frequencies (e.g., basses, sub-bass).
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        brightness_score: 0-1, where 1 is very bright (lots of high-freq content)
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Calculate spectral centroid (center of mass of spectrum)
        # Higher values = brighter sound
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        
        # Normalize to 0-1 range (Nyquist frequency = sr/2)
        nyquist = sr / 2
        brightness = spectral_centroid.mean() / nyquist
        
        return min(brightness, 1.0)
    except Exception as e:
        logger.error(f"Error detecting brightness: {e}")
        return None


def detect_loudness(y, sr):
    """
    Detect the overall loudness/intensity of the track.
    
    This uses RMS (Root Mean Square) energy to measure loudness.
    Higher values indicate louder, more intense tracks.
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        loudness_score: 0-1, normalized loudness level
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Calculate RMS energy
        rms_energy = librosa.feature.rms(y=y)[0]
        
        # Get max RMS energy and normalize
        max_energy = rms_energy.max()
        loudness = max_energy / (1.0 + 1e-10)  # Avoid division by zero
        
        # Normalize to 0-1 range
        return min(loudness, 1.0)
    except Exception as e:
        logger.error(f"Error detecting loudness: {e}")
        return None


def detect_energy_dynamics(y, sr):
    """
    Detect how energy varies throughout the track.
    
    Some tracks are steady (minimal variation), others have pronounced rises
    and falls (e.g., build-ups and breakdowns).
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        dict with:
        - dynamic_range: How much energy variation (0-1)
        - energy_curve: Overall trend (ascending, descending, stable)
        - peak_intensity: Strongest moment in the track
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Compute energy over time using STFT
        S = librosa.feature.melspectrogram(y=y, sr=sr)
        energy = np.sqrt((S ** 2).sum(axis=0))
        
        # Normalize
        energy = energy / (energy.max() + 1e-10)
        
        # Calculate dynamic range
        dynamic_range = (energy.max() - energy.min())
        
        # Detect trend (first half vs second half)
        mid = len(energy) // 2
        first_half_avg = energy[:mid].mean()
        second_half_avg = energy[mid:].mean()
        
        if second_half_avg > first_half_avg + 0.1:
            energy_curve = "ascending"  # Energy builds up
        elif first_half_avg > second_half_avg + 0.1:
            energy_curve = "descending"  # Energy decreases
        else:
            energy_curve = "stable"  # Consistent energy
        
        peak_intensity = energy.max()
        
        return {
            "dynamic_range": min(dynamic_range, 1.0),
            "energy_curve": energy_curve,
            "peak_intensity": min(peak_intensity, 1.0),
            "average_energy": float(energy.mean())
        }
    except Exception as e:
        logger.error(f"Error detecting dynamics: {e}")
        return None


def detect_beat_intensity(y, sr):
    """
    Detect the strength of the beat / kick drum impact.

    High beat intensity indicates powerful, punchy percussive elements
    typical of club tracks. This contributes 25% of the energy score.

    Args:
        y: Audio time series
        sr: Sample rate

    Returns:
        beat_intensity: 0-1 score
    """
    if not LIBROSA_AVAILABLE:
        return None

    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        # Normalise peak onset strength relative to overall signal level
        rms = librosa.feature.rms(y=y)[0].mean()
        peak_onset = onset_env.max()
        beat_intensity = peak_onset * rms / (peak_onset + rms + 1e-10)
        return min(float(beat_intensity), 1.0)
    except Exception as e:
        logger.error(f"Error detecting beat intensity: {e}")
        return None


def build_energy_timeline(y, sr, n_segments=10):
    """
    Build a coarse energy curve across the track (n_segments data points).

    Args:
        y: Audio time series
        sr: Sample rate
        n_segments: Number of equal-length segments to analyse

    Returns:
        list of floats (0-1) representing energy per segment
    """
    if not LIBROSA_AVAILABLE:
        return []

    try:
        seg_len = len(y) // max(n_segments, 1)
        timeline = []
        for i in range(n_segments):
            seg = y[i * seg_len: (i + 1) * seg_len]
            if len(seg) == 0:
                break
            rms = librosa.feature.rms(y=seg)[0]
            timeline.append(round(float(min(rms.mean(), 1.0)), 3))
        return timeline
    except Exception as e:
        logger.error(f"Error building energy timeline: {e}")
        return []


def detect_spectral_richness(y, sr):
    """
    Detect how complex/rich the harmonic content is.
    
    Dense tracks have more simultaneous frequency components.
    Minimal tracks have fewer, simpler sounds.
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        richness_score: 0-1, where 1 is very dense/complex
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Analyze spectral content using mel-scale spectrogram
        S = librosa.feature.melspectrogram(y=y, sr=sr)
        
        # Power to dB scale
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Count "active" frequency bands (those with significant energy)
        # Threshold: -40 dB below peak
        threshold = S_db.max() - 40
        active_bands = (S_db > threshold).sum(axis=0)
        
        # Average proportion of active bands
        richness = active_bands.mean() / S_db.shape[0]
        
        return min(richness, 1.0)
    except Exception as e:
        logger.error(f"Error detecting richness: {e}")
        return None


def classify_energy_level(y, sr):
    """
    Classify overall energy level into categories with a 0-10 numeric score.

    Multi-factor weighted calculation (based on prompt Section B.4):
      Spectral energy (frequency content)  30 %
      Dynamic range                        20 %
      Beat intensity / kick strength       25 %
      Percussion complexity                15 %
      Spectral richness                    10 %

    Args:
        y: Audio time series
        sr: Sample rate

    Returns:
        dict with:
          - level: "Low" | "Medium" | "High"
          - numeric_score: 0-10 integer
          - level_descriptor: human-readable label (e.g. "Balanced")
          - loudness: 0-1
          - brightness: "Dark" | "Neutral" | "Bright"
          - brightness_score: 0-1
          - density: "Minimal" | "Medium" | "Dense"
          - richness_score: 0-1
          - beat_intensity: 0-1
          - energy_curve: "ascending" | "descending" | "stable"
          - peak_intensity: 0-1
          - overall_score: 0-1 combined weighted score
          - energy_timeline: list of 10 energy values (0-1) across track
    """
    if not LIBROSA_AVAILABLE:
        return None

    try:
        loudness    = detect_loudness(y, sr)
        brightness  = detect_spectral_brightness(y, sr)
        richness    = detect_spectral_richness(y, sr)
        dynamics    = detect_energy_dynamics(y, sr)
        beat_int    = detect_beat_intensity(y, sr)
        timeline    = build_energy_timeline(y, sr, n_segments=10)

        if loudness is None or brightness is None:
            return None

        beat_int   = beat_int   if beat_int  is not None else 0.5
        richness   = richness   if richness  is not None else 0.5
        dyn_range  = dynamics["dynamic_range"] if dynamics else 0.5

        # Weighted overall score
        overall_score = (
            loudness   * 0.30 +
            dyn_range  * 0.20 +
            beat_int   * 0.25 +
            richness   * 0.15 +
            brightness * 0.10
        )
        overall_score = min(overall_score, 1.0)

        # Legacy level string
        if overall_score > 0.64:
            level = "High"
        elif overall_score > 0.38:
            level = "Medium"
        else:
            level = "Low"

        # 0-10 numeric
        numeric_score, level_descriptor = _score_to_numeric(overall_score)

        # Brightness classification
        if brightness > 0.65:
            brightness_class = "Bright"
        elif brightness > 0.35:
            brightness_class = "Neutral"
        else:
            brightness_class = "Dark"

        # Density classification
        if richness > 0.65:
            density = "Dense"
        elif richness > 0.35:
            density = "Medium"
        else:
            density = "Minimal"

        return {
            "level": level,
            "numeric_score": numeric_score,
            "level_descriptor": level_descriptor,
            "loudness": loudness,
            "brightness": brightness_class,
            "brightness_score": brightness,
            "density": density,
            "richness_score": richness,
            "beat_intensity": beat_int,
            "energy_curve": dynamics["energy_curve"] if dynamics else "unknown",
            "peak_intensity": dynamics["peak_intensity"] if dynamics else loudness,
            "overall_score": round(overall_score, 3),
            "energy_timeline": timeline,
        }
    except Exception as e:
        logger.error(f"Error classifying energy: {e}")
        return None


def analyze_energy_shift(y1, sr1, y2, sr2):
    """
    Analyze harmonic energy shift between two tracks.
    
    Useful for predicting transition smoothness.
    
    Args:
        y1, sr1: First track audio and sample rate
        y2, sr2: Second track audio and sample rate
    
    Returns:
        dict with:
        - brightness_shift: Change in brightness (-1 to 1)
        - loudness_shift: Change in loudness (-1 to 1)
        - density_shift: Change in density (-1 to 1)
        - transition_smoothness: 0-1 score for smooth transition
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        energy1 = classify_energy_level(y1, sr1)
        energy2 = classify_energy_level(y2, sr2)
        
        if energy1 is None or energy2 is None:
            return None
        
        brightness_shift = energy2["brightness_score"] - energy1["brightness_score"]
        loudness_shift = energy2["loudness"] - energy1["loudness"]
        density_shift = energy2["richness_score"] - energy1["richness_score"]
        
        # Smoothness: smaller shifts are smoother
        # Also factor in energy curves
        shift_magnitude = (abs(brightness_shift) + abs(loudness_shift) + abs(density_shift)) / 3
        smoothness = max(0, 1 - shift_magnitude)
        
        return {
            "brightness_shift": brightness_shift,
            "loudness_shift": loudness_shift,
            "density_shift": density_shift,
            "shift_magnitude": shift_magnitude,
            "transition_smoothness": smoothness
        }
    except Exception as e:
        logger.error(f"Error analyzing energy shift: {e}")
        return None
