"""
Mood Classification - Detecting Emotional Character of Tracks

This module classifies track mood based on:
- Major vs Minor tonality
- Spectral brightness (dark = less bright, euphoric = bright)
- Aggressiveness (attack/intensity of sounds)
- Harmonic tension (dissonance vs consonance)

Mood categories: Dark, Euphoric, Melancholic, Aggressive, Chill, Driving
"""

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


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


def classify_mood(y, sr):
    """
    Classify track mood into categories.
    
    Mood classes: Dark, Euphoric, Melancholic, Aggressive, Chill, Driving
    
    Args:
        y: Audio time series
        sr: Sample rate
    
    Returns:
        dict with:
        - primary_mood: Most likely mood
        - all_moods: Scores for all mood categories
        - is_major: Whether track is in major key
        - aggressiveness: 0-1 score
        - brightness: 0-1 score
        - tension: 0-1 score
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        major_info = detect_major_minor(y, sr)
        aggressiveness = detect_aggressiveness(y, sr)
        tension = detect_harmonic_tension(y, sr)
        brightness = detect_brightness(y, sr)
        
        if major_info is None:
            return None
        
        is_major = major_info["is_major"]
        
        # Initialize mood scores
        mood_scores = {
            "Dark": 0.0,
            "Euphoric": 0.0,
            "Melancholic": 0.0,
            "Aggressive": 0.0,
            "Chill": 0.0,
            "Driving": 0.0
        }
        
        # Classification logic
        
        # DARK: Minor, low brightness, high tension
        dark_score = (
            (0.5 if not is_major else 0) +  # Minor is darker
            (1.0 - brightness) * 0.5 +       # Low brightness
            tension * 0.3                     # Some tension
        ) / 2.5
        mood_scores["Dark"] = dark_score
        
        # EUPHORIC: Major, high brightness, low tension
        euphoric_score = (
            (0.5 if is_major else 0) +      # Major is euphoric
            brightness * 0.5 +               # High brightness
            (1.0 - tension) * 0.3            # Low tension/harmony
        ) / 2.5
        mood_scores["Euphoric"] = euphoric_score
        
        # MELANCHOLIC: Minor, low-medium brightness, medium tension
        melancholic_score = (
            (0.5 if not is_major else 0) +  # Minor scale
            (1.0 - brightness) * 0.3 +      # Somewhat dark
            tension * 0.5 * (1.0 - aggressiveness)  # Sad, not aggressive
        ) / 2.5
        mood_scores["Melancholic"] = melancholic_score
        
        # AGGRESSIVE: High aggressiveness, high tension, any tonality
        aggressive_score = (
            aggressiveness * 0.6 +           # Very aggressive
            tension * 0.4                    # High tension
        ) / 2.0
        mood_scores["Aggressive"] = aggressive_score
        
        # CHILL: Low aggressiveness, any tonality, low tension, medium brightness
        chill_score = (
            (1.0 - aggressiveness) * 0.4 +  # Not aggressive
            (1.0 - tension) * 0.3 +          # Relaxed harmony
            (1.0 - abs(brightness - 0.5)) * 0.3  # Medium brightness
        ) / 2.0
        mood_scores["Chill"] = chill_score
        
        # DRIVING: Could be major or minor, high energy, rhythmic
        # (determined by energy level in other modules)
        driving_score = (
            brightness * 0.3 +               # Some brightness
            aggressiveness * 0.4 +           # Some intensity
            max(0, 1.0 - tension) * 0.3     # Forward momentum
        ) / 2.0
        mood_scores["Driving"] = driving_score
        
        # Normalize scores
        total = sum(mood_scores.values())
        if total > 0:
            for mood in mood_scores:
                mood_scores[mood] = mood_scores[mood] / (total + 1e-10)
        
        # Get primary mood
        primary_mood = max(mood_scores, key=mood_scores.get)
        
        return {
            "primary_mood": primary_mood,
            "all_moods": mood_scores,
            "is_major": is_major,
            "aggressiveness": min(aggressiveness, 1.0),
            "brightness": brightness,
            "tension": tension
        }
    except Exception as e:
        logger.error(f"Error classifying mood: {e}")
        return None


def analyze_mood_compatibility(mood1, mood2):
    """
    Analyze how compatible two moods are for transition.
    
    Args:
        mood1, mood2: Output dicts from classify_mood()
    
    Returns:
        compatibility_score: 0-1, where 1 is very compatible
    """
    if mood1 is None or mood2 is None:
        return 0.5
    
    try:
        prim1 = mood1["primary_mood"]
        prim2 = mood2["primary_mood"]
        
        # Mood compatibility matrix
        compatibility_map = {
            ("Dark", "Dark"): 1.0,
            ("Dark", "Euphoric"): 0.3,
            ("Dark", "Melancholic"): 0.9,
            ("Dark", "Aggressive"): 0.7,
            ("Dark", "Chill"): 0.6,
            ("Dark", "Driving"): 0.5,
            
            ("Euphoric", "Dark"): 0.3,
            ("Euphoric", "Euphoric"): 1.0,
            ("Euphoric", "Melancholic"): 0.4,
            ("Euphoric", "Aggressive"): 0.6,
            ("Euphoric", "Chill"): 0.7,
            ("Euphoric", "Driving"): 0.85,
            
            ("Melancholic", "Dark"): 0.9,
            ("Melancholic", "Euphoric"): 0.4,
            ("Melancholic", "Melancholic"): 1.0,
            ("Melancholic", "Aggressive"): 0.5,
            ("Melancholic", "Chill"): 0.8,
            ("Melancholic", "Driving"): 0.45,
            
            ("Aggressive", "Dark"): 0.7,
            ("Aggressive", "Euphoric"): 0.6,
            ("Aggressive", "Melancholic"): 0.5,
            ("Aggressive", "Aggressive"): 1.0,
            ("Aggressive", "Chill"): 0.2,
            ("Aggressive", "Driving"): 0.8,
            
            ("Chill", "Dark"): 0.6,
            ("Chill", "Euphoric"): 0.7,
            ("Chill", "Melancholic"): 0.8,
            ("Chill", "Aggressive"): 0.2,
            ("Chill", "Chill"): 1.0,
            ("Chill", "Driving"): 0.3,
            
            ("Driving", "Dark"): 0.5,
            ("Driving", "Euphoric"): 0.85,
            ("Driving", "Melancholic"): 0.45,
            ("Driving", "Aggressive"): 0.8,
            ("Driving", "Chill"): 0.3,
            ("Driving", "Driving"): 1.0,
        }
        
        key = (prim1, prim2)
        base_compatibility = compatibility_map.get(key, 0.5)
        
        # Adjust based on brightness and aggressiveness similarity
        brightness_diff = abs(mood1["brightness"] - mood2["brightness"])
        aggressive_diff = abs(mood1["aggressiveness"] - mood2["aggressiveness"])
        
        # Similarity bonus
        similarity_bonus = (1.0 - brightness_diff * 0.2) * (1.0 - aggressive_diff * 0.2)
        
        final_score = base_compatibility * 0.7 + similarity_bonus * 0.3
        
        return min(final_score, 1.0)
    except Exception as e:
        logger.error(f"Error analyzing mood compatibility: {e}")
        return 0.5
