import subprocess
import time
import os
import sys
import socket
import qrcode
import re

def kill_existing_processes():
    """Cleans up old processes to free up ports 8000 and 8501."""
    print("🧹 Cleaning up old processes...")
    ports = [8000, 8501]
    for port in ports:
        try:
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True, text=True)
            for line in output.splitlines():
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if int(pid) != os.getpid():
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
        except:
            pass
    time.sleep(1)

def start_backend():
    print("🚀 Starting Backend API...")
    # Bind to 127.0.0.1 to bypass public firewall blocks
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"], cwd="backend")

def start_cameras():
    print("📷 Starting Camera Nodes...")
    return subprocess.Popen([sys.executable, "run_all_cameras.py"])

def start_navigator():
    print("📍 Starting Smart Wayfinder...")
    # Bind to 127.0.0.1 to bypass public firewall blocks.
    # The Tunnel will forward traffic to this local address.
    return subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "navigator.py", 
        "--server.port", "8501", 
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false"
    ], cwd="dashboard", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def generate_qr(url, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"🔗 Generated QR for: {url} -> {filename}")

def main():
    print("="*60)
    print("🛡️  SMART PARKING: STEALTH TUNNEL LAUNCHER")
    print("-" * 60)
    print("💡 This launcher bypasses McAfee by using a secure cloud bridge.")
    print("="*60)
    
    kill_existing_processes()
    
    # 1. Start Services
    backend = start_backend()
    cameras = start_cameras()
    navigator = start_navigator()
    
    print("\n⏳ Initializing services... (Waiting for Navigator to be ready)")
    
    # 2. DYNAMIC PORT CHECK (Fast Startup)
    # Instead of waiting 15s, we check if the port is open every 0.1s
    navigator_ready = False
    start_time = time.time()
    while time.time() - start_time < 30: # Max 30s timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', 8501)) == 0:
                navigator_ready = True
                break
        time.sleep(0.5)

    if not navigator_ready:
        print("❌ Error: Navigator failed to start within 30 seconds.")
        backend.terminate()
        cameras.terminate()
        navigator.terminate()
        return

    # 3. Start Secure Tunnel (localhost.run)
    print("\n🚀 Bypassing Firewall... Creating Secure HTTPS Link...")
    tunnel_cmd = ["ssh", "-R", "80:127.0.0.1:8501", "nokey@localhost.run"]
    
    try:
        tunnel_proc = subprocess.Popen(tunnel_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        
        secure_url = None
        start_wait = time.time()
        while time.time() - start_wait < 30:
            line = tunnel_proc.stdout.readline()
            if not line: break
            
            # Look for the generated HTTPS link
            match = re.search(r'https://[a-zA-Z0-9.-]+\.lhr\.life', line)
            if match:
                secure_url = match.group(0)
                # 1. Gate QR (Instant 90s)
                generate_qr(f"{secure_url}?mode=gate", "entry_gate_qr.png")
                # 2. Home QR (Pre-book 45m)
                generate_qr(f"{secure_url}?mode=home", "home_prebook_qr.png")
                
                print("\n" + "🔥"*20)
                print("🏁 ENTRY GATE QR IS READY!")
                print(f"👉 SCAN THIS LINK: {secure_url}?mode=gate")
                print("🔥"*20 + "\n")

                # ASCII for quick terminal scanning
                qr_gate = qrcode.QRCode()
                qr_gate.add_data(f"{secure_url}?mode=gate")
                qr_gate.print_ascii()
                
                # Show images
                try: 
                    os.startfile("home_prebook_qr.png")
                    time.sleep(1) # Small gap for OS to handle multiple opens
                    os.startfile("entry_gate_qr.png")
                except: pass
                break
        
        if not secure_url:
            print("\n❌ Error: Could not establish secure cloud link.")
            print("Fallback: Using Local IP QR...")
            local_ip = get_local_ip()
            generate_qr(f"http://{local_ip}:8501?mode=gate", "entry_gate_qr.png")
            generate_qr(f"http://{local_ip}:8501?mode=home", "home_prebook_qr.png")

        print(f"\n👉 PC Access: http://localhost:8501")
        print("\n🛑 Press Ctrl+C to shut down.")

        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping system...")
        backend.terminate()
        cameras.terminate()
        navigator.terminate()
        try: tunnel_proc.terminate()
        except: pass
        print("Goodbye!")

if __name__ == "__main__":
    main()
