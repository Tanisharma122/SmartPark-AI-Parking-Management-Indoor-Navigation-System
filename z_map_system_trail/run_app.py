import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    print("Launching HikCentral-style Parking Dashboard...")
    main()
