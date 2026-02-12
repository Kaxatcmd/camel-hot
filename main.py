"""
DJ Harmonic Analyzer - Main Entry Point (GUI Version)

This is the main program with Graphical User Interface.
The application provides an easy-to-use GUI for:
- Analyzing music files to detect keys and BPM
- Organizing your music library by Camelot notation
- Creating harmonic mixing playlists
- Checking musical key compatibility

To run:
    python main.py

This will launch the GUI application.
"""

from gui.main_window import main


if __name__ == "__main__":
    main()


# ============= LEGACY CLI CODE (Mantido para referência) =============
# O código abaixo foi substituído pela versão GUI
# Ele pode ser consultado para referência ou para criar um modo CLI alternativo

def cmd_analyze(args):
    """
    Analyze a single audio file.
    
    This command tells you:
    - What musical key the song is in
    - The Camelot notation (DJ format)
    - The BPM (tempo)
    - How long the track is
    """
    from audio_analysis.key_detection import analyze_track
    
    print(f"\n🔍 Analyzing: {args.file}")
    print("-" * 40)
    
    result = analyze_track(args.file)
    
    print(f"📀 Key:        {result.get('key', 'Unknown')}")
    print(f"🎼 Camelot:     {result.get('camelot', 'Unknown')}")
    print(f"⏱️  BPM:         {result.get('bpm', 'Unknown')}")
    print(f"⏰ Duration:   {result.get('duration', 'Unknown')} seconds")
    print(f"📁 File:       {result.get('file_path', args.file)}")
    
    if 'confidence' in result:
        print(f"💪 Confidence: {result['confidence']:.0%}")


def cmd_organize(args):
    """
    Organize a folder of music by musical key.
    
    This will:
    1. Find all audio files in the input folder
    2. Analyze each file to detect its key
    3. Create folders for each Camelot key
    4. Copy (or move) files into their matching folders
    
    Example:
        python main.py organize --input /music/downloads --output /music/by_key
    """
    from file_manager.organizaer import organize_by_key
    
    print(f"\n📂 Organizing: {args.input} → {args.output}")
    print("-" * 40)
    
    organize_by_key(
        input_directory=args.input,
        output_directory=args.output,
        move_files=args.move
    )


def cmd_playlist(args):
    """
    Create a playlist of harmonically compatible songs.
    
    This creates an M3U playlist you can load in DJ software!
    
    Options:
    - --key: Only include songs compatible with this Camelot key
    - --bpm: Only include songs in this BPM range
    - --limit: Maximum number of songs
    
    Example:
        # Create a playlist in 8A, 120-130 BPM, max 20 songs
        python main.py playlist --input /music --output 8A.m3u --key 8A --bpm 120 130 --limit 20
    """
    from file_manager.organizaer import create_playlist
    
    # Parse BPM range if provided
    bpm_range = None
    if args.bpm:
        bpm_range = (args.bpm[0], args.bpm[1])
    
    print(f"\n📝 Creating playlist: {args.output}")
    if args.key:
        print(f"   Target Key: {args.key}")
    if bpm_range:
        print(f"   BPM Range: {bpm_range[0]}-{bpm_range[1]}")
    print("-" * 40)
    
    create_playlist(
        input_directory=args.input,
        output_file=args.output,
        target_key=args.key,
        bpm_range=bpm_range,
        max_songs=args.limit
    )


def cmd_find(args):
    """
    Find all audio files in a folder.
    
    Just lists what files are found - useful for checking
    what the tool can see before you try to analyze it.
    
    Example:
        python main.py find /music/downloads
    """
    from file_manager.organizaer import find_audio_files
    
    print(f"\n🔎 Searching in: {args.directory}")
    print("-" * 40)
    
    files = find_audio_files(args.directory)
    
    print(f"📁 Found {len(files)} audio files:\n")
    for f in sorted(files)[:50]:  # Show first 50
        print(f"   • {f}")
    
    if len(files) > 50:
        print(f"   ... and {len(files) - 50} more")


def cmd_compatible(args):
    """
    Check which keys are compatible with a given Camelot key.
    
    Harmonic mixing means playing songs that work well together.
    This tells you what keys you can mix to!
    
    Example:
        python main.py compatible 8A
    """
    from utils.camelot_map import get_harmonic_mixes, is_compatible_keys
    
    print(f"\n🎵 Compatible keys for {args.key}:")
    print("-" * 40)
    
    mixes = get_harmonic_mixes(args.key)
    
    if mixes:
        print(f"✅ You can mix {args.key} with:\n")
        for m in mixes:
            print(f"   🎼 {m}")
        print("\n💡 Tip: These keys are on the same spot or next to")
        print("   each other on the Camelot wheel - they'll sound good together!")
    else:
        print(f"❓ Could not find compatible keys for '{args.key}'")
        print("   Make sure you're using Camelot notation (e.g., '8A', '5B')")


def main():
    """
    Main entry point for the DJ Harmonic Analyzer.
    
    This sets up the command-line interface and routes
    commands to the appropriate functions.
    """
    print_welcome()
    
    # Create the argument parser
    # This handles all the command-line magic
    parser = argparse.ArgumentParser(
        description="DJ Harmonic Analyzer - Analyze and organize music by key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze song.mp3
  %(prog)s organize --input /music --output /organized
  %(prog)s playlist --input /music --output mix.m3u --key 8A
  %(prog)s compatible 8A
        """
    )
    
    # Add subcommands (the main actions)
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # ─────────────────────────────────────────────────────
    # Command: analyze
    # ─────────────────────────────────────────────────────
    parser_analyze = subparsers.add_parser('analyze', help='Analyze a single audio file')
    parser_analyze.add_argument('file', help='Path to audio file')
    
    # ─────────────────────────────────────────────────────
    # Command: organize
    # ─────────────────────────────────────────────────────
    parser_org = subparsers.add_parser('organize', help='Organize files by key')
    parser_org.add_argument('--input', required=True, help='Input directory')
    parser_org.add_argument('--output', required=True, help='Output directory')
    parser_org.add_argument('--move', action='store_true', 
                           help='Move files instead of copying (removes originals)')
    
    # ─────────────────────────────────────────────────────
    # Command: playlist
    # ─────────────────────────────────────────────────────
    parser_pl = subparsers.add_parser('playlist', help='Create harmonic playlist')
    parser_pl.add_argument('--input', required=True, help='Input directory')
    parser_pl.add_argument('--output', required=True, help='Output playlist file (.m3u)')
    parser_pl.add_argument('--key', help='Target Camelot key (e.g., 8A)')
    parser_pl.add_argument('--bpm', type=int, nargs=2, metavar=('MIN', 'MAX'),
                          help='BPM range filter')
    parser_pl.add_argument('--limit', type=int, default=20, help='Max songs (default: 20)')
    
    # ─────────────────────────────────────────────────────
    # Command: find
    # ─────────────────────────────────────────────────────
    parser_find = subparsers.add_parser('find', help='Find audio files in directory')
    parser_find.add_argument('directory', help='Directory to search')
    
    # ─────────────────────────────────────────────────────
    # Command: compatible
    # ─────────────────────────────────────────────────────
    parser_comp = subparsers.add_parser('compatible', help='Show compatible keys')
    parser_comp.add_argument('key', help='Camelot key (e.g., 8A)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'organize':
        cmd_organize(args)
    elif args.command == 'playlist':
        cmd_playlist(args)
    elif args.command == 'find':
        cmd_find(args)
    elif args.command == 'compatible':
        cmd_compatible(args)
    else:
        # No command specified - show help
        parser.print_help()
        print("\n🎧 Run with --help for more options!")


# This line makes the script runnable directly
# (python main.py) instead of just (python -m main)
if __name__ == "__main__":
    main()

