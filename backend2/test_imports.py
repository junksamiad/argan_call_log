#!/usr/bin/env python3
"""
Quick import test to verify all existing_email_handler imports work
"""

import sys
import os

# Add the backend2 directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_existing_email_imports():
    """Test all imports used in existing_email_handler.py"""
    print("🧪 Testing existing_email_handler imports...")
    
    try:
        # Test basic imports
        print("✓ Testing basic imports...")
        import logging
        import re
        import json
        from typing import Dict, Any, List, Optional
        print("  ✅ Basic imports successful")
        
        # Test models import
        print("✓ Testing models import...")
        from models.email_context import EmailContext
        print("  ✅ EmailContext import successful")
        
        # Test utilities import
        print("✓ Testing database utilities import...")
        from database import extract_email_date_from_headers
        print("  ✅ database.extract_email_date_from_headers import successful")
        
        # Test ai_agents imports
        print("✓ Testing ai_agents imports...")
        from ai_agents import ConversationParsingAgent1
        print("  ✅ ConversationParsingAgent1 import successful")
        
        # Test ConversationParsingAgent2 import (used in the else clause)
        print("✓ Testing ConversationParsingAgent2 import...")
        from ai_agents import ConversationParsingAgent2
        print("  ✅ ConversationParsingAgent2 import successful")
        
        # Test database table import (used in get_existing_record function)
        print("✓ Testing database table import...")
        from database import table
        print("  ✅ database.table import successful")
        
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("✅ existing_email_handler.py should work without import errors")
        return True
        
    except ImportError as e:
        print(f"\n❌ IMPORT FAILED: {e}")
        print("🚨 existing_email_handler.py will fail with import errors")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_existing_email_imports()
    sys.exit(0 if success else 1) 