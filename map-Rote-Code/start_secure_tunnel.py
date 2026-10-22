import subprocess
import re
import time
import qrcode
import os
import socket
import sys

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def generate_qr(url, mode="SECURE"):
    print(f"\n{'🔒' if mode=='SECURE' else '📡'} Generating {mode} QR Code for: {url}")
    qr = qrcode.QRCode(version=1, box_size=15, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("parking_gate_qr.png")
    print(f"✅ QR Code updated: 'parking_gate_qr.png' ({mode} Mode)")

def main():
    print("\n" + "="*50)
    print("🚀 SMART PARKING MASTER TUNNEL & QR")
    print("="*50)
    
    # --- STEP 1: VERIFY NAVIGATOR IS RUNNING ---
    print("\n🔍 Checking for Smart Navigator...")
    port = 8502
    if not is_port_open(port):
        print(f"⚠️  Warning: Navigator not found on port {port}.")
        print("Checking port 8501 (Default Streamlit)...")
        if is_port_open(8501):
            port = 8501
            print(f"✅ Found Navigator on port {8501}!")
        else:
            print("\n❌ ERROR: Your 'navigator.py' is NOT running!")
            print("Please open a NEW terminal and run:")
            print("  cd dashboard")
            print("  streamlit run navigator.py --server.port 8502")
            print("\nWait until the navigator opens in your browser, then run this script again.")
            input("\nPress Enter to exit...")
            return

    # --- STEP 2: MODE SELECTION ---
    print(f"\n✅ Navigator is ONLINE on port {port}")
    print("\nChoose Mode:")
    print("1. [S] Secure Tunnel (HTTPS - Best for phones)")
    print("2. [L] Local Network (Wi-Fi only - No internet needed)")
    
    choice = input("\nSelect Mode (S/L) [Default S]: ").strip().lower()

    if choice == 'l':
        # Get Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except: local_ip = "127.0.0.1"
        
        local_url = f"http://{local_ip}:{port}"
        generate_qr(local_url, "LOCAL")
        print(f"\n🔗 URL: {local_url}")
        print("⚠️  Note: Phone must be on the SAME Wi-Fi as this PC.")
        print("Press Ctrl+C to exit.")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: pass
        return

    # --- STEP 3: START SECURE TUNNEL ---
    print(f"\n1. Connecting to tunnel service for port {port}...")
    # Map external port 80 to our local streamlit port
    cmd = ["ssh", "-R", f"80:localhost:{port}", "nokey@localhost.run"]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        start_time = time.time()
        
        while True:
            line = process.stdout.readline()
            if not line: break
            print(f"   > {line.strip()}")
            
            # Search for the HTTPS link in the output
            match = re.search(r'https://[a-zA-Z0-9.-]+\.lhr\.life', line)
            if match:
                secure_url = match.group(0)
                generate_qr(secure_url, "SECURE")
                print("\n✅ TUNNEL ACTIVE!")
                print("📱 SCAN THE QR CODE NOW.")
                print("\n🔔 KEEP THIS WINDOW OPEN.")
                break
            
            if "Permission denied" in line or "Connection refused" in line:
                print("\n❌ SSH Connection failed. Check your internet or Firewall.")
                process.terminate()
                return

            if time.time() - start_time > 25:
                print("\n❌ Tunnel Timeout. The service 'localhost.run' might be busy.")
                print("Try running again in a minute, or use [L] Local Mode.")
                process.terminate()
                return

        process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        process.terminate()

if __name__ == "__main__":
    main()
