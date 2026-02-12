#!/usr/bin/env python3
"""
🧪 Simple Test Script for DJ Harmonic Analyzer

Run this to verify your installation is working correctly!

Usage:
    python test_setup.py
"""

import sys

def test_utils():
    """Test the Camelot utility functions."""
    print("🧪 Testing Utils Module...")
    
    from utils.camelot_map import (
        get_camelot_key,
        get_relative_minor,
        is_compatible_keys,
        get_harmonic_mixes
    )
    
    # Test 1: Get Camelot key
    key = get_camelot_key("C Major")
    assert key == "8B", f"Expected '8B', got '{key}'"
    print("  ✓ C Major → 8B")
    
    key = get_camelot_key("A Minor")
    assert key == "8A", f"Expected '8A', got '{key}'"
    print("  ✓ A Minor → 8A")
    
    # Test 2: Relative minor/major
    rel = get_relative_minor("8B")
    assert rel == "8A", f"Expected '8A', got '{rel}'"
    print("  ✓ 8B relative → 8A")
    
    # Test 3: Compatibility checks
    assert is_compatible_keys("8A", "8A") == True
    print("  ✓ 8A is compatible with 8A")
    
    assert is_compatible_keys("8A", "7A") == True
    print("  ✓ 8A is compatible with 7A")
    
    assert is_compatible_keys("8A", "5B") == False
    print("  ✓ 8A is NOT compatible with 5B")
    
    # Test 4: Harmonic mixes
    mixes = get_harmonic_mixes("8A")
    assert "8A" in mixes
    assert "7A" in mixes
    assert "9A" in mixes
    print(f"  ✓ 8A compatible keys: {mixes}")
    
    print("✅ Utils tests passed!\n")


def test_file_manager():
    """Test the file manager functions."""
    print("🧪 Testing File Manager Module...")
    
    from file_manager.organizaer import find_audio_files
    
    # This should work without error
    files = find_audio_files(".")
    print(f"  ✓ Found {len(files)} audio files in current directory")
    
    print("✅ File Manager tests passed!\n")


def test_audio_analysis():
    """Test the audio analysis (may fail without librosa)."""
    print("🧪 Testing Audio Analysis Module...")
    
    try:
        import librosa
        print("  ✓ Librosa is installed")
    except ImportError:
        print("  ⚠️  Librosa not installed - audio analysis will not work")
        print("     Run: pip install librosa")
        return
    
    from audio_analysis.key_detection import (
        detect_key_from_audio,
        detect_bpm,
        analyze_track
    )
    
    print("  ✓ All audio analysis functions imported successfully")
    
    # Check if test audio exists
    import os
    input_audio = "input_audio"
    if os.path.exists(input_audio):
        files = os.listdir(input_audio)
        if files:
            test_file = os.path.join(input_audio, files[0])
            print(f"  🎵 Testing with: {test_file}")
            result = analyze_track(test_file)
            print(f"     Key: {result.get('key', 'N/A')}")
            print(f"     BPM: {result.get('bpm', 'N/A')}")
        else:
            print("  ⚠️  No audio files in input_audio/ folder")
    else:
        print("  ℹ️  No input_audio/ folder - add some music to test!")
    
    print("✅ Audio Analysis tests passed!\n")


def main():
    """Run all tests."""
    print("=" * 50)
    print("🎧 DJ Harmonic Analyzer - Setup Test")
    print("=" * 50)
    print()
    
    try:
        test_utils()
        test_file_manager()
        test_audio_analysis()
        
        print("=" * 50)
        print("🎉 All tests completed successfully!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("  1. Add some audio files to input_audio/")
        print("  2. Run: python main.py --help")
        print("  3. Try: python main.py analyze input_audio/your_song.mp3")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

