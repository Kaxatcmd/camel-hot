#!/usr/bin/env python3
"""
CAMEL-HOT Logo Setup Utility

This script helps verify and set up the new CAMEL-HOT logo in the correct location.
Run this to check your logo setup and verify the application is ready!
"""

import os
import sys
from pathlib import Path

def check_assets_directory():
    """Check if assets directory exists and is accessible"""
    assets_path = Path(__file__).parent / "assets"
    
    if not assets_path.exists():
        print("❌ Assets directory not found!")
        print(f"   Expected at: {assets_path}")
        return False
    
    print(f"✅ Assets directory found: {assets_path}")
    return True

def check_logo_files():
    """Check for any existing logo files"""
    assets_path = Path(__file__).parent / "assets"
    logo_formats = ["camel_mascot.png", "camel_mascot.jpg", "camel_mascot.jpeg", "camel_mascot.svg"]
    
    found_logos = []
    for logo_name in logo_formats:
        logo_path = assets_path / logo_name
        if logo_path.exists():
            size = logo_path.stat().st_size
            found_logos.append((logo_name, size))
            print(f"✅ Found: {logo_name} ({size} bytes)")
    
    if not found_logos:
        print("ℹ️  No logo files found (placeholder will be used)")
        return False
    
    return True

def check_gui_file():
    """Verify GUI file is updated with new styling"""
    gui_path = Path(__file__).parent / "gui" / "main_window.py"
    
    if not gui_path.exists():
        print(f"❌ GUI file not found: {gui_path}")
        return False
    
    with open(gui_path, 'r') as f:
        content = f.read()
    
    # Check for desert sunset theme indicators
    if "desert" in content.lower() or "camel_mascot.png" in content:
        print("✅ GUI file is updated with new styling")
        return True
    else:
        print("⚠️  GUI file may need updates")
        return False

def print_setup_instructions():
    """Print instructions for setting up the logo"""
    print("\n" + "="*60)
    print("📝 LOGO SETUP INSTRUCTIONS")
    print("="*60)
    
    assets_path = Path(__file__).parent / "assets"
    
    print(f"\n1. Save your CAMEL-HOT logo image to:")
    print(f"   📁 {assets_path}/camel_mascot.png")
    print(f"      (or .jpg, .jpeg, .svg)")
    
    print(f"\n2. Supported formats (in order of preference):")
    print(f"   ✓ PNG (.png) - Best quality with transparency")
    print(f"   ✓ JPEG (.jpg, .jpeg) - Good quality, no transparency")
    print(f"   ✓ SVG (.svg) - Scalable vector graphics")
    
    print(f"\n3. Restart the application:")
    print(f"   $ python main.py")
    
    print(f"\n4. You should see:")
    print(f"   ✓ Beautiful desert sunset gradient background")
    print(f"   ✓ Your CAMEL-HOT logo displayed")
    print(f"   ✓ Enhanced UI with professional styling")

def print_status_report():
    """Print a complete status report"""
    print("\n" + "="*60)
    print("🐪 CAMEL-HOT Application Status Report")
    print("="*60 + "\n")
    
    checks = [
        ("Assets Directory", check_assets_directory),
        ("Logo Files", check_logo_files),
        ("GUI Updates", check_gui_file),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n🔍 Checking: {name}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ OK" if result else "⚠️  NEEDS ATTENTION"
        print(f"{name:<30} {status}")
    
    all_ok = all(result for _, result in results)
    
    if all_ok:
        print("\n🎉 System is ready!")
    else:
        print("\n⚠️  Some items need attention. See instructions above.")
    
    print_setup_instructions()

def main():
    """Main entry point"""
    try:
        print_status_report()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
