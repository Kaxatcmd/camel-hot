"""
Transition Scoring Engine - Intelligent Track Compatibility Analysis

Scores how well two tracks will transition together by analysing:
  - Harmonic compatibility (Camelot wheel, distance scoring)
  - Energy shift smoothness
  - Groove compatibility (family + swing + syncopation)
  - Mood alignment
  - BPM proximity

Scores are on a 0-100 integer scale.
Provides comprehensive transition notes and technique suggestions.
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
from utils.camelot_map import (is_compatible_keys, get_compatible_keys,
                                get_harmonic_compatibility_score,
                                get_transition_reasoning)


def score_harmonic_compatibility(camelot1, camelot2):
    """
    Score how harmonically compatible two keys are (0-1, backward-compat).

    Internally uses the new 0-100 scoring from camelot_map and normalises.

    Args:
        camelot1, camelot2: Camelot notation keys (e.g., "8A", "9B")

    Returns:
        score: 0-1 float
    """
    try:
        if camelot1 == "Unknown" or camelot2 == "Unknown":
            return 0.5
        result = get_harmonic_compatibility_score(camelot1, camelot2)
        return result["score"] / 100.0
    except Exception as e:
        print(f"Error scoring harmonic compatibility: {e}")
        return 0.5


def score_bpm_compatibility(bpm1, bpm2, tolerance_percent=5):
    """
    Score BPM compatibility on a finer 0.0-1.0 scale.

    Scoring bands:
      0 BPM diff            → 1.00 (perfect)
      ≤ 1 BPM               → 0.98
      ≤ 3 BPM               → 0.92
      ≤ 5 BPM               → 0.85
      ≤ 8 BPM               → 0.75
      Half/double time       → 0.78
      ≤ 15 BPM              → 0.60
      ≤ 25 BPM              → 0.40
      > 25 BPM              → 0.15-0.30

    Args:
        bpm1, bpm2: Beats per minute
        tolerance_percent: Ignored; kept for backward compatibility

    Returns:
        score: 0-1 float
    """
    if bpm1 is None or bpm2 is None:
        return 0.5

    try:
        diff = abs(bpm1 - bpm2)

        # Half/double time check
        for ratio in (2.0, 0.5):
            if abs(bpm2 / bpm1 - ratio) < 0.06:
                return 0.78

        if diff == 0:
            return 1.00
        if diff <= 1:
            return 0.98
        if diff <= 3:
            return 0.92
        if diff <= 5:
            return 0.85
        if diff <= 8:
            return 0.75
        if diff <= 15:
            return 0.60
        if diff <= 25:
            return 0.40
        if diff <= 40:
            return 0.25
        return max(0.10, 0.25 - (diff - 40) * 0.003)

    except Exception as e:
        print(f"Error scoring BPM compatibility: {e}")
        return 0.5


def calculate_transition_score(track1_analysis, track2_analysis):
    """
    Calculate comprehensive transition score (0-100) between two tracks.

    Weighted factors (per prompt Section C.1):
      Harmonic compatibility  35 %
      Rhythmic (BPM + groove) 25 %
      Energy flow             20 %
      Mood alignment          15 %
      Danceability proximity   5 %

    Args:
        track1_analysis, track2_analysis: Dicts from analyze_track()

    Returns:
        dict with:
          - overall_score: int 0-100
          - harmonic_score: int 0-100
          - energy_score: int 0-100
          - groove_score: int 0-100
          - mood_score: int 0-100
          - bpm_score: int 0-100
          - mix_difficulty: "Easy" | "Moderate" | "Challenging" | "Expert"
          - recommendation: text label
          - notes: list of bullet-point notes
          - technique_suggestions: list of technique strings
    """
    if track1_analysis is None or track2_analysis is None:
        return {"overall_score": 0, "recommendation": "Insufficient data"}

    try:
        cam1 = track1_analysis.get("camelot", "Unknown")
        cam2 = track2_analysis.get("camelot", "Unknown")

        # ── Component scores (0-1 internally, 0-100 in output) ───────────────
        harmonic_raw = score_harmonic_compatibility(cam1, cam2)

        bpm_raw = score_bpm_compatibility(
            track1_analysis.get("bpm"),
            track2_analysis.get("bpm")
        )

        # Energy score
        e1 = track1_analysis.get("energy") or {}
        e2 = track2_analysis.get("energy") or {}
        if e1 and e2:
            energy_shift = abs(e1.get("overall_score", 0.5) -
                               e2.get("overall_score", 0.5))
            energy_raw = max(0.3, 1.0 - energy_shift * 0.5)
        else:
            energy_raw = 0.5

        groove_raw = 0.5
        g1 = track1_analysis.get("groove")
        g2 = track2_analysis.get("groove")
        if g1 and g2:
            groove_raw = analyze_groove_compatibility(g1, g2)

        mood_raw = 0.5
        m1 = track1_analysis.get("mood")
        m2 = track2_analysis.get("mood")
        if m1 and m2:
            mood_raw = analyze_mood_compatibility(m1, m2)

        # Danceability proximity bonus (0-1)
        d1 = (m1 or {}).get("danceability", 50)
        d2 = (m2 or {}).get("danceability", 50)
        dance_raw = max(0.0, 1.0 - abs(d1 - d2) / 100.0)

        # Rhythmic composite = 60% BPM + 40% groove
        rhythmic_raw = bpm_raw * 0.60 + groove_raw * 0.40

        # ── Weighted overall (0-1) ────────────────────────────────────────────
        overall = (
            harmonic_raw * 0.35 +
            rhythmic_raw * 0.25 +
            energy_raw   * 0.20 +
            mood_raw     * 0.15 +
            dance_raw    * 0.05
        )
        overall = min(overall, 1.0)

        # Convert to 0-100 integers
        def pct(v):
            return int(round(v * 100))

        overall_score  = pct(overall)
        harmonic_score = pct(harmonic_raw)
        energy_score   = pct(energy_raw)
        groove_score   = pct(groove_raw)
        mood_score     = pct(mood_raw)
        bpm_score      = pct(bpm_raw)

        # ── Recommendation label ──────────────────────────────────────────────
        if overall_score >= 85:
            recommendation = "🟢 Excellent transition"
        elif overall_score >= 70:
            recommendation = "🟢 Good transition"
        elif overall_score >= 55:
            recommendation = "🟡 Acceptable transition"
        elif overall_score >= 40:
            recommendation = "🟠 Possible with care"
        else:
            recommendation = "🔴 Difficult transition"

        # ── Mix difficulty ────────────────────────────────────────────────────
        if overall_score >= 80:
            mix_difficulty = "Easy"
        elif overall_score >= 60:
            mix_difficulty = "Moderate"
        elif overall_score >= 40:
            mix_difficulty = "Challenging"
        else:
            mix_difficulty = "Expert"

        # ── Notes ─────────────────────────────────────────────────────────────
        notes = []
        compat_result = get_harmonic_compatibility_score(cam1, cam2)
        notes.append(
            f"{'✓' if harmonic_score >= 75 else '~' if harmonic_score >= 55 else '✗'} "
            f"Harmonic: {compat_result['label']} — {compat_result['reasoning']}"
        )

        if bpm_score >= 90:
            notes.append("✓ BPM perfectly matched — beatmatch-ready")
        elif bpm_score >= 75:
            notes.append("✓ BPM well matched — minor adjustment needed")
        elif bpm_score >= 55:
            notes.append("~ BPM adjustment required — plan the beatmatch")
        else:
            notes.append("✗ Large BPM difference — consider half/double time")

        if e1 and e2:
            e_dir = e2.get("energy_curve", "stable")
            n1 = e1.get("numeric_score", "?")
            n2 = e2.get("numeric_score", "?")
            notes.append(
                f"{'✓' if energy_score >= 75 else '~' if energy_score >= 55 else '✗'} "
                f"Energy: {n1}/10 → {n2}/10  ({e_dir} incoming)"
            )

        if g1 and g2:
            fam1 = g1.get("groove_family", "?")
            fam2 = g2.get("groove_family", "?")
            notes.append(
                f"{'✓' if groove_score >= 75 else '~' if groove_score >= 55 else '✗'} "
                f"Groove: {fam1} → {fam2}  (score {groove_score}/100)"
            )

        if m1 and m2:
            pm1 = m1.get("primary_mood", "?")
            pm2 = m2.get("primary_mood", "?")
            notes.append(
                f"{'✓' if mood_score >= 75 else '~' if mood_score >= 55 else '✗'} "
                f"Mood: {pm1} → {pm2}"
            )

        # ── Technique suggestions ─────────────────────────────────────────────
        tr = get_transition_reasoning(cam1, cam2,
                                      track1_analysis.get("bpm"),
                                      track2_analysis.get("bpm"))
        technique_suggestions = tr["techniques"]

        # BPM-specific additions
        bpm1 = track1_analysis.get("bpm")
        bpm2 = track2_analysis.get("bpm")
        if bpm1 and bpm2 and abs(bpm1 - bpm2) > 3:
            technique_suggestions.append(
                f"Pitch-lock adjust: {bpm1:.0f} BPM → {bpm2:.0f} BPM "
                f"({abs(bpm2 - bpm1):.1f} BPM diff)"
            )

        return {
            "overall_score":        overall_score,
            "harmonic_score":       harmonic_score,
            "energy_score":         energy_score,
            "groove_score":         groove_score,
            "mood_score":           mood_score,
            "bpm_score":            bpm_score,
            "mix_difficulty":       mix_difficulty,
            "recommendation":       recommendation,
            "notes":                notes,
            "technique_suggestions": technique_suggestions,
        }

    except Exception as e:
        print(f"Error calculating transition score: {e}")
        return {"overall_score": 0, "recommendation": f"Error: {str(e)}"}


def find_best_transitions_for_track(track_analysis, candidate_tracks):
    """
    Find the best transitions from one track to a list of candidates (0-100 scoring).

    Args:
        track_analysis: Dict from analyze_track() for source track
        candidate_tracks: List of dicts from analyze_track()

    Returns:
        Sorted list of dicts: { index, score, recommendation, details }
    """
    results = []
    for idx, candidate in enumerate(candidate_tracks):
        transition = calculate_transition_score(track_analysis, candidate)
        results.append({
            "index": idx,
            "score": transition.get("overall_score", 0),
            "recommendation": transition.get("recommendation", "Unknown"),
            "details": transition,
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def suggest_next_tracks(current_track, all_tracks, top_n=5):
    """
    Suggest the best N next tracks to play after *current_track*.

    Args:
        current_track: Analysis dict for the currently playing track
        all_tracks: List of analysis dicts for all candidate tracks
        top_n: How many suggestions to return (default 5)

    Returns:
        List of dicts (top_n items):
          { 'rank', 'file_path', 'score', 'recommendation',
            'technique_suggestions', 'notes' }
    """
    results = find_best_transitions_for_track(current_track, all_tracks)
    suggestions = []
    for rank, r in enumerate(results[:top_n], start=1):
        candidate = all_tracks[r["index"]]
        suggestions.append({
            "rank": rank,
            "file_path": candidate.get("file_path", ""),
            "camelot": candidate.get("camelot", "?"),
            "bpm": candidate.get("bpm"),
            "score": r["score"],
            "recommendation": r["recommendation"],
            "technique_suggestions": r["details"].get("technique_suggestions", []),
            "notes": r["details"].get("notes", []),
        })
    return suggestions


def build_compatibility_matrix(tracks):
    """
    Build an all-vs-all compatibility matrix for a list of tracks.

    Args:
        tracks: List of analysis dicts from analyze_track()

    Returns:
        dict with:
          - matrix: 2D list[i][j] = overall_score (int 0-100)
          - best_pairs: list of (i, j, score) sorted by score desc
          - worst_pairs: list of (i, j, score) sorted by score asc (top 10)
          - track_avg_scores: list of average compatibility per track
    """
    n = len(tracks)
    matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 100
            elif j > i:
                result = calculate_transition_score(tracks[i], tracks[j])
                score = result.get("overall_score", 0)
                matrix[i][j] = score
                matrix[j][i] = score  # symmetric for display; in practice i→j ≠ j→i

    # Collect pairs
    pairs = [(i, j, matrix[i][j]) for i in range(n) for j in range(i + 1, n)]
    best_pairs  = sorted(pairs, key=lambda x: x[2], reverse=True)[:20]
    worst_pairs = sorted(pairs, key=lambda x: x[2])[:10]

    # Average score per track (excluding self)
    track_avg = []
    for i in range(n):
        others = [matrix[i][j] for j in range(n) if j != i]
        track_avg.append(round(sum(others) / len(others), 1) if others else 0)

    return {
        "matrix": matrix,
        "best_pairs": best_pairs,
        "worst_pairs": worst_pairs,
        "track_avg_scores": track_avg,
    }


def full_track_analysis(file_path):
    """
    Complete analysis of a track including all features for transitions.

    Args:
        file_path: Path to audio file

    Returns:
        Comprehensive analysis dict with all features (delegates to analyze_track)
    """
    if not LIBROSA_AVAILABLE:
        return None

    try:
        from audio_analysis.key_detection import analyze_track
        return analyze_track(file_path)
    except Exception as e:
        print(f"Error in full track analysis: {e}")
        return None
