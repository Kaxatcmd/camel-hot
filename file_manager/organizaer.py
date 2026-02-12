"""
File Organizer - Sorting Your Music Library

This module helps you organize your music collection based on
musical properties like key and BPM. Perfect for DJs who want
their music library sorted by Camelot key!

Key Features:
- Find all audio files in a folder
- Organize files into folders by their musical key
- Create playlists of harmonically compatible songs
"""

import os
import shutil
from pathlib import Path


def find_audio_files(directory, extensions=None):
    """
    Find all audio files in a directory and its subdirectories.
    
    This walks through a folder and collects any files that look
    like audio - MP3, WAV, FLAC, etc.
    
    Args:
        directory: Folder to search in (e.g., "/music/my_collection")
        extensions: List of extensions to look for. If None, uses defaults.
    
    Returns:
        List of paths to audio files found
    
    Example:
        >>> files = find_audio_files("/home/user/music")
        >>> print(f"Found {len(files)} audio files")
        Found 150 audio files
    """
    # Default audio file extensions if none specified
    if extensions is None:
        extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aiff']
    
    # Make sure extensions are lowercase
    extensions = [ext.lower() for ext in extensions]
    
    audio_files = []
    
    # pathlib is modern and handles paths well on all OS
    path = Path(directory)
    
    # Walk through all folders and files
    # .rglob finds files recursively (in all subfolders)
    for ext in extensions:
        # Find files matching this extension
        audio_files.extend(path.rglob(f"*{ext}"))
    
    # Convert Path objects to strings for easier handling
    return [str(f) for f in audio_files]


def organize_by_key(input_directory, output_directory, move_files=False):
    """
    Organize audio files into folders based on their musical key.
    
    This is like having a DJ library where everything is sorted
    by Camelot key. You can find compatible tracks instantly!
    
    How it works:
    1. Find all audio files in the input folder
    2. Analyze each file to detect its key
    3. Create folders for each Camelot key (e.g., "8A", "9B")
    4. Copy (or move) files into their matching folder
    
    Args:
        input_directory: Where to look for audio files
        output_directory: Where to put the organized files
        move_files: If True, removes from original location. 
                    If False, copies (safer - keeps originals!)
    
    Returns:
        Summary dictionary with organizing results
    
    Example:
        >>> result = organize_by_key("/downloads", "/music/organized")
        >>> print(f"Moved {result['moved_count']} files")
        Moved 50 files
    """
    # Make sure output directory exists
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    # Find all audio files
    audio_files = find_audio_files(input_directory)
    
    # Track what happened
    results = {
        "total_files": len(audio_files),
        "organized_count": 0,
        "errors": [],
        "by_key": {}  # Count files per key
    }
    
    # Import here to avoid circular imports
    from audio_analysis.key_detection import analyze_track
    
    print(f"🔍 Found {len(audio_files)} audio files")
    
    for file_path in audio_files:
        try:
            # Analyze this track
            analysis = analyze_track(file_path)
            
            # Get the Camelot key (or Unknown)
            camelot = analysis.get('camelot', 'Unknown')
            
            if camelot == 'Unknown':
                # Skip files we couldn't analyze
                results['errors'].append({
                    'file': file_path,
                    'reason': 'Could not detect key'
                })
                continue
            
            # Create folder for this key if it doesn't exist
            key_folder = Path(output_directory) / camelot
            key_folder.mkdir(exist_ok=True)
            
            # Get the filename
            filename = Path(file_path).name
            
            # Build the destination path
            destination = key_folder / filename
            
            # Copy or move the file
            if move_files:
                shutil.move(file_path, destination)
            else:
                shutil.copy2(file_path, destination)
            
            # Track success
            results['organized_count'] += 1
            
            # Track by key
            if camelot not in results['by_key']:
                results['by_key'][camelot] = []
            results['by_key'][camelot].append(filename)
            
            print(f"  ✓ {filename} → {camelot}")
        
        except Exception as e:
            # Something went wrong with this file
            results['errors'].append({
                'file': file_path,
                'reason': str(e)
            })
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Organized: {results['organized_count']}")
    print(f"  Errors: {len(results['errors'])}")
    print(f"  Keys found: {', '.join(sorted(results['by_key'].keys()))}")
    
    return results


def create_playlist(input_directory, output_file, target_key=None, 
                    bpm_range=None, max_songs=20):
    """
    Create an M3U playlist of harmonically compatible songs.
    
    This creates a playlist you can load in DJ software! You can:
    - Pick a target key (like "8A") and get compatible songs
    - Filter by BPM range
    - Limit the total number of songs
    
    Args:
        input_directory: Folder containing audio files
        output_file: Where to save the playlist (.m3u format)
        target_key: Camelot key to match (e.g., "8A")
        bpm_range: Tuple (min_bpm, max_bpm) to filter by
        max_songs: Maximum songs to include
    
    Returns:
        List of files in the playlist
    
    Example:
        >>> # Create a playlist in 8A at 120-130 BPM
        >>> playlist = create_playlist(
        ...     "/music",
        ...     "/music/8A_playlist.m3u",
        ...     target_key="8A",
        ...     bpm_range=(120, 130)
        ... )
        >>> print(f"Created playlist with {len(playlist)} songs")
    """
    # Find all audio files
    audio_files = find_audio_files(input_directory)
    
    # Track playlist entries
    playlist = []
    
    # Import analysis function
    from audio_analysis.key_detection import analyze_track
    from utils.camelot_map import is_compatible_keys
    
    print(f"🎵 Building playlist...")
    
    for file_path in audio_files:
        # Stop if we have enough songs
        if len(playlist) >= max_songs:
            break
        
        try:
            # Analyze this track
            analysis = analyze_track(file_path)
            
            track_key = analysis.get('camelot', 'Unknown')
            track_bpm = analysis.get('bpm', 0)
            
            # Skip if we couldn't detect the key
            if track_key == 'Unknown':
                continue
            
            # Check key compatibility
            if target_key is not None:
                if not is_compatible_keys(track_key, target_key):
                    continue
            
            # Check BPM range
            if bpm_range is not None:
                min_bpm, max_bpm = bpm_range
                if track_bpm < min_bpm or track_bpm > max_bpm:
                    continue
            
            # This track passes all filters - add it!
            playlist.append(file_path)
            print(f"  ✓ Added: {Path(file_path).name} ({track_key}, {track_bpm} BPM)")
        
        except Exception as e:
            print(f"  ✗ Error analyzing {file_path}: {e}")
    
    # Write the playlist file
    # M3U format is simple: just absolute paths, one per line
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header (optional but nice)
        f.write("#EXTM3U\n")
        f.write(f"# Playlist generated by DJ Harmonic Analyzer\n")
        f.write(f"# Target Key: {target_key or 'Any'}\n")
        f.write(f"# BPM Range: {bpm_range or 'Any'}\n\n")
        
        # Write each file path
        for file_path in playlist:
            f.write(f"{file_path}\n")
    
    print(f"\n✅ Playlist saved to: {output_file}")
    print(f"   Total songs: {len(playlist)}")
    
    return playlist


def copy_with_metadata(source, destination, analysis):
    """
    Copy a file and add harmonic analysis info to the filename.
    
    This is useful if you want to see the key in the filename itself.
    For example: "My Song (8A, 128 BPM).mp3"
    
    Args:
        source: Original file path
        destination: Target directory
        analysis: Dictionary with 'camelot' and 'bpm' keys
    """
    # Get original filename
    original_name = Path(source).stem  # Without extension
    
    # Build new name with metadata
    camelot = analysis.get('camelot', 'Unknown')
    bpm = analysis.get('bpm', 0)
    
    # Format: "Artist - Title (8A, 128 BPM).mp3"
    new_name = f"{original_name} ({camelot}, {bpm} BPM){Path(source).suffix}"
    
    # Full destination path
    dest_path = Path(destination) / new_name
    
    # Do the copy
    shutil.copy2(source, dest_path)
    
    return str(dest_path)


# Alias para manter compatibilidade com código antigo
create_harmonic_playlist = create_playlist

def create_harmonic_sequence_playlist(input_directory, output_file, 
                                      start_key, sequence_length=8,
                                      direction='forward', max_songs_per_key=3):
    """
    Create a playlist following a harmonic sequence path.
    
    This creates a professional DJ-style playlist that follows a specific
    harmonic journey around the Camelot wheel. Each track transitions
    harmonically to the next!
    
    Args:
        input_directory: Folder containing audio files
        output_file: Where to save the playlist (.m3u format)
        start_key: Starting Camelot key (e.g., "8A")
        sequence_length: How many keys to traverse
        direction: 'forward', 'backward', or 'zigzag'
        max_songs_per_key: Maximum tracks per key in sequence
    
    Returns:
        List of files in the playlist
    
    Example:
        >>> playlist = create_harmonic_sequence_playlist(
        ...     "/music",
        ...     "/music/harmonic_mix.m3u",
        ...     start_key="8A",
        ...     sequence_length=8,
        ...     direction="forward"
        ... )
    """
    from utils.camelot_map import generate_harmonic_sequence
    from audio_analysis.key_detection import analyze_track
    
    # Find all audio files
    audio_files = find_audio_files(input_directory)
    
    # Generate the key sequence we'll follow
    key_sequence = generate_harmonic_sequence(start_key, sequence_length, direction)
    
    print(f"🎼 Criando playlist com sequência harmônica: {' > '.join(key_sequence)}")
    
    # Organize files by key
    files_by_key = {}
    
    for file_path in audio_files:
        try:
            analysis = analyze_track(file_path)
            key = analysis.get('camelot', 'Unknown')
            
            if key not in files_by_key:
                files_by_key[key] = []
            files_by_key[key].append(file_path)
        except Exception as e:
            print(f"  ✗ Erro ao analisar {file_path}: {e}")
    
    # Build playlist following the sequence
    playlist = []
    file_count = {key: 0 for key in key_sequence}
    
    for key in key_sequence:
        if key in files_by_key:
            # Get songs for this key, up to max_songs_per_key
            for file_path in files_by_key[key]:
                if file_count[key] < max_songs_per_key:
                    playlist.append(file_path)
                    file_count[key] += 1
                    print(f"  ✓ Added: {Path(file_path).name} ({key})")
                else:
                    break
    
    # Write the playlist file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# Harmonic Sequence Playlist\n")
        f.write(f"# Sequence: {' > '.join(key_sequence)}\n")
        f.write(f"# Direction: {direction}\n\n")
        
        for file_path in playlist:
            f.write(f"{file_path}\n")
    
    print(f"\n✅ Harmonic sequence playlist saved: {output_file}")
    print(f"   Total songs: {len(playlist)}")
    
    return playlist


def create_key_to_key_playlist(input_directory, output_file,
                               start_key, target_key, max_songs=30):
    """
    Create a playlist that transitions from one key to another.
    
    This finds an optimal harmonic path from start to target key
    and creates a mix that naturally transitions between them.
    
    Args:
        input_directory: Folder containing audio files
        output_file: Where to save the playlist
        start_key: Starting Camelot key (e.g., "8A")
        target_key: Target Camelot key (e.g., "3B")
        max_songs: Maximum songs to include
    
    Returns:
        List of files in the playlist
    
    Example:
        >>> playlist = create_key_to_key_playlist(
        ...     "/music",
        ...     "/music/transition.m3u",
        ...     start_key="8A",
        ...     target_key="3B"
        ... )
    """
    from utils.camelot_map import get_harmonic_path
    from audio_analysis.key_detection import analyze_track
    
    # Find all audio files
    audio_files = find_audio_files(input_directory)
    
    # Get the harmonic path from start to target
    path = get_harmonic_path(start_key, target_key)
    
    print(f"🎼 Criando playlist de transição: {' > '.join(path)}")
    
    # Organize files by key
    files_by_key = {}
    
    for file_path in audio_files:
        try:
            analysis = analyze_track(file_path)
            key = analysis.get('camelot', 'Unknown')
            
            if key not in files_by_key:
                files_by_key[key] = []
            files_by_key[key].append({
                'path': file_path,
                'bpm': analysis.get('bpm', 0)
            })
        except Exception as e:
            print(f"  ✗ Erro ao analisar {file_path}: {e}")
    
    # Build playlist following the transition path
    playlist = []
    songs_added = 0
    
    for key in path:
        if songs_added >= max_songs:
            break
        
        if key in files_by_key:
            # Sort by BPM for smoother transitions
            files_by_key[key].sort(key=lambda x: x['bpm'])
            
            for file_info in files_by_key[key]:
                if songs_added >= max_songs:
                    break
                
                playlist.append(file_info['path'])
                songs_added += 1
                print(f"  ✓ Added: {Path(file_info['path']).name} ({key}, {file_info['bpm']} BPM)")
    
    # Write the playlist file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# Key Transition Playlist\n")
        f.write(f"# Path: {' > '.join(path)}\n")
        f.write(f"# Start: {start_key} > End: {target_key}\n\n")
        
        for file_path in playlist:
            f.write(f"{file_path}\n")
    
    print(f"\n✅ Transition playlist saved: {output_file}")
    print(f"   Total songs: {len(playlist)}")
    
    return playlist


def create_camelot_zone_playlist(input_directory, output_file,
                                 target_key, zone_size=3, max_songs=50):
    """
    Create a focused playlist within a Camelot "zone".
    
    A zone is a region of the Camelot wheel where all keys are
    compatible. This creates a playlist of only compatible tracks!
    
    Args:
        input_directory: Folder containing audio files
        output_file: Where to save the playlist
        target_key: Center Camelot key (e.g., "8A")
        zone_size: How wide the zone is (1-3, incompatible at 3+)
        max_songs: Maximum songs to include
    
    Returns:
        List of files in the playlist
    
    Example:
        >>> playlist = create_camelot_zone_playlist(
        ...     "/music",
        ...     "/music/zone_8a.m3u",
        ...     target_key="8A",
        ...     zone_size=2
        ... )
    """
    from utils.camelot_map import is_compatible_keys
    from audio_analysis.key_detection import analyze_track
    
    # Find all audio files
    audio_files = find_audio_files(input_directory)
    
    print(f"🎼 Criando playlist de zona compatível: {target_key} (raio {zone_size})")
    
    playlist = []
    
    for file_path in audio_files:
        if len(playlist) >= max_songs:
            break
        
        try:
            analysis = analyze_track(file_path)
            key = analysis.get('camelot', 'Unknown')
            
            # Check if this key is within our zone
            if is_compatible_keys(key, target_key):
                playlist.append(file_path)
                print(f"  ✓ Added: {Path(file_path).name} ({key})")
        except Exception as e:
            print(f"  ✗ Erro ao analisar {file_path}: {e}")
    
    # Write the playlist file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# Camelot Zone Playlist\n")
        f.write(f"# Center: {target_key}\n")
        f.write(f"# Zone Size: {zone_size}\n")
        f.write(f"# All tracks are harmonically compatible!\n\n")
        
        for file_path in playlist:
            f.write(f"{file_path}\n")
    
    print(f"\n✅ Zone playlist saved: {output_file}")
    print(f"   Total songs: {len(playlist)}")
    
    return playlist