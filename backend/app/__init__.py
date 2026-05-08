"""
Backend Application Initialization Module
Sets up comprehensive logging for all backend operations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_setup import setup_comprehensive_logging

# Initialize comprehensive logging when the backend app module is imported
setup_comprehensive_logging()