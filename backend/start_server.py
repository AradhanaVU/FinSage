#!/usr/bin/env python
"""Simple script to start the server and show any errors"""
import sys
import traceback

try:
    print("Starting server...")
    import uvicorn
    from app.main import app
    print("✓ App imported successfully!")
    # Try ports 8000, 8001, 8002, etc. until we find a free one
    import socket
    port = 8000
    max_attempts = 10
    
    for attempt in range(max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            break  # Port is free, use it
        except OSError:
            port += 1
            if attempt == max_attempts - 1:
                print(f"ERROR: Could not find a free port after {max_attempts} attempts")
                sys.exit(1)
    
    if port != 8000:
        print(f"Port 8000 is busy, using port {port} instead")
    
    print(f"Starting uvicorn on http://127.0.0.1:{port}")
    print(f"Frontend should connect to: http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

