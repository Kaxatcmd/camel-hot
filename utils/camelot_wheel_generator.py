"""
Camelot Wheel Generator
Generates a beautiful visual representation of the Camelot wheel for harmonic mixing
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Wedge, Polygon
import numpy as np
from pathlib import Path


def generate_camelot_wheel(output_path="assets/camelot_wheel.png", size=(800, 800)):
    """
    Generate a beautiful Camelot wheel visualization.
    
    The Camelot wheel shows 24 musical keys arranged in a circle:
    - 12 minor keys (1A-12A) on the inner ring
    - 12 major keys (1B-12B) on the outer ring
    - Keys are arranged by harmonic compatibility
    
    Args:
        output_path: Where to save the wheel image
        size: Tuple of (width, height) in pixels
    """
    
    # Create figure with dark background
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    ax.set_aspect('equal')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')
    
    # Camelot wheel order (harmonic relationship)
    minor_keys = ['8A', '3A', '10A', '5A', '12A', '7A', '2A', '9A', '4A', '11A', '6A', '1A']
    major_keys = ['8B', '3B', '10B', '5B', '12B', '7B', '2B', '9B', '4B', '11B', '6B', '1B']
    
    # Color scheme - gradient from cool to warm
    colors_minor = plt.cm.hsv(np.linspace(0, 1, 12))
    colors_major = plt.cm.hsv(np.linspace(0, 1, 12))
    
    # Adjust colors for better visibility
    colors_minor = plt.cm.tab20(np.linspace(0, 1, 12))
    colors_major = plt.cm.Set3(np.linspace(0, 1, 12))
    
    # Draw outer circle border
    outer_circle = Circle((0, 0), 1.35, fill=False, edgecolor='#fff', linewidth=3)
    ax.add_patch(outer_circle)
    
    # Draw middle circle border
    middle_circle = Circle((0, 0), 0.85, fill=False, edgecolor='#888', linewidth=2, linestyle='--')
    ax.add_patch(middle_circle)
    
    # Draw inner circle
    inner_circle = Circle((0, 0), 0.1, fill=True, facecolor='#222', edgecolor='#fff', linewidth=2)
    ax.add_patch(inner_circle)
    
    angles = np.linspace(0, 2 * np.pi, 13)[:-1]  # 12 positions
    
    # Draw major keys (outer ring)
    for i, (angle, key, color) in enumerate(zip(angles, major_keys, colors_major)):
        x = 1.1 * np.cos(angle - np.pi/2)
        y = 1.1 * np.sin(angle - np.pi/2)
        
        # Draw key segment
        wedge = Wedge((0, 0), 1.35, np.degrees(angle - np.pi/2 - np.pi/12), 
                      np.degrees(angle - np.pi/2 + np.pi/12), 
                      facecolor=color, edgecolor='#fff', linewidth=1.5, alpha=0.7)
        ax.add_patch(wedge)
        
        # Add key label
        ax.text(x, y, key, fontsize=14, fontweight='bold', ha='center', va='center',
                color='#fff', bbox=dict(boxstyle='circle,pad=0.3', facecolor='#000', alpha=0.7))
    
    # Draw minor keys (inner ring)
    for i, (angle, key, color) in enumerate(zip(angles, minor_keys, colors_minor)):
        x = 0.6 * np.cos(angle - np.pi/2)
        y = 0.6 * np.sin(angle - np.pi/2)
        
        # Draw key segment
        wedge = Wedge((0, 0), 0.85, np.degrees(angle - np.pi/2 - np.pi/12), 
                      np.degrees(angle - np.pi/2 + np.pi/12), 
                      facecolor=color, edgecolor='#fff', linewidth=1.5, alpha=0.7)
        ax.add_patch(wedge)
        
        # Add key label
        ax.text(x, y, key, fontsize=12, fontweight='bold', ha='center', va='center',
                color='#fff', bbox=dict(boxstyle='circle,pad=0.2', facecolor='#000', alpha=0.7))
    
    # Add center text
    ax.text(0, 0, 'CAMELOT\nWHEEL', fontsize=10, ha='center', va='center',
            color='#fff', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#000', alpha=0.8, edgecolor='#fff', linewidth=1))
    
    # Add legend
    ax.text(-1.4, -1.3, 'Inner Ring: Minor Keys (A)\nOuter Ring: Major Keys (B)',
            fontsize=10, color='#ccc', family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#222', alpha=0.9, edgecolor='#555', linewidth=1))
    
    # Add compatibility note
    ax.text(1.35, -1.3, 'Adjacent keys are harmonically compatible',
            fontsize=9, color='#aaa', ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#222', alpha=0.9, edgecolor='#555', linewidth=1))
    
    # Create output directory if needed
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with high DPI
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a', edgecolor='none')
    plt.close()
    
    return str(output_file.absolute())


if __name__ == '__main__':
    path = generate_camelot_wheel()
    print(f"✓ Camelot wheel generated: {path}")
