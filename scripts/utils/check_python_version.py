#!/usr/bin/env python3
"""
Check Python version compatibility for Pocket Link Manager
"""

import sys
import io

# Handle Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MIN_PYTHON_MAJOR = 3
MIN_PYTHON_MINOR = 12
RECOMMENDED_PYTHON_MINOR = 13

def check_python_version():
    """Check if Python version meets requirements"""
    current_version = sys.version_info
    current_version_str = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    
    print("Python Version Check")
    print("=" * 50)
    print(f"Current version: {current_version_str}")
    print(f"Minimum required: {MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR}.0")
    print(f"Recommended: {MIN_PYTHON_MAJOR}.{RECOMMENDED_PYTHON_MINOR}.0+")
    print("=" * 50)
    
    # Check minimum version
    if (current_version.major < MIN_PYTHON_MAJOR or 
        (current_version.major == MIN_PYTHON_MAJOR and current_version.minor < MIN_PYTHON_MINOR)):
        print(f"[X] ERROR: Python {current_version_str} is below minimum required version {MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR}.0")
        print(f"   Please upgrade to Python 3.12 or higher")
        return False
    
    # Check if recommended version
    if (current_version.major == MIN_PYTHON_MAJOR and current_version.minor >= RECOMMENDED_PYTHON_MINOR):
        print(f"[OK] SUCCESS: Python {current_version_str} meets recommended version")
        print(f"   You're using the latest recommended version!")
    elif (current_version.major == MIN_PYTHON_MAJOR and current_version.minor >= MIN_PYTHON_MINOR):
        print(f"[!] WARNING: Python {current_version_str} meets minimum requirements")
        print(f"   Consider upgrading to Python 3.13+ for better performance")
    
    # Check for deprecation warnings
    if current_version.major == 3 and current_version.minor >= 12:
        print(f"\n[NOTE] You may see deprecation warnings for datetime.utcnow()")
        print(f"   These are non-breaking and will be addressed before Python 3.14")
    
    return True

if __name__ == '__main__':
    success = check_python_version()
    sys.exit(0 if success else 1)
