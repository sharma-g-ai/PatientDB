#!/usr/bin/env python3
"""
Healthix Patient Chat - Main Application Launcher
This script starts the backend server with enhanced file attachment functionality.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("🏥 Starting Healthix Patient Chat with File Attachments...")
    
    # Check if we're in the right directory
    if not Path("backend/main.py").exists():
        print("❌ Please run this script from the PatientDB root directory")
        return 1
    
    # Change to backend directory
    os.chdir("backend")
    
    print("📦 Checking dependencies...")
    try:
        subprocess.run([sys.executable, "-c", "import fastapi, uvicorn"], check=True, capture_output=True)
        print("✅ Core dependencies found")
    except subprocess.CalledProcessError:
        print("❌ Missing dependencies. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "../requirements.txt"])
    
    print("🚀 Starting backend server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("💬 Enhanced chat interface at: http://localhost:8000/chat")
    print("📎 File attachment functionality enabled")
    print("📊 Supports: PDF, Excel, CSV, Images, Text files")
    print("")
    print("🔧 Available endpoints:")
    print("   • http://localhost:8000/chat - Enhanced chat with file attachments")
    print("   • http://localhost:8000/interface - Direct React interface")  
    print("   • http://localhost:8000/docs - API documentation")
    print("")
    
    # Start the server
    try:
        # Give a moment then open browser
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://localhost:8000/chat")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start server
        subprocess.run([sys.executable, "main.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())