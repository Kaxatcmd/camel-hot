"""
Demo Script - Transition Scoring Engine Features

This script demonstrates all the new transition scoring capabilities.
Run with: python test_transition_engine.py

Features demonstrated:
1. Energy level detection
2. Groove analysis
3. Mood classification
4. Comprehensive transition scoring
5. Finding best transitions for a track
"""

import os
from pathlib import Path
from audio_analysis.key_detection import analyze_track
from utils.transition_scoring import (
    calculate_transition_score,
    find_best_transitions_for_track,
    full_track_analysis
)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_single_track_analysis(file_path):
    """Demonstrate complete analysis of a single track."""
    print_section("SINGLE TRACK ANALYSIS")
    
    print(f"Analyzing: {file_path}")
    analysis = analyze_track(file_path)
    
    if analysis is None:
        print("❌ Analysis failed - librosa may not be installed")
        return analysis
    
    print("\n📋 BASIC INFO")
    print(f"  File: {os.path.basename(analysis.get('file_path', 'Unknown'))}")
    print(f"  Duration: {analysis.get('duration', 'Unknown')} seconds")
    print(f"  Key: {analysis.get('key', 'Unknown')}")
    print(f"  Camelot: {analysis.get('camelot', 'Unknown')}")
    print(f"  BPM: {analysis.get('bpm', 'Unknown')}")
    print(f"  Key Confidence: {analysis.get('confidence', 0):.2%}")
    
    # Energy Analysis
    energy = analysis.get('energy')
    if energy:
        print("\n⚡ ENERGY LEVEL")
        print(f"  Overall Level: {energy.get('level', 'Unknown')}")
        print(f"  Brightness: {energy.get('brightness', 'Unknown')} ({energy.get('brightness_score', 0):.2f})")
        print(f"  Density: {energy.get('density', 'Unknown')} ({energy.get('richness_score', 0):.2f})")
        print(f"  Energy Curve: {energy.get('energy_curve', 'Unknown')}")
        print(f"  Overall Score: {energy.get('overall_score', 0):.2f}/1.0")
    
    # Groove Analysis
    groove = analysis.get('groove')
    if groove:
        print("\n🥁 GROOVE & RHYTHM")
        print(f"  Type: {groove.get('type', 'Unknown')}")
        print(f"  Kick Presence: {groove.get('kick_presence', 0):.2f}")
        print(f"  Kick Regularity: {groove.get('kick_regularity', 0):.2f}")
        print(f"  Percussion Density: {groove.get('percussion_density', 0):.2f}")
        print(f"  Swing/Groove Feel: {groove.get('swing', 0):.2f}")
    
    # Mood Classification
    mood = analysis.get('mood')
    if mood:
        print("\n😊 MOOD & EMOTION")
        print(f"  Primary Mood: {mood.get('primary_mood', 'Unknown')}")
        print(f"  Tonality: {'Major' if mood.get('is_major') else 'Minor'}")
        print(f"  Aggressiveness: {mood.get('aggressiveness', 0):.2f}")
        print(f"  Brightness: {mood.get('brightness', 0):.2f}")
        print(f"  Harmonic Tension: {mood.get('tension', 0):.2f}")
        
        all_moods = mood.get('all_moods', {})
        if all_moods:
            print("\n  Mood Scores:")
            for mood_name, score in sorted(all_moods.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
                print(f"    {mood_name:15} {bar} {score:.2%}")
    
    return analysis


def demo_transition_analysis(file1, file2):
    """Demonstrate transition scoring between two tracks."""
    print_section("TRANSITION ANALYSIS")
    
    print(f"Comparing transitions:")
    print(f"  Track 1: {os.path.basename(file1)}")
    print(f"  Track 2: {os.path.basename(file2)}")
    
    analysis1 = analyze_track(file1)
    analysis2 = analyze_track(file2)
    
    if analysis1 is None or analysis2 is None:
        print("❌ Analysis failed")
        return None
    
    transition = calculate_transition_score(analysis1, analysis2)
    
    print(f"\n{transition.get('recommendation', 'Unknown')}")
    print(f"\n📊 TRANSITION SCORES")
    print(f"  Overall Compatibility: {transition.get('overall_score', 0):.2f}/1.0")
    print(f"  Harmonic:  {transition.get('harmonic_score', 0):.2f} (Camelot wheel)")
    print(f"  Energy:    {transition.get('energy_score', 0):.2f} (Spectral shift)")
    print(f"  Groove:    {transition.get('groove_score', 0):.2f} (Rhythm match)")
    print(f"  Mood:      {transition.get('mood_score', 0):.2f} (Emotional fit)")
    print(f"  BPM:       {transition.get('bpm_score', 0):.2f} (Tempo match)")
    
    print(f"\n💡 NOTES")
    for note in transition.get('notes', []):
        print(f"  {note}")
    
    return transition


def demo_find_best_transitions(reference_file, music_folder):
    """Demonstrate finding best transition candidates."""
    print_section("FINDING BEST TRANSITIONS")
    
    print(f"Reference track: {os.path.basename(reference_file)}")
    print(f"Searching in: {music_folder}")
    
    # Find all audio files
    audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
    candidate_files = []
    
    if os.path.isdir(music_folder):
        for root, _, files in os.walk(music_folder):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    candidate_files.append(os.path.join(root, file))
    
    if not candidate_files:
        print(f"❌ No audio files found in {music_folder}")
        return
    
    print(f"Found {len(candidate_files)} candidate tracks")
    
    # Analyze reference
    ref_analysis = analyze_track(reference_file)
    if ref_analysis is None:
        print("❌ Failed to analyze reference track")
        return
    
    # Analyze candidates
    print("\nAnalyzing candidates...")
    candidate_analyses = []
    for file in candidate_files[:10]:  # Limit to first 10 for demo
        analysis = analyze_track(file)
        if analysis:
            candidate_analyses.append(analysis)
    
    # Find best transitions
    results = find_best_transitions_for_track(ref_analysis, candidate_analyses)
    
    print(f"\n🎯 BEST 5 TRANSITIONS")
    for i, result in enumerate(results[:5], 1):
        score = result.get('score', 0)
        filename = os.path.basename(
            candidate_analyses[result.get('index', 0)].get('file_path', 'Unknown')
        )
        recommendation = result.get('recommendation', 'Unknown')
        
        print(f"\n  {i}. {filename}")
        print(f"     Score: {score:.2f}/1.0")
        print(f"     {recommendation}")


def demo_complete_workflow():
    """Demonstrate a complete workflow finding and analyzing all tracks."""
    print_section("COMPLETE WORKFLOW DEMO")
    
    # Check for audio files in input_audio folder
    input_folder = "input_audio"
    audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
    
    audio_files = []
    if os.path.isdir(input_folder):
        for root, _, files in os.walk(input_folder):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        print(f"ℹ️ No audio files found in '{input_folder}' folder")
        print("   To test the complete workflow, add some MP3/WAV files to input_audio/")
        print("\n   You can still test individual features by running:")
        print("   - test_setup.py (basic tests)")
        print("   - CLI: python audio_analysis/key_detection.py <file.mp3>")
        return
    
    print(f"Found {len(audio_files)} audio files\n")
    
    # Analyze all files
    print("Analyzing all tracks...")
    analyses = []
    for file in audio_files[:5]:  # Limit to first 5 for demo
        print(f"  • {os.path.basename(file)}...")
        analysis = analyze_track(file)
        if analysis:
            analyses.append(analysis)
    
    # Show mix opportunities
    print(f"\n🎛️ MIX OPPORTUNITIES")
    if len(analyses) >= 2:
        for i in range(len(analyses) - 1):
            transition = calculate_transition_score(analyses[i], analyses[i + 1])
            score = transition.get('overall_score', 0)
            rec = transition.get('recommendation', 'Unknown')
            
            file1 = os.path.basename(analyses[i].get('file_path', 'Unknown'))
            file2 = os.path.basename(analyses[i + 1].get('file_path', 'Unknown'))
            
            print(f"\n  {file1} → {file2}")
            print(f"    {rec}")
            print(f"    Score: {score:.2f}")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("  TRANSITION SCORING ENGINE - FEATURE DEMONSTRATION")
    print("="*70)
    
    print("\n🚀 This demo showcases the new offline transition analysis features:")
    print("   1. Energy Level Detection")
    print("   2. Groove & Rhythm Analysis")
    print("   3. Mood Classification")
    print("   4. Transition Compatibility Scoring")
    print("   5. Auto-DJ Playlist Generation")
    
    # Check if we have test audio files
    demo_file1 = "input_audio/sample1.mp3"
    demo_file2 = "input_audio/sample2.mp3"
    input_folder = "input_audio"
    
    # Try to find actual audio files
    actual_files = []
    if os.path.isdir(input_folder):
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                    actual_files.append(os.path.join(root, file))
    
    if not actual_files:
        print("\n" + "="*70)
        print("  ⓘ DEMO MODE")
        print("="*70)
        print("\n📌 To run the full demonstrations, add audio files to 'input_audio/'")
        print("\n✅ The transition engine is fully implemented and ready to use!")
        print("\nYou can test it with the GUI by running: python main.py")
        print("\n" + "="*70)
        return
    
    # Demo with actual files
    print(f"\nUsing {len(actual_files)} audio file(s) for demonstration...\n")
    
    # Demo 1: Single track analysis
    if len(actual_files) >= 1:
        demo_single_track_analysis(actual_files[0])
    
    # Demo 2: Transition between two tracks
    if len(actual_files) >= 2:
        demo_transition_analysis(actual_files[0], actual_files[1])
    
    # Demo 3: Find best transitions
    if len(actual_files) >= 1:
        demo_find_best_transitions(actual_files[0], input_folder)
    
    # Demo 4: Complete workflow
    demo_complete_workflow()
    
    print("\n" + "="*70)
    print("  ✅ DEMO COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Try the GUI: python main.py")
    print("  2. Read the guide: TRANSITION_ENGINE_GUIDE.md")
    print("  3. Check implementation: audio_analysis/ and utils/")
    print("\n")


if __name__ == "__main__":
    main()
