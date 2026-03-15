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
import re
import shutil
from pathlib import Path


def get_next_org_number(target_directory):
    """
    Find the next available CH_Org number in the target directory.

    Scans for existing CH_Org[N] folders and returns max(N) + 1.
    Returns 1 if none exist yet.

    Args:
        target_directory: Directory to scan

    Returns:
        Integer - the next available organization number
    """
    path = Path(target_directory)
    if not path.exists():
        return 1

    existing_numbers = []
    try:
        for item in path.iterdir():
            if item.is_dir():
                match = re.match(r'^CH_Org(\d+)$', item.name, re.IGNORECASE)
                if match:
                    existing_numbers.append(int(match.group(1)))
    except PermissionError:
        return 1

    if not existing_numbers:
        return 1
    return max(existing_numbers) + 1


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


def organize_by_key(input_directory, output_directory, move_files=False,
                    parent_folder_name=None, progress_callback=None):
    """
    Organize audio files into a hierarchical folder structure based on Camelot key.

    When *parent_folder_name* is provided (e.g. "CH_Org1") the output looks like::

        output_directory/
        └── CH_Org1/
            ├── 8A_Camelot/  ← tracks detected as 8A
            ├── 8B_Camelot/
            ├── Unclassified/  ← tracks whose key could not be detected
            └── ...

    When *parent_folder_name* is omitted the flat legacy behaviour is preserved
    (key folders created directly inside *output_directory*).

    Args:
        input_directory:    Where to look for audio files.
        output_directory:   Destination root directory.
        move_files:         If True, moves files (removes originals).
                            If False (default), copies — originals are preserved.
        parent_folder_name: Optional name for the top-level container folder.
                            Supports the CH_Org[N] naming convention.

    Returns:
        Summary dictionary with fields:
            total_files, organized_count, errors, by_key,
            parent_folder, parent_folder_name
    """
    # Resolve base output path
    if parent_folder_name:
        base_path = Path(output_directory) / parent_folder_name
    else:
        base_path = Path(output_directory)

    base_path.mkdir(parents=True, exist_ok=True)

    # Find all audio files
    audio_files = find_audio_files(input_directory)

    results = {
        "total_files": len(audio_files),
        "organized_count": 0,
        "errors": [],
        "by_key": {},
        "parent_folder": str(base_path),
        "parent_folder_name": parent_folder_name,
    }

    # Import here to avoid circular imports at module load time
    from audio_analysis.key_detection import analyze_track

    print(f"🔍 Found {len(audio_files)} audio files")
    _total = len(audio_files)

    for _idx, file_path in enumerate(audio_files):
        if progress_callback:
            try:
                if progress_callback(Path(file_path).name, _idx, _total):
                    results['cancelled'] = True
                    break
            except Exception:
                pass
        try:
            analysis = analyze_track(file_path)
            camelot = analysis.get('camelot', 'Unknown')

            # Determine the subfolder label
            if camelot and camelot != 'Unknown':
                folder_label = f"{camelot}_Camelot"
                key_id = camelot
            else:
                folder_label = 'Unclassified'
                key_id = 'Unclassified'

            key_folder = base_path / folder_label
            key_folder.mkdir(exist_ok=True)

            filename = Path(file_path).name
            destination = key_folder / filename

            # Skip duplicates gracefully
            if destination.exists():
                results['errors'].append({
                    'file': file_path,
                    'reason': f'File already exists in {folder_label}'
                })
                continue

            if move_files:
                shutil.move(file_path, str(destination))
            else:
                shutil.copy2(file_path, str(destination))

            results['organized_count'] += 1

            if key_id not in results['by_key']:
                results['by_key'][key_id] = []
            results['by_key'][key_id].append(filename)

            print(f"  ✓ {filename} → {folder_label}")

        except Exception as e:
            results['errors'].append({
                'file': file_path,
                'reason': str(e)
            })

    print(f"\n📊 Summary:")
    print(f"  Total files : {results['total_files']}")
    print(f"  Organized   : {results['organized_count']}")
    print(f"  Skipped     : {len(results['errors'])}")
    print(f"  Keys found  : {', '.join(sorted(results['by_key'].keys()))}")

    return results


def create_playlist(input_directory, output_file, target_key=None,
                    bpm_range=None, max_songs=20, progress_callback=None):
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
    _total = len(audio_files)

    # Track playlist entries
    playlist = []
    
    # Import analysis function
    from audio_analysis.key_detection import analyze_track
    from utils.camelot_map import is_compatible_keys
    
    print(f"🎵 Building playlist...")
    
    for _idx, file_path in enumerate(audio_files):
        # Stop if we have enough songs
        if len(playlist) >= max_songs:
            break

        if progress_callback:
            try:
                if progress_callback(Path(file_path).name, _idx, _total):
                    break
            except Exception:
                pass

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
                                      direction='forward', max_songs_per_key=3,
                                      progress_callback=None):
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
    _total = len(audio_files)

    for _idx, file_path in enumerate(audio_files):
        if progress_callback:
            try:
                if progress_callback(Path(file_path).name, _idx, _total):
                    break
            except Exception:
                pass
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
                               start_key, target_key, max_songs=30,
                               progress_callback=None):
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
    _total = len(audio_files)

    for _idx, file_path in enumerate(audio_files):
        if progress_callback:
            try:
                if progress_callback(Path(file_path).name, _idx, _total):
                    break
            except Exception:
                pass
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
                                 target_key, zone_size=3, max_songs=50,
                                 progress_callback=None):
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
    _total = len(audio_files)

    for _idx, file_path in enumerate(audio_files):
        if len(playlist) >= max_songs:
            break

        if progress_callback:
            try:
                if progress_callback(Path(file_path).name, _idx, _total):
                    break
            except Exception:
                pass

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


# ─────────────────────────────────────────────────────────────────────────────
# NEW: Intelligent sequencing and next-track suggestions
# ─────────────────────────────────────────────────────────────────────────────

def optimize_playlist_order(analyses, strategy="energy_arc"):
    """
    Reorder a list of already-analysed tracks for optimal flow.

    Strategies:
      'energy_arc'  — build from low to a climax then cool down
      'harmonic'    — maximise harmonic compatibility between consecutive tracks
      'mood'        — cluster by mood for emotional continuity

    Args:
        analyses: List of analysis dicts (from analyze_track()).  Each must
                  have at least 'file_path' and 'camelot'.
        strategy: Ordering strategy (see above)

    Returns:
        Ordered list of analysis dicts.
    """
    if not analyses:
        return []

    try:
        from utils.transition_scoring import calculate_transition_score

        if strategy == "energy_arc":
            # Sort by numeric energy: low → high → low (arc)
            def energy_key(a):
                e = a.get("energy") or {}
                return e.get("numeric_score", 5)

            scored = sorted(analyses, key=energy_key)
            n = len(scored)
            # Build arc: first half ascending, second half descending
            ascending  = scored[:n // 2]
            descending = list(reversed(scored[n // 2:]))
            return ascending + descending

        elif strategy == "harmonic":
            # Greedy nearest-neighbour on harmonic score
            remaining = list(analyses)
            ordered   = [remaining.pop(0)]
            while remaining:
                current = ordered[-1]
                best_idx = 0
                best_score = -1
                for i, candidate in enumerate(remaining):
                    score = calculate_transition_score(current, candidate).get("harmonic_score", 0)
                    if score > best_score:
                        best_score = score
                        best_idx = i
                ordered.append(remaining.pop(best_idx))
            return ordered

        elif strategy == "mood":
            # Group by primary mood, then by energy within group
            from collections import defaultdict
            groups = defaultdict(list)
            for a in analyses:
                mood = (a.get("mood") or {}).get("primary_mood", "Unknown")
                groups[mood].append(a)
            ordered = []
            for mood_tracks in groups.values():
                mood_tracks.sort(key=lambda a: (a.get("energy") or {}).get("numeric_score", 5))
                ordered.extend(mood_tracks)
            return ordered

        else:
            return analyses

    except Exception as e:
        print(f"Error optimising playlist order: {e}")
        return analyses


def create_intelligent_playlist(input_directory, output_file,
                                 strategy="energy_arc", max_songs=30,
                                 target_key=None, bpm_range=None):
    """
    Create an intelligently ordered playlist using transition scoring.

    Analyses all audio files, then orders them according to the chosen strategy
    for a smooth, professional DJ set.

    Args:
        input_directory: Folder containing audio files
        output_file: Where to save the playlist (.m3u)
        strategy: 'energy_arc' | 'harmonic' | 'mood' (default 'energy_arc')
        max_songs: Maximum tracks to include
        target_key: Optional Camelot key filter
        bpm_range: Optional (min, max) BPM filter tuple

    Returns:
        List of ordered file paths in the playlist
    """
    from audio_analysis.key_detection import analyze_track
    from utils.camelot_map import is_compatible_keys

    audio_files = find_audio_files(input_directory)
    print(f"🔍 Found {len(audio_files)} audio files — analysing...")

    analyses = []
    for fp in audio_files:
        if len(analyses) >= max_songs * 3:  # analyse extra for filtering
            break
        try:
            a = analyze_track(fp)
            cam = a.get("camelot", "Unknown")
            bpm = a.get("bpm") or 0

            if cam == "Unknown":
                continue
            if target_key and not is_compatible_keys(cam, target_key):
                continue
            if bpm_range:
                min_b, max_b = bpm_range
                if not (min_b <= bpm <= max_b):
                    continue

            analyses.append(a)
        except Exception as e:
            print(f"  ✗ {fp}: {e}")

    if not analyses:
        print("⚠️  No compatible tracks found.")
        return []

    # Trim to max_songs before optimising (expensive for large libraries)
    analyses = analyses[:max_songs]
    ordered  = optimize_playlist_order(analyses, strategy=strategy)

    paths = [a["file_path"] for a in ordered]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Intelligent Playlist — strategy: {strategy}\n")
        f.write(f"# Target key: {target_key or 'Any'}  BPM range: {bpm_range or 'Any'}\n\n")
        for fp in paths:
            f.write(f"{fp}\n")

    print(f"\n✅ Intelligent playlist saved: {output_file}  ({len(paths)} tracks)")
    return paths
