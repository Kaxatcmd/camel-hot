"""
Key Detection - Finding the Musical Key of a Song

This module contains the core logic for detecting the musical key
(and BPM) of an audio file.

Musical key detection works by:
1. Loading the audio file
2. Analyzing the frequency content (what notes are present)
3. Looking for patterns that match major or minor scales
4. Finding the strongest pitch profile to determine the key

Note: This is a simplified version. Real key detection is complex
and typically uses libraries like librosa or Essentia.
"""

# In a real implementation, you'd use audio processing libraries
# For this example, we'll show the structure and concepts

try:
    # Librosa is great for audio analysis
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("Tip: Install librosa for audio analysis with 'pip install librosa'")


# Standard musical keys and their frequency characteristics
# Each key has a unique "fingerprint" of which notes are emphasized
KEY_PROFILES = {
    # Major keys have a brighter, happier sound
    # The numbers represent how much each note is emphasized (0-1 scale)
    "C Major": {
        "C": 1.0, "D": 0.6, "E": 0.8, "F": 0.7, 
        "G": 0.9, "A": 0.5, "B": 0.6
    },
    "G Major": {
        "G": 1.0, "A": 0.6, "B": 0.8, "C": 0.7,
        "D": 0.9, "E": 0.5, "F#": 0.6
    },
    "D Minor": {
        "D": 1.0, "E": 0.5, "F": 0.6, "G": 0.8,
        "A": 0.7, "Bb": 0.5, "C": 0.6
    },
    # ... more keys would be defined here
}

# All notes in the chromatic scale (all 12 semitones)
ALL_NOTES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]


def _note_to_frequency(note_name):
    """
    Convert a note name to its frequency in Hz.
    
    Middle A (A4) is defined as 440 Hz - this is the tuning standard.
    All other notes are calculated relative to this.
    
    Example:
        A4 = 440 Hz
        A5 = 880 Hz (one octave higher)
        A3 = 220 Hz (one octave lower)
    """
    # This uses the formula: frequency = 440 * 2^((n-69)/12)
    # where n is the MIDI note number for that note
    pass  # Implementation would go here


def _find_strongest_pitch(y, sr):
    """
    Find the most dominant pitch/frequency in the audio.
    
    This looks at the audio waveform and finds the frequency
    that has the most energy - that's likely the root note!
    
    Args:
        y: The audio time series (waveform)
        sr: Sample rate (samples per second)
    
    Returns:
        The frequency in Hz of the strongest pitch
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        # Use librosa's pitch detection
        # This gives us the fundamental frequency (F0) over time
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        # Find the strongest pitch across all time
        strongest_pitch = 0
        max_magnitude = 0
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            magnitude = magnitudes[index, t]
            
            if magnitude > max_magnitude:
                max_magnitude = magnitude
                strongest_pitch = pitches[index, t]
        
        # Se não encontrou pitch com piptrack, tenta outra abordagem
        if strongest_pitch == 0:
            # Usar spectral centroid como fallback
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            strongest_pitch = spectral_centroids.mean()
        
        return strongest_pitch if strongest_pitch > 0 else None
    
    except Exception as e:
        print(f"Erro ao detectar pitch: {e}")
        return None


def _frequency_to_note(frequency):
    """
    Convert a frequency (Hz) to a note name.
    
    Given something like 440 Hz, this tells you it's A4 (A in octave 4).
    
    Args:
        frequency: Sound frequency in Hertz
    
    Returns:
        Note name like "A4" or "C#5"
    """
    if frequency <= 0:
        return "Unknown"
    
    # Formula in reverse: n = 12 * log2(frequency/440) + 69
    # This gives us the MIDI note number
    midi_note = 12 * (frequency / 440.0).bit_length() + 69
    # Wait, that's not right. Let me fix it...
    
    # Correct formula:
    # MIDI note number = 69 + 12 * log2(frequency / 440)
    import math
    midi_note = 69 + 12 * math.log2(frequency / 440)
    midi_note = round(midi_note)
    
    # Get the octave number (middle C is C4 = MIDI note 60)
    octave = midi_note // 12 - 1
    
    # Get the note within the octave (0-11)
    note_index = midi_note % 12
    
    return f"{ALL_NOTES[note_index]}{octave}"


def detect_key_from_audio(file_path):
    """
    Detect the musical key of an audio file.
    
    Usa análise chroma (12 notas musicais) para detectar a tonalidade.
    
    Args:
        file_path: Path to the audio file (mp3, wav, etc.)
    
    Returns:
        A dictionary with:
        - 'key': The detected key name (e.g., "C Major")
        - 'camelot': The Camelot notation (e.g., "8B")
        - 'confidence': How sure we are about this detection (0-1)
    """
    if not LIBROSA_AVAILABLE:
        return {
            "key": "Unknown - librosa not installed",
            "camelot": "Unknown",
            "confidence": 0.0
        }
    
    try:
        # Carregar áudio
        y, sr = librosa.load(file_path, duration=30)
        
        # Calcular chroma (energia de cada nota: C, C#, D, D#, E, F, etc)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Média da energia em cada nota ao longo do tempo
        chroma_mean = chroma.mean(axis=1)
        
        # Encontrar a nota com mais energia (root note)
        root_index = chroma_mean.argmax()
        confidence = chroma_mean[root_index]
        
        # Mapeamento de índice para nota
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        root_note = note_names[root_index]
        
        # Detectar se é major ou minor
        is_major = _guess_scale_type(chroma_mean)
        key_name = f"{root_note} {'Major' if is_major else 'Minor'}"
        
        # Converter para notação Camelot
        from utils.camelot_map import get_camelot_key
        camelot = get_camelot_key(key_name)
        
        return {
            "key": key_name,
            "camelot": camelot,
            "confidence": min(confidence, 1.0)
        }
    
    except Exception as e:
        print(f"Erro ao detectar tonalidade: {e}")
        return {
            "key": f"Erro ao detectar: {str(e)}",
            "camelot": "Unknown",
            "confidence": 0.0
        }


def _guess_scale_type(chroma_vector):
    """
    Guess whether a track is in a major or minor scale.
    
    Analisa o padrão de notas para determinar major/minor.
    Em escalas maiores, a 3ª e 5ª notas têm mais energia.
    Em escalas menores, a 3ª (menor) tem menos energia.
    """
    try:
        # padrão major: notas 0(root), 4(3ª maior), 7(5ª) têm mais energia
        # padrão minor: notas 0(root), 3(3ª menor), 7(5ª) têm mais energia
        
        if len(chroma_vector) < 8:
            return True  # padrão: major
        
        # Normalizar
        chroma_norm = chroma_vector / (chroma_vector.max() + 1e-10)
        
        # Score para major: 3ª maior (índice 4) tem mais energia que 3ª menor (índice 3)
        major_score = chroma_norm[4] - chroma_norm[3]
        
        return major_score > 0
    
    except:
        return True  # padrão: major


def detect_bpm(file_path):
    """
    Detect the BPM (beats per minute) of an audio file.
    
    BPM tells you how fast the tempo is - important for DJs
    to match tempos when mixing songs!
    
    Args:
        file_path: Path to the audio file
    
    Returns:
        BPM value as a number, or None if detection failed
    
    Example:
        >>> detect_bpm("house_track.mp3")
        128
    """
    if not LIBROSA_AVAILABLE:
        return None
    
    try:
        import warnings
        # Load the audio
        y, sr = librosa.load(file_path, duration=30)
        
        # Use librosa's beat tracking (com compatibilidade com versões)
        try:
            # Versão nova (librosa >= 0.10)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tempo = librosa.feature.rhythm.tempo(y=y, sr=sr)
                if hasattr(tempo, '__iter__'):
                    tempo = tempo[0] if len(tempo) > 0 else 0
        except (AttributeError, TypeError):
            # Versão antiga (librosa < 0.10)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tempo = librosa.beat.tempo(y=y, sr=sr)
                if hasattr(tempo, '__iter__'):
                    tempo = tempo[0] if len(tempo) > 0 else 0
        
        return round(tempo) if tempo > 0 else None
    
    except Exception as e:
        print(f"Erro ao detectar BPM: {e}")
        return None


def analyze_track(file_path):
    """
    Complete analysis of a track - key, BPM, and more.
    
    This gives you all the important musical information about
    a song in one call.
    
    Args:
        file_path: Path to the audio file
    
    Returns:
        Dictionary with:
        - file_path: Where the file is
        - key: Musical key name
        - camelot: Camelot notation
        - bpm: Beats per minute
        - duration: How long the track is (seconds)
    
    Example:
        >>> info = analyze_track("my_song.mp3")
        >>> print(f"This song is in {info['camelot']} at {info['bpm']} BPM")
        This song is in 8A at 120 BPM
    """
    if not LIBROSA_AVAILABLE:
        return {
            "file_path": file_path,
            "key": "Unknown - librosa not installed",
            "camelot": "Unknown",
            "bpm": None,
            "duration": None,
            "error": "Install librosa: pip install librosa"
        }
    
    try:
        # Load the full audio
        y, sr = librosa.load(file_path, duration=60)  # Carregar até 60 segundos
        duration = librosa.get_duration(y=y, sr=sr)
        
        print(f"🎵 Analisando: {file_path}")
        print(f"   ⏱️  Duração: {duration:.2f}s")
        
        # Get key and BPM
        print(f"   🔍 Detectando tonalidade...")
        key_info = detect_key_from_audio(file_path)
        
        print(f"   ⏱️  Detectando BPM...")
        bpm = detect_bpm(file_path)
        
        result = {
            "file_path": file_path,
            "key": key_info['key'],
            "camelot": key_info['camelot'],
            "bpm": bpm,
            "duration": round(duration, 2),
            "confidence": key_info['confidence']
        }
        
        print(f"   ✅ Análise completa!")
        print(f"      • Tonalidade: {result['key']}")
        print(f"      • Camelot: {result['camelot']}")
        print(f"      • BPM: {result['bpm']}")
        
        return result
    
    except Exception as e:
        print(f"❌ Erro ao analisar {file_path}: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "file_path": file_path,
            "key": f"Erro: {str(e)}",
            "camelot": "Unknown",
            "bpm": None,
            "duration": None
        }

