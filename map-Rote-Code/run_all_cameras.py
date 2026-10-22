import subprocess
import os
import sys
import time
import signal
import requests

# ---------- CONFIG ----------
BACKEND_URL = "http://127.0.0.1:8000/admin"
ORG_ID = "ORG_001" # Unique ID for each client you deploy to

# List of camera node directories relative to this script
CAMERA_NODES = [
    "camera_node/camera1",
    "camera_node/camera2"
]

processes = []

def log_event(level, source, message):
    """Sends a log entry to the Admin Dashboard registry."""
    try:
        url = f"{BACKEND_URL}/add-log?level={level}&source={source}&message={message}&org_id={ORG_ID}"
        requests.post(url, timeout=2)
    except:
        pass # Don't crash the launcher if logs fail

def signal_handler(sig, frame):
    print("\n\n🛑 Shutting down all cameras...")
    log_event("WARNING", "Launcher", "System manually stopped by developer (Ctrl+C)")
    for name, p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def launch():
    print("🚀 SMART PARKING: Starting All Camera Nodes...")
    print("---------------------------------------------")
    log_event("INFO", "Launcher", "Starting all camera nodes...")
    
    root_dir = os.getcwd()
    
    for node in CAMERA_NODES:
        node_path = os.path.join(root_dir, node)
        main_script = os.path.join(node_path, "main.py")
        
        if os.path.exists(main_script):
            print(f"✅ Starting {node}...")
            # Start process in its own folder context
            p = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=node_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes.append((node, p))
        else:
            print(f"❌ Error: {main_script} not found.")
            log_event("ERROR", "Launcher", f"File missing: {main_script}")

    print("\n✨ All cameras are running! Data is flowing to the Dashboard.")
    print("👉 Press Ctrl+C to stop all cameras at once.\n")

    # Keep track of which cameras we've already reported as dead
    dead_cameras = set()

    # Monitor and print logs
    while True:
        still_running = False
        for i, (name, p) in enumerate(processes):
            # Check if process is still alive
            exit_code = p.poll()
            
            if exit_code is None:
                still_running = True
                # Try to read output without blocking
                try:
                    line = p.stdout.readline()
                    if line:
                        print(f"[{name.upper()}] {line.strip()}")
                except:
                    pass
            else:
                if name not in dead_cameras:
                    msg = f"{name.upper()} has gone OFFLINE! (Exit Code: {exit_code})"
                    print(f"\n🚨 ALERT: {msg}")
                    print(f"👉 Please check its folder and config settings.\n")
                    log_event("CRITICAL", f"Node_{name}", msg)
                    dead_cameras.add(name)
        
        # If all cameras are dead, we can exit or just wait
        if not still_running and len(dead_cameras) == len(processes):
            print("⚠️ All camera nodes have stopped. Exiting launcher...")
            log_event("WARNING", "Launcher", "All camera nodes reached termination.")
            break
            
        time.sleep(0.01)

if __name__ == "__main__":
    launch()
