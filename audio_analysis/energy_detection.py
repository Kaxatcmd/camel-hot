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
            "average_energy": energy.mean()
        }
    except Exception as e:
        logger.error(f"Error detecting dynamics: {e}")
        return None


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
    Classify overall energy level into categories.
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        dict with:
        - level: Low, Medium, High
        - brightness: Dark, Neutral, Bright
        - density: Minimal, Medium, Dense
        - overall_score: 0-1 combined energy score
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        loudness = detect_loudness(y, sr)
        brightness = detect_spectral_brightness(y, sr)
        richness = detect_spectral_richness(y, sr)
        dynamics = detect_energy_dynamics(y, sr)
        
        if loudness is None or brightness is None:
            return None
        
        # Classify energy level
        if loudness > 0.7:
            level = "High"
        elif loudness > 0.4:
            level = "Medium"
        else:
            level = "Low"
        
        # Classify brightness
        if brightness > 0.65:
            brightness_class = "Bright"
        elif brightness > 0.35:
            brightness_class = "Neutral"
        else:
            brightness_class = "Dark"
        
        # Classify density
        if richness > 0.65:
            density = "Dense"
        elif richness > 0.35:
            density = "Medium"
        else:
            density = "Minimal"
        
        # Combined score
        overall_score = (loudness * 0.4 + brightness * 0.3 + richness * 0.3)
        
        return {
            "level": level,
            "loudness": loudness,
            "brightness": brightness_class,
            "brightness_score": brightness,
            "density": density,
            "richness_score": richness,
            "energy_curve": dynamics["energy_curve"] if dynamics else "unknown",
            "peak_intensity": dynamics["peak_intensity"] if dynamics else loudness,
            "overall_score": overall_score
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
