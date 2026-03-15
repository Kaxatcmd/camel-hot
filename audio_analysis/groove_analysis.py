"""
Groove Analysis - Detecting Rhythm and Percussion Characteristics

This module analyzes groove patterns:
- Kick drum presence and regularity
- Percussion density (how busy the drums are)
- Swing detection (human-feel vs quantized)
- Groove type classification (Driving, Rolling, Minimal, Breaky)

Uses librosa's onset detection and rhythm analysis.
"""
import logging

logger = logging.getLogger(__name__)
try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def detect_onset_energy(y, sr):
    """
    Detect the strength and timing of percussion hits (onsets).
    
    Onsets are moments where a percussive sound starts.
    High onset energy = busier, more percussive track.
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        dict with:
        - onset_strength: 0-1, how pronounced the hit patterns are
        - onset_count: Number of detected onsets per second
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Detect onsets
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        # Find peaks in onset strength
        try:
            # Librosa 0.11+ requires all keyword arguments including wait and delta
            onset_frames = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.0, wait=10)
        except (TypeError, AttributeError):
            # Fallback: if peak_pick not available, use simple threshold
            onset_frames = np.where(onset_env > onset_env.mean())[0]
        
        # Overall strength
        onset_strength = onset_env.mean()
        
        # Duration-based count
        duration = librosa.get_duration(y=y, sr=sr)
        onset_count = len(onset_frames) / max(duration, 1.0)
        
        # Normalize
        onset_strength = min(onset_strength, 1.0)
        onset_count = min(onset_count / 4, 1.0)  # Normalize (4 onsets/sec = max)
        
        return {
            "onset_strength": onset_strength,
            "onset_count": onset_count,
            "onset_frames": len(onset_frames)
        }
    except Exception as e:
        logger.error(f"Error detecting onsets: {e}")
        return None


def detect_kick_presence(y, sr):
    """
    Detect presence of kick drum patterns.
    
    Kicks are typically in the 40-200 Hz range. Regular kick patterns
    indicate a driving, structured beat.
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        dict with:
        - kick_presence: 0-1, likelihood of kick drum presence
        - kick_regularity: 0-1, how regular/quantized the kicks are
        - kick_strength: 0-1, perceived loudness of kicks
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Isolate low-frequency content (kick range: 40-200 Hz)
        # Use high-pass filter to remove sub-bass, then analyze
        D = librosa.stft(y)
        magnitude = np.abs(D)
        
        # Focus on kick range (frequencies ~40-200 Hz)
        # STFT bin 0 is DC, bin frequency = sr / n_fft * bin_number
        # For 22050 Hz sample rate with 2048 STFT bins:
        # Each bin ≈ 10.7 Hz
        
        # Calculate energy in kick range (bins for ~50-300 Hz)
        n_fft = D.shape[0]
        bin_50hz = int(50 * n_fft / sr)
        bin_300hz = int(300 * n_fft / sr)
        
        if bin_300hz > n_fft:
            bin_300hz = n_fft
        
        kick_band = magnitude[bin_50hz:bin_300hz, :].mean(axis=0)
        kick_strength_score = np.sqrt(kick_band).mean()
        kick_strength_score = min(kick_strength_score, 1.0)
        
        # Detect regularity: consistent kick hits every ~0.5 seconds (house kick)
        # or more complex patterns
        hop_length = len(D) // magnitude.shape[1]
        time_per_frame = hop_length / sr
        
        # Look for periodicity in kick_band
        # Simple check: high variance in peaks suggests regularity
        if len(kick_band) > 20:
            try:
                # Librosa 0.11+ requires all keyword arguments including wait and delta
                kick_peaks = librosa.util.peak_pick(kick_band, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.0, wait=10)
            except (TypeError, AttributeError):
                # Fallback: if peak_pick not available, use simple threshold
                kick_peaks = np.where(kick_band > kick_band.mean())[0]
            
            if len(kick_peaks) > 2:
                peak_intervals = np.diff(kick_peaks) * time_per_frame
                # Check if intervals are relatively consistent (low coefficient of variation)
                regularity = 1.0 - (np.std(peak_intervals) / (np.mean(peak_intervals) + 0.1))
                kick_regularity = max(0, min(regularity, 1.0))
            else:
                kick_regularity = 0.3
        else:
            kick_regularity = 0.5
        
        kick_presence = kick_strength_score
        
        return {
            "kick_presence": kick_presence,
            "kick_strength": kick_strength_score,
            "kick_regularity": kick_regularity
        }
    except Exception as e:
        logger.error(f"Error detecting kicks: {e}")
        return None


def detect_percussion_density(y, sr):
    """
    Detect how busy/complex the percussion is.
    
    Dense: lots of hi-hats, percussion layers
    Minimal: simple, sparse drums
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        percussion_density: 0-1, where 1 is very busy drums
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Analyze high-frequency content (hi-hats, cymbals: 5kHz+)
        D = librosa.stft(y)
        magnitude = np.abs(D)
        
        n_fft = D.shape[0]
        bin_5khz = int(5000 * n_fft / sr)
        
        # Energy in high-frequency range
        if bin_5khz < n_fft:
            high_freq = magnitude[bin_5khz:, :].mean(axis=0)
            density = high_freq.mean()
            density = min(density, 1.0)
        else:
            density = 0.3
        
        return density
    except Exception as e:
        logger.error(f"Error detecting percussion density: {e}")
        return 0.5


def detect_swing(y, sr):
    """
    Detect if the track has swing/groove feel (human-like timing).
    
    Perfectly quantized beats have zero swing.
    Real groove has slight timing variations (swing).
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        swing_score: 0-1, where 1 is very swung (loose, human feel)
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Detect beats/onsets
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        try:
            # Librosa 0.11+ requires all keyword arguments including wait and delta
            onset_frames = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.0, wait=10)
        except (TypeError, AttributeError):
            # Fallback: if peak_pick not available, use simple threshold
            onset_frames = np.where(onset_env > onset_env.mean())[0]
        
        if len(onset_frames) < 4:
            return 0.5  # Not enough data
        
        # Convert frames to time
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        
        # Calculate intervals between onsets
        intervals = np.diff(onset_times)
        
        if len(intervals) < 3:
            return 0.5
        
        # Perfect quantization = all intervals equal
        # Swing = slight variations in intervals
        # Coefficient of variation of intervals
        mean_interval = intervals.mean()
        std_interval = intervals.std()
        cv = std_interval / (mean_interval + 0.001)
        
        # Map CV to swing score (0-1)
        # CV ~0.02-0.05 is typical human swing
        # CV < 0.01 is very quantized
        # CV > 0.1 is very loose or irregular
        
        if cv < 0.02:
            swing = 0.1  # Very quantized
        elif cv < 0.05:
            swing = 0.5 + (cv - 0.02) * 10  # Moderate swing
        elif cv < 0.15:
            swing = 0.8  # Strong swing
        else:
            swing = 0.9  # Very loose
        
        swing = min(swing, 1.0)
        
        return swing
    except Exception as e:
        logger.error(f"Error detecting swing: {e}")
        return 0.5


def measure_swing_percentage(y, sr):
    """
    Measure swing as a 0-100 percentage (0 = perfectly quantised, 100 = maximum swing).

    Analyses the ratio of alternating inter-onset intervals in 8th-note pairs.
    A 50 % swing (straight 8ths) maps to ~0 %, while jazz triplet swing (~67 %) maps to ~100 %.

    Returns:
        swing_pct: float 0-100
    """
    if not LIBROSA_AVAILABLE:
        return 50.0

    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        try:
            onset_frames = librosa.util.peak_pick(onset_env,
                           pre_max=3, post_max=3, pre_avg=3, post_avg=3,
                           delta=0.0, wait=10)
        except (TypeError, AttributeError):
            onset_frames = np.where(onset_env > onset_env.mean())[0]

        if len(onset_frames) < 6:
            return 50.0

        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        intervals = np.diff(onset_times)

        # Pair up consecutive intervals and look at long/short ratio
        pairs = [(intervals[i], intervals[i + 1]) for i in range(0, len(intervals) - 1, 2)]
        if not pairs:
            return 50.0

        ratios = [max(a, b) / (min(a, b) + 1e-6) for a, b in pairs]
        mean_ratio = np.mean(ratios)

        # Straight 8ths → ratio ≈ 1.0 → 0 % swing
        # Triplet swing → ratio ≈ 2.0 → ~80-100 % swing
        swing_pct = min(max((mean_ratio - 1.0) / 1.0 * 100, 0), 100)
        return round(float(swing_pct), 1)
    except Exception as e:
        logger.error(f"Error measuring swing percentage: {e}")
        return 50.0


def measure_syncopation(y, sr):
    """
    Measure syncopation level on a 0-100 scale.

    Higher values indicate more offbeat/syncopated rhythms.
    Analyses the proportion of onset energy falling between primary beat subdivisions.

    Returns:
        syncopation_score: int 0-100
    """
    if not LIBROSA_AVAILABLE:
        return 50

    try:
        import warnings
        # Get beat positions
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                tempo_arr = librosa.feature.rhythm.tempo(y=y, sr=sr)
            except AttributeError:
                tempo_arr = librosa.beat.tempo(y=y, sr=sr)

        bpm = float(tempo_arr[0]) if hasattr(tempo_arr, '__iter__') else float(tempo_arr)
        beat_period = 60.0 / max(bpm, 1)

        # Strong beats are at multiples of beat_period; weak offbeats halfway between
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        times = librosa.times_like(onset_env, sr=sr)

        on_beat_energy = 0.0
        off_beat_energy = 0.0
        for t, strength in zip(times, onset_env):
            phase = (t % beat_period) / beat_period  # 0-1 within beat
            if phase < 0.15 or phase > 0.85:  # near beat — on-beat
                on_beat_energy += strength
            elif 0.4 < phase < 0.6:  # halfway — offbeat
                off_beat_energy += strength

        total = on_beat_energy + off_beat_energy + 1e-10
        off_ratio = off_beat_energy / total
        syncopation_score = int(min(off_ratio * 200, 100))  # scale 0.5 → 100
        return syncopation_score
    except Exception as e:
        logger.error(f"Error measuring syncopation: {e}")
        return 50


def classify_groove_family(kick_presence, kick_regularity, perc_density, swing_pct):
    """
    Classify groove into a musical-style family.

    Families: Electronic, Funk, Jazz, Latin, Tribal, Minimal, Acoustic

    Returns:
        groove_family: str
    """
    # Electronic: quantised kick (regularity > 0.7), medium-dense hi-hats
    if kick_regularity > 0.70 and kick_presence > 0.55 and perc_density > 0.40 and swing_pct < 30:
        return "Electronic"

    # Funk: syncopated kick, moderate density, some swing
    if kick_presence > 0.50 and 20 <= swing_pct <= 65 and perc_density > 0.45:
        return "Funk"

    # Jazz: high swing, sparse-to-medium density
    if swing_pct >= 55 and perc_density < 0.60:
        return "Jazz"

    # Latin: regular kick, medium density, moderate swing
    if kick_regularity > 0.55 and 25 <= swing_pct <= 60 and kick_presence > 0.40:
        return "Latin"

    # Tribal: dense percussion, lower kick prominence
    if perc_density > 0.68 and kick_presence < 0.55:
        return "Tribal"

    # Minimal: sparse everything
    if perc_density < 0.30 and kick_presence < 0.40:
        return "Minimal"

    # Acoustic / other
    return "Acoustic"


def _groove_complexity(kick_regularity, perc_density, syncopation, swing_pct):
    """Return a 0-10 complexity score for the groove."""
    raw = (
        (1.0 - kick_regularity) * 2.5 +  # irregular kicks add complexity
        perc_density           * 2.5 +
        (syncopation / 100)    * 2.5 +
        (swing_pct / 100)      * 2.5
    )
    return round(min(raw, 10.0), 1)


def classify_groove_type(y, sr):
    """
    Classify groove with extended attributes including family, swing, syncopation,
    and complexity.

    Args:
        y: Audio time series
        sr: Sample rate

    Returns:
        dict with:
          - type: Driving | Rolling | Minimal | Breaky
          - groove_family: Electronic | Funk | Jazz | Latin | Tribal | Minimal | Acoustic
          - kick_presence: 0-1
          - kick_regularity: 0-1
          - percussion_density: 0-1
          - swing: 0-1  (normalised, backward-compat)
          - swing_percentage: 0-100 swing amount
          - syncopation_score: 0-100
          - complexity_score: 0-10
          - onset_strength: 0-1
    """
    if not LIBROSA_AVAILABLE:
        return None

    try:
        kick_info    = detect_kick_presence(y, sr)
        perc_density = detect_percussion_density(y, sr)
        swing        = detect_swing(y, sr)
        onset_info   = detect_onset_energy(y, sr)
        swing_pct    = measure_swing_percentage(y, sr)
        syncopation  = measure_syncopation(y, sr)

        if kick_info is None or onset_info is None:
            return None

        kick_presence    = kick_info["kick_presence"]
        kick_regularity  = kick_info["kick_regularity"]
        onset_strength   = onset_info["onset_strength"]
        perc_density     = perc_density if perc_density is not None else 0.5

        # ── Groove type ───────────────────────────────────────────────────────
        if kick_presence > 0.6 and kick_regularity > 0.6:
            groove_type = "Driving" if perc_density > 0.6 else "Rolling"
        elif onset_strength > 0.6 and perc_density < 0.4:
            groove_type = "Breaky"
        elif perc_density < 0.3:
            groove_type = "Minimal"
        else:
            groove_type = "Rolling"

        # ── Extended attributes ───────────────────────────────────────────────
        groove_family   = classify_groove_family(kick_presence, kick_regularity,
                                                  perc_density, swing_pct)
        complexity      = _groove_complexity(kick_regularity, perc_density,
                                              syncopation, swing_pct)

        return {
            "type":              groove_type,
            "groove_family":     groove_family,
            "kick_presence":     kick_presence,
            "kick_regularity":   kick_regularity,
            "percussion_density": perc_density,
            "swing":             swing,
            "swing_percentage":  swing_pct,
            "syncopation_score": syncopation,
            "complexity_score":  complexity,
            "onset_strength":    onset_strength,
        }
    except Exception as e:
        logger.error(f"Error classifying groove: {e}")
        return None


def analyze_groove_compatibility(groove1, groove2):
    """
    Analyze how compatible two groove types are for transition.

    Incorporates groove family, swing difference, and syncopation similarity.

    Args:
        groove1, groove2: Output dicts from classify_groove_type()

    Returns:
        compatibility_score: 0-1, where 1 is very compatible
    """
    if groove1 is None or groove2 is None:
        return 0.5

    try:
        type1   = groove1.get("type", "Rolling")
        type2   = groove2.get("type", "Rolling")
        family1 = groove1.get("groove_family", "Electronic")
        family2 = groove2.get("groove_family", "Electronic")

        # Base compatibility by groove type
        compatibility_map = {
            ("Driving",  "Driving"):  1.0,
            ("Driving",  "Rolling"):  0.85,
            ("Driving",  "Breaky"):   0.40,
            ("Driving",  "Minimal"):  0.30,
            ("Rolling",  "Driving"):  0.85,
            ("Rolling",  "Rolling"):  1.0,
            ("Rolling",  "Breaky"):   0.70,
            ("Rolling",  "Minimal"):  0.50,
            ("Breaky",   "Driving"):  0.40,
            ("Breaky",   "Rolling"):  0.70,
            ("Breaky",   "Breaky"):   0.95,
            ("Breaky",   "Minimal"):  0.80,
            ("Minimal",  "Driving"):  0.30,
            ("Minimal",  "Rolling"):  0.50,
            ("Minimal",  "Breaky"):   0.80,
            ("Minimal",  "Minimal"):  1.0,
        }

        # Family affinity bonus (same or related family)
        same_family_bonus = 0.10 if family1 == family2 else 0.0
        related_families = {frozenset({"Electronic", "Funk"}),
                            frozenset({"Funk", "Latin"}),
                            frozenset({"Jazz", "Acoustic"})}
        if frozenset({family1, family2}) in related_families:
            same_family_bonus = 0.05

        base = compatibility_map.get((type1, type2), 0.5)

        # Penalise large swing & density differences
        density_diff  = abs(groove1.get("percussion_density", 0.5) -
                            groove2.get("percussion_density", 0.5))
        swing_diff    = abs(groove1.get("swing_percentage",   50) -
                            groove2.get("swing_percentage",   50)) / 100.0
        synco_diff    = abs(groove1.get("syncopation_score",  50) -
                            groove2.get("syncopation_score",  50)) / 100.0

        similarity_factor = (1.0 - density_diff * 0.15 -
                                   swing_diff   * 0.10 -
                                   synco_diff   * 0.10)

        final = base * 0.65 + similarity_factor * 0.25 + same_family_bonus
        return round(min(max(final, 0.0), 1.0), 3)
    except Exception as e:
        logger.error(f"Error analyzing groove compatibility: {e}")
        return 0.5
