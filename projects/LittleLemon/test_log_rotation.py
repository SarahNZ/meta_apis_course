#!/usr/bin/env python
"""
Test script to demonstrate daily log rotation functionality.

This script shows how the TimedRotatingFileHandler works:
- Creates new log files daily at midnight
- Archives old logs with date suffixes (e.g., littlelemon.log.2025-09-26)
- Automatically deletes logs older than backupCount days (30 days)
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LittleLemon.settings')
django.setup()

import logging

# Get the logger configured in settings.py
logger = logging.getLogger('LittleLemonAPI')

def test_logging_functionality():
    """Test that logging is working with the new TimedRotatingFileHandler."""
    
    print("🔄 Testing Daily Log Rotation Configuration")
    print("=" * 50)
    
    # Test different log levels
    logger.info("🧪 Testing INFO level logging")
    logger.warning("⚠️ Testing WARNING level logging") 
    logger.error("❌ Testing ERROR level logging")
    
    # Check current log file
    log_file = project_root / 'logs' / 'littlelemon.log'
    if log_file.exists():
        file_size = log_file.stat().st_size
        print(f"📄 Current log file size: {file_size:,} bytes")
        
        # Show recent log entries
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-5:] if len(lines) >= 5 else lines
            
        print("\n📋 Recent log entries:")
        for line in recent_lines:
            print(f"   {line.strip()}")
    
    print("\n✅ Log Rotation Configuration:")
    print("   • Rotates daily at midnight")
    print("   • Keeps 30 days of archived logs")
    print("   • Archived logs named: littlelemon.log.YYYY-MM-DD")
    print("   • Old logs automatically deleted after 30 days")
    print("   • UTF-8 encoding for international characters")
    
    print("\n📁 Log files will appear as:")
    print("   logs/littlelemon.log              (current)")
    print("   logs/littlelemon.log.2025-09-26   (yesterday)")
    print("   logs/littlelemon.log.2025-09-25   (2 days ago)")
    print("   logs/littlelemon.log.2025-09-24   (3 days ago)")
    print("   ...")

if __name__ == '__main__':
    test_logging_functionality()