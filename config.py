# config.py
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
