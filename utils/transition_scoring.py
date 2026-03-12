"""
Transition Scoring Engine - Intelligent Track Compatibility Analysis

This engine scores how well two tracks will transition together by analyzing:
- Harmonic compatibility (key matching via Camelot)
- Energy shift smoothness
- Groove compatibility
- Mood alignment
- BPM proximity

Provides comprehensive transition scores and recommendations.
"""

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

from audio_analysis.energy_detection import classify_energy_level, analyze_energy_shift
from audio_analysis.groove_analysis import classify_groove_type, analyze_groove_compatibility
from audio_analysis.mood_classification import classify_mood, analyze_mood_compatibility
from utils.camelot_map import is_compatible_keys, get_compatible_keys


def score_harmonic_compatibility(camelot1, camelot2):
    """
    Score how harmonically compatible two keys are.
    
    Uses Camelot wheel rules for harmonic mixing.
    
    Args:
        camelot1, camelot2: Camelot notation keys (e.g., "8A", "9B")
    
    Returns:
        score: 0-1, where 1 is perfect harmonic match
    """
    try:
        if camelot1 == "Unknown" or camelot2 == "Unknown":
            return 0.5
        
        # Check direct compatibility
        if is_compatible_keys(camelot1, camelot2):
            return 1.0
        
        # Check near-compatible (1 semitone or classic distance)
        compatible_list = get_compatible_keys(camelot1)
        if camelot2 in compatible_list:
            return 1.0
        
        # Extract number and letter
        try:
            num1 = int(camelot1[:-1]) if camelot1[:-1] else 1
            letter1 = camelot1[-1]
            num2 = int(camelot2[:-1]) if camelot2[:-1] else 1
            letter2 = camelot2[-1]
        except:
            return 0.5
        
        # Same number = relative minor/major (good)
        if num1 == num2:
            return 0.85
        
        # Adjacent numbers = 5th relationship (good)
        if abs(num1 - num2) == 1:
            if letter1 == letter2:
                return 0.75
            else:
                return 0.65
        
        # Same letter = parallel major/minor (okay)
        if letter1 == letter2 and abs(num1 - num2) == 0:
            return 0.85
        
        # Different number and letter = mixed (weak)
        if abs(num1 - num2) <= 2:
            return 0.4
        
        # Far apart
        return 0.2
    
    except Exception as e:
        print(f"Error scoring harmonic compatibility: {e}")
        return 0.5


def score_bpm_compatibility(bpm1, bpm2, tolerance_percent=10):
    """
    Score how compatible two BPMs are.
    
    Similar BPMs are easiest, but half/double BPM is also good.
    
    Args:
        bpm1, bpm2: Beats per minute
        tolerance_percent: Allowed difference percentage (default 10%)
    
    Returns:
        score: 0-1, where 1 is perfect BPM match
    """
    if bpm1 is None or bpm2 is None:
        return 0.5
    
    try:
        # Calculate percentage difference
        diff_percent = abs(bpm1 - bpm2) / max(bpm1, bpm2) * 100
        
        # Same BPM
        if diff_percent < tolerance_percent:
            return 1.0
        
        # Check half/double BPM (both valid in DJ mixing)
        ratio = bpm2 / bpm1
        if 1.9 < ratio < 2.1:  # Double tempo
            return 0.9
        if 0.45 < ratio < 0.55:  # Half tempo
            return 0.9
        
        # Within 20% = still good
        if diff_percent < 20:
            return 0.8 - (diff_percent - tolerance_percent) * 0.03
        
        # Within 40% = moderate
        if diff_percent < 40:
            return 0.5 - (diff_percent - 20) * 0.015
        
        # Beyond 40% = poor
        return max(0.1, 0.35 - (diff_percent - 40) * 0.01)
    
    except Exception as e:
        print(f"Error scoring BPM compatibility: {e}")
        return 0.5


def calculate_transition_score(track1_analysis, track2_analysis):
    """
    Calculate comprehensive transition score between two tracks.
    
    Args:
        track1_analysis: Dict from full_track_analysis()
        track2_analysis: Dict from full_track_analysis()
    
    Returns:
        dict with:
        - overall_score: 0-1 combined compatibility
        - harmonic_score: Camelot wheel compatibility
        - energy_score: Energy shift smoothness
        - groove_score: Rhythm pattern compatibility
        - mood_score: Emotional alignment
        - bpm_score: Tempo compatibility
        - recommendation: Text recommendation
        - notes: Detailed notes about the transition
    """
    if track1_analysis is None or track2_analysis is None:
        return {
            "overall_score": 0.0,
            "recommendation": "Insufficient data for analysis"
        }
    
    try:
        # Get component scores
        harmonic_score = score_harmonic_compatibility(
            track1_analysis.get("camelot", "Unknown"),
            track2_analysis.get("camelot", "Unknown")
        )
        
        energy_score = 1.0
        if track1_analysis.get("energy"):
            track1_energy = track1_analysis.get("energy", {})
            track2_energy = track2_analysis.get("energy", {})
            if track1_energy and track2_energy:
                energy_shift = abs(track1_energy.get("overall_score", 0.5) -
                                   track2_energy.get("overall_score", 0.5))
                energy_score = max(0.4, 1.0 - energy_shift * 0.4)
        
        groove_score = 0.5
        if track1_analysis.get("groove") and track2_analysis.get("groove"):
            groove_score = analyze_groove_compatibility(
                track1_analysis["groove"],
                track2_analysis["groove"]
            )
        
        mood_score = 0.5
        if track1_analysis.get("mood") and track2_analysis.get("mood"):
            mood_score = analyze_mood_compatibility(
                track1_analysis["mood"],
                track2_analysis["mood"]
            )
        
        bpm_score = score_bpm_compatibility(
            track1_analysis.get("bpm"),
            track2_analysis.get("bpm")
        )
        
        # Weighted average
        overall_score = (
            harmonic_score * 0.25 +
            energy_score * 0.20 +
            groove_score * 0.20 +
            mood_score * 0.20 +
            bpm_score * 0.15
        )
        
        # Generate recommendation
        if overall_score > 0.85:
            recommendation = "🟢 Excellent transition"
        elif overall_score > 0.70:
            recommendation = "🟢 Good transition"
        elif overall_score > 0.55:
            recommendation = "🟡 Acceptable transition"
        elif overall_score > 0.40:
            recommendation = "🟠 Possible with care"
        else:
            recommendation = "🔴 Difficult transition"
        
        # Generate notes
        notes = []
        
        if harmonic_score > 0.8:
            notes.append("✓ Harmonic compatibility excellent")
        elif harmonic_score > 0.6:
            notes.append("~ Harmonic compatibility good")
        else:
            notes.append("✗ Harmonic compatibility weak - consider pitch shift")
        
        if energy_score > 0.8:
            notes.append("✓ Energy levels similar")
        elif energy_score > 0.6:
            notes.append("~ Slight energy shift needed")
        else:
            notes.append("✗ Large energy difference - use EQ")
        
        if groove_score > 0.8:
            notes.append("✓ Groove patterns compatible")
        elif groove_score > 0.6:
            notes.append("~ Similar groove types")
        else:
            notes.append("✗ Groove change required - plan transition")
        
        if mood_score > 0.8:
            notes.append("✓ Moods align well")
        elif mood_score > 0.6:
            notes.append("~ Mood shift present")
        else:
            notes.append("✗ Significant mood change - build up gradually")
        
        if bpm_score > 0.85:
            notes.append("✓ BPM perfectly matched")
        elif bpm_score > 0.7:
            notes.append("✓ BPM well matched")
        elif bpm_score > 0.5:
            notes.append("~ BPM adjustment needed")
        else:
            notes.append("✗ Large BPM difference")
        
        return {
            "overall_score": min(overall_score, 1.0),
            "harmonic_score": harmonic_score,
            "energy_score": energy_score,
            "groove_score": groove_score,
            "mood_score": mood_score,
            "bpm_score": bpm_score,
            "recommendation": recommendation,
            "notes": notes
        }
    
    except Exception as e:
        print(f"Error calculating transition score: {e}")
        return {
            "overall_score": 0.0,
            "recommendation": f"Error: {str(e)}"
        }


def find_best_transitions_for_track(track_analysis, candidate_tracks):
    """
    Find the best transitions from one track to a list of candidates.
    
    Args:
        track_analysis: Dict from full_track_analysis() for source track
        candidate_tracks: List of dicts from full_track_analysis()
    
    Returns:
        Sorted list of (score, index, recommendation) tuples
    """
    results = []
    
    for idx, candidate in enumerate(candidate_tracks):
        transition = calculate_transition_score(track_analysis, candidate)
        results.append({
            "index": idx,
            "score": transition["overall_score"],
            "recommendation": transition.get("recommendation", "Unknown"),
            "details": transition
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results


def full_track_analysis(file_path):
    """
    Complete analysis of a track including all features for transitions.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Comprehensive analysis dict with all features
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Load audio
        y, sr = librosa.load(file_path, duration=60)
        
        # Import from key_detection to get basic analysis
        from audio_analysis.key_detection import analyze_track as basic_analyze
        
        basic_info = basic_analyze(file_path)
        
        # Add advanced features
        energy = classify_energy_level(y, sr)
        groove = classify_groove_type(y, sr)
        mood = classify_mood(y, sr)
        
        # Combine into comprehensive analysis
        analysis = {
            **basic_info,
            "energy": energy,
            "groove": groove,
            "mood": mood
        }
        
        return analysis
    
    except Exception as e:
        print(f"Error in full track analysis: {e}")
        return None
