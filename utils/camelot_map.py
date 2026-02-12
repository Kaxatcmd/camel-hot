"""
Camelot Wheel Mapping - Harmonic Mixing Helper

The Camelot system is a way to represent musical keys using numbers (1-12)
and letters (A for major, B for minor). This makes it easy for DJs to mix
songs that sound good together harmonically.

Example: "8A" means C# Minor, and it can mix with:
  - Same key: 8A
  - Relative major: 8B (A# Major / C# Minor are the same key)
  - +/- 1 hour on the wheel: 7A, 9A, 8B, 8A
"""

# Think of the Camelot wheel like a clock:
# - Numbers 1-12 represent the 12 musical notes
# - 'A' = Major scale (happy, bright sound)
# - 'B' = Minor scale (sad, dark sound)

# This dictionary maps standard key names to their Camelot notation
# The key is the "musical" name, the value is the Camelot code
CAMELOT_MAP = {
    # Major Keys (the "A" circle)
    "C Major": "8B",
    "C# Major": "3B",  # Also called Db Major
    "D Major": "10B",
    "Eb Major": "3B",  # Also called D# Major
    "E Major": "7B",
    "F Major": "2B",
    "F# Major": "9B",  # Also called Gb Major
    "G Major": "4B",
    "Ab Major": "9B",  # Also called G# Major
    "A Major": "11B",
    "Bb Major": "6B",  # Also called A# Major
    "B Major": "1B",
    
    # Minor Keys (the "A" circle)
    "C Minor": "5A",
    "C# Minor": "12A",  # Also called Db Minor
    "D Minor": "7A",
    "D# Minor": "2A",   # Also called Eb Minor
    "E Minor": "9A",
    "F Minor": "4A",
    "F# Minor": "11A",  # Also called Gb Minor
    "G Minor": "6A",
    "G# Minor": "1A",   # Also called Ab Minor
    "A Minor": "8A",
    "A# Minor": "3A",   # Also called Bb Minor
    "B Minor": "10A",
}

# Sometimes you need to know the relative key - the "twin" key
# that uses the same notes but different mood (major vs minor)
# Example: C Major (8B) and A Minor (8A) use the same notes!
RELATIVE_KEYS = {
    "C Major": "A Minor",
    "A Minor": "C Major",
    "C# Major": "A# Minor",
    "A# Minor": "C# Major",
    "D Major": "B Minor",
    "B Minor": "D Major",
    "Eb Major": "C Minor",
    "C Minor": "Eb Major",
    "E Major": "C# Minor",
    "C# Minor": "E Major",
    "F Major": "D Minor",
    "D Minor": "F Major",
    "F# Major": "D# Minor",
    "D# Minor": "F# Major",
    "G Major": "E Minor",
    "E Minor": "G Major",
    "Ab Major": "F Minor",
    "F Minor": "Ab Major",
    "A Major": "F# Minor",
    "F# Minor": "A Major",
    "Bb Major": "G Minor",
    "G Minor": "Bb Major",
    "B Major": "G# Minor",
    "G# Minor": "B Major",
}


def get_camelot_key(standard_key_name):
    """
    Convert a standard musical key name to Camelot notation.
    
    This is like translating from "musical speak" to "DJ speak".
    
    Args:
        standard_key_name: Something like "C Major" or "A Minor"
    
    Returns:
        Camelot code like "8B" or "5A"
    
    Example:
        >>> get_camelot_key("C Major")
        '8B'
        >>> get_camelot_key("A Minor")
        '8A'
    """
    # Just look it up in our dictionary - simple as that!
    return CAMELOT_MAP.get(standard_key_name, "Unknown")


def get_relative_minor(camelot_code):
    """
    Get the relative minor/major key from a Camelot code.
    
    If you have "8B" (C Major), this gives you "8A" (A Minor).
    They use the same notes but sound different!
    
    Args:
        camelot_code: Something like "8B" or "5A"
    
    Returns:
        The related key code, or None if not found
    
    Example:
        >>> get_relative_minor("8B")
        '8A'
        >>> get_relative_minor("8A")
        '8B'
    """
    # Split "8B" into number "8" and letter "B"
    if len(camelot_code) < 2:
        return None
    
    number = camelot_code[:-1]
    letter = camelot_code[-1]
    
    # Flip the letter: A becomes B, B becomes A
    new_letter = "A" if letter == "B" else "B"
    
    return number + new_letter


def is_compatible_keys(key1, key2):
    """
    Check if two Camelot keys can be mixed together harmonically.
    
    Think of it like this: on the Camelot wheel, compatible keys
    are next to each other or at the same spot. You can mix these
    and they'll sound good!
    
    Args:
        key1: First Camelot code like "8A"
        key2: Second Camelot code like "8A" or "7A"
    
    Returns:
        True if the keys work together, False otherwise
    
    Example:
        >>> is_compatible_keys("8A", "8A")  # Same key
        True
        >>> is_compatible_keys("8A", "7A")  # One step away
        True
        >>> is_compatible_keys("8A", "5B")  # Random combo - not good
        False
    """
    # Can't compare if we don't have valid keys
    if len(key1) < 2 or len(key2) < 2:
        return False
    
    try:
        # Extract the number parts (8 and 8 from "8A" and "8A")
        num1 = int(key1[:-1])
        num2 = int(key2[:-1])
        
        # Extract the letter parts (A and A)
        letter1 = key1[-1]
        letter2 = key2[-1]
        
        # If letters are different (one major, one minor), 
        # they're compatible only if numbers match exactly
        # Example: "8A" and "8B" are the same key, just major/minor
        if letter1 != letter2:
            return num1 == num2
        
        # Same letter? Then numbers must be the same or differ by 1
        # This means they're on the same spot or next to each other
        diff = abs(num1 - num2)
        
        # Numbers match exactly OR they're one step apart
        # (wrapping around from 12 to 1 is also fine!)
        return diff == 0 or diff == 1 or diff == 11
    
    except (ValueError, IndexError):
        # Something went wrong - not valid Camelot codes
        return False


def get_harmonic_mixes(camelot_code):
    """
    Get all keys that work well with a given Camelot key.
    
    This gives you a list of "safe" keys to mix to - the DJ's
    harmonic playground!
    
    Args:
        camelot_code: Something like "8A"
    
    Returns:
        List of compatible Camelot codes
    
    Example:
        >>> get_harmonic_mixes("8A")
        ['7A', '8A', '9A', '8B']  # The classic compatible keys
    """
    if len(camelot_code) < 2:
        return []
    
    try:
        number = int(camelot_code[:-1])
        letter = camelot_code[-1]
        
        # Calculate the three compatible numbers:
        # 1. Same number (the same spot on the wheel)
        # 2. One less (one hour counter-clockwise)
        # 3. One more (one hour clockwise)
        # We use % 12 and add 1 because the numbers are 1-12, not 0-11
        prev_num = ((number - 2) % 12) + 1
        next_num = (number % 12) + 1
        
        # The same key in major/minor (relative key)
        relative = get_relative_minor(camelot_code)
        
        # Combine them all!
        compatible = [
            f"{prev_num}{letter}",  # One step back
            f"{number}{letter}",    # Same spot
            f"{next_num}{letter}",  # One step forward
        ]
        
        # Add the relative key if we found it
        if relative:
            compatible.append(relative)
        
        return compatible
    
    except (ValueError, IndexError):
        return []


def get_compatible_keys(camelot_code):
    """
    Get all keys compatible with the given Camelot key.
    
    Alias para get_harmonic_mixes() para manter compatibilidade.
    
    Args:
        camelot_code: Camelot code like "8A"
    
    Returns:
        List of compatible Camelot codes
    """
    return get_harmonic_mixes(camelot_code)

def get_harmonic_path(start_key, end_key, max_steps=12):
    """
    Find a harmonic mixing path from one key to another.
    
    This calculates a sequence of keys that can be mixed together
    to transition smoothly from start to end. Each step is harmonic!
    
    Args:
        start_key: Starting Camelot code (e.g., "8A")
        end_key: Target Camelot code (e.g., "3B")
        max_steps: Maximum number of steps to allow
    
    Returns:
        List of Camelot codes that form a harmonic path
    
    Example:
        >>> get_harmonic_path("8A", "8B")
        ['8A', '8B']
        >>> get_harmonic_path("8A", "9A")
        ['8A', '9A']
    """
    if len(start_key) < 2 or len(end_key) < 2:
        return [start_key]
    
    try:
        path = [start_key]
        current = start_key
        
        for _ in range(max_steps):
            if current == end_key:
                break
            
            # Get compatible keys from current position
            compatible = get_harmonic_mixes(current)
            
            # Try to find the best next step towards the end key
            best_next = None
            best_distance = float('inf')
            
            for candidate in compatible:
                if candidate not in path:
                    # Calculate distance to target
                    try:
                        curr_num = int(current[:-1])
                        target_num = int(end_key[:-1])
                        cand_num = int(candidate[:-1])
                        
                        # Distance is how far candidate is from target
                        distance = abs(cand_num - target_num)
                        # Account for wheel wrap-around
                        distance = min(distance, 12 - distance)
                        
                        if distance < best_distance:
                            best_distance = distance
                            best_next = candidate
                    except ValueError:
                        continue
            
            if best_next and best_next not in path:
                path.append(best_next)
                current = best_next
            else:
                break
        
        # If we haven't reached the target, try a direct movement
        if current != end_key and len(path) < max_steps:
            path.append(end_key)
        
        return path
    
    except (ValueError, IndexError):
        return [start_key]


def generate_harmonic_sequence(start_key, length=8, direction='forward'):
    """
    Generate a harmonic mixing sequence from a starting key.
    
    This creates a DJ-style mixing path where you move around the
    Camelot wheel, each step being compatible with the previous.
    
    Args:
        start_key: Starting Camelot code (e.g., "8A")
        length: How many keys in the sequence
        direction: 'forward', 'backward', or 'zigzag'
    
    Returns:
        List of Camelot codes forming a harmonic sequence
    
    Example:
        >>> generate_harmonic_sequence("8A", 4, "forward")
        ['8A', '9A', '10A', '11A']
        
        >>> generate_harmonic_sequence("8A", 4, "zigzag")
        ['8A', '8B', '9A', '9B']
    """
    if length <= 0:
        return []
    
    sequence = [start_key]
    current = start_key
    
    if len(start_key) < 2:
        return sequence
    
    try:
        current_num = int(start_key[:-1])
        current_letter = start_key[-1]
        
        for i in range(1, length):
            if direction == 'forward':
                # Move forward on the wheel
                next_num = (current_num % 12) + 1
                sequence.append(f"{next_num}{current_letter}")
                current_num = next_num
                
            elif direction == 'backward':
                # Move backward on the wheel
                next_num = ((current_num - 2) % 12) + 1
                sequence.append(f"{next_num}{current_letter}")
                current_num = next_num
                
            elif direction == 'zigzag':
                # Alternate between letter A and B (major/minor)
                new_letter = 'B' if current_letter == 'A' else 'A'
                sequence.append(f"{current_num}{new_letter}")
                current_letter = new_letter
        
        return sequence
    
    except (ValueError, IndexError):
        return sequence


def get_relative_key_chain(start_key, length=4):
    """
    Get a chain of relative major/minor keys.
    
    Useful for creating playlists that stay in the same tonality
    but alternate between major and minor flavors.
    
    Args:
        start_key: Starting Camelot code (e.g., "8A")
        length: How many keys in the chain
    
    Returns:
        List of alternating major/minor Camelot codes
    
    Example:
        >>> get_relative_key_chain("8A", 4)
        ['8A', '8B', '8A', '8B']
    """
    if length <= 0:
        return []
    
    chain = [start_key]
    current = start_key
    
    for _ in range(length - 1):
        relative = get_relative_minor(current)
        if relative:
            chain.append(relative)
            current = relative
        else:
            break
    
    return chain


def find_camelot_wheel_distance(key1, key2):
    """
    Calculate the distance between two keys on the Camelot wheel.
    
    Distance is measured as steps around the wheel (0-6 steps).
    Useful for understanding how far apart two keys are musically.
    
    Args:
        key1: First Camelot code (e.g., "8A")
        key2: Second Camelot code (e.g., "3A")
    
    Returns:
        Distance in steps (0-6)
    
    Example:
        >>> find_camelot_wheel_distance("8A", "8A")  # Same
        0
        >>> find_camelot_wheel_distance("8A", "9A")  # Adjacent
        1
        >>> find_camelot_wheel_distance("8A", "3A")  # Far
        5
    """
    if len(key1) < 2 or len(key2) < 2:
        return None
    
    try:
        # Extract numbers
        num1 = int(key1[:-1])
        num2 = int(key2[:-1])
        letter1 = key1[-1]
        letter2 = key2[-1]
        
        # If different letters (A vs B), they're at same number position
        if letter1 != letter2:
            return 0
        
        # Same letter - calculate steps around the wheel
        distance = abs(num1 - num2)
        # Account for wheel wrap-around
        distance = min(distance, 12 - distance)
        
        return distance
    
    except (ValueError, IndexError):
        return None