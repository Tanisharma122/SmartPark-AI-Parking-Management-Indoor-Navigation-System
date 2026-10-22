import qrcode
import socket
import os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        try:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
    except:
        return "127.0.0.1"

def generate_gate_qr():
    print("\n" + "🚀 PROFESSIONAL SECURE QR GENERATOR" + "\n" + "="*45)
    
    print("To get a SECURE HTTPS link (No phone warnings) without Node.js:")
    print("-" * 45)
    print("1. Open a NEW separate terminal.")
    print("2. Paste this exact command and press Enter:")
    print("\n   ssh -R 80:localhost:8502 nokey@localhost.run\n")
    print("3. Look for the line that starts with 'https://...'")
    print("4. Copy that link and paste it below.")
    print("-" * 45)
    
    user_url = input("\nPaste your Secure URL (or press ENTER for local IP): ").strip()
    
    if not user_url:
        local_ip = get_local_ip()
        nav_url = f"http://{local_ip}:8502"
        print(f"\n⚠️  Using Local IP: {nav_url} (Phone will show 'Not Secure' warning)")
    else:
        nav_url = user_url
        if not nav_url.startswith("http"):
            nav_url = "https://" + nav_url
        print(f"\n🔒 SUCCESS! Using Secure URL: {nav_url}")

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=5,
    )
    qr.add_data(nav_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    output_path = "parking_gate_qr.png"
    img.save(output_path)
    
    print("\n" + "="*45)
    print(f"✅ QR Code saved as '{output_path}'")
    print(f"👉 Now scan this to see your navigator SECURELY on any phone!")
    print("="*45 + "\n")

if __name__ == "__main__":
    generate_gate_qr()
