"""
Start All JSON APIs
Launches all 9 JSON-based APIs (8 individual + 1 master) in separate processes
"""

import subprocess
import sys
import time
import os

# API files and their ports
APIS = [
    ("json_api_1_shopping_category.py", 6001, "Shopping Category"),
    ("json_api_2_shopping_subcategory.py", 6002, "Shopping Subcategory"),
    ("json_api_3_item_category.py", 6003, "Item Category"),
    ("json_api_4_item_subcategory.py", 6004, "Item Subcategory"),
    ("json_api_5_skw_generation.py", 6005, "SKW Generation"),
    ("json_api_6_dsw_generation.py", 6006, "DSW Generation"),
    ("json_api_7_ai_attributes.py", 6007, "AI Attributes"),
    ("json_api_8_arabic_translation.py", 6008, "Arabic Translation"),
    ("json_api_master_pipeline.py", 6000, "Master Pipeline"),
]


def start_api(api_file, port, name):
    """Start a single API in a new process"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        api_path = os.path.join(script_dir, api_file)

        print(f"Starting {name} API on port {port}...")

        # Start the API process
        process = subprocess.Popen(
            [sys.executable, api_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir
        )

        return process

    except Exception as e:
        print(f"Error starting {name} API: {str(e)}")
        return None


def main():
    """Start all APIs"""
    print("\n" + "="*60)
    print("Starting All JSON APIs")
    print("="*60 + "\n")

    processes = []

    # Start all APIs
    for api_file, port, name in APIS:
        process = start_api(api_file, port, name)
        if process:
            processes.append((process, name, port))
            time.sleep(2)  # Wait a bit between starting each API

    print("\n" + "="*60)
    print("All JSON APIs Started")
    print("="*60)
    print("\nAPIs running:")
    for _, name, port in processes:
        print(f"  • {name}: http://localhost:{port}")

    print("\n" + "="*60)
    print("\nMaster Pipeline API: http://localhost:6000")
    print("\nPress Ctrl+C to stop all APIs")
    print("="*60 + "\n")

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping all APIs...")
        for process, name, _ in processes:
            print(f"  Stopping {name}...")
            process.terminate()
        print("\nAll APIs stopped.\n")


if __name__ == "__main__":
    main()
