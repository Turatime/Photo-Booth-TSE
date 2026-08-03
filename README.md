# Photo Booth Studio - Open House TSE 2026

Photo Booth Web Application for Open House TSE 2026. Built with FastAPI (Python), WebRTC, Pillow, and Google Drive API.

---

## Tools and Technologies Used

- Python 3.14 / 3.9+
- FastAPI (Web Server Framework)
- Uvicorn (ASGI Web Server)
- WebRTC API (Live Webcam / Sony A7 IV Stream)
- Pillow / PIL (Image Processing & High-Res Frame Compositing)
- PyDrive2 (Google Drive API Integration)
- QRCode (QR Code Generator)
- HTML5, CSS3, JavaScript ES6 (Frontend Studio Interface)

---

## Installation and How to Run

### macOS / Linux

```bash
# 1. Navigate to project directory
cd "/Users/timemy/Desktop/Photo Booth"

# 2. Create Virtual Environment
python3 -m venv .venv

# 3. Activate Virtual Environment
source .venv/bin/activate

# 4. Install Dependencies
pip install -r requirements.txt

# 5. Run the Server
python server.py
# (or execute ./run_app.sh)
```

---

### Windows (Command Prompt / PowerShell)

```cmd
:: 1. Navigate to project directory
cd "C:\path\to\Photo Booth"

:: 2. Create Virtual Environment
python -m venv .venv

:: 3. Activate Virtual Environment
:: PowerShell:
.venv\Scripts\Activate.ps1
:: Command Prompt (cmd.exe):
.venv\Scripts\activate.bat

:: 4. Install Dependencies
pip install -r requirements.txt

:: 5. Run the Server
python server.py
```

After starting the server, open your Web Browser and navigate to:  
`http://localhost:8000`

---

## How to Add New Frames (Adding Custom Frame Templates)

### Step 1: Place New PNG Frame File
Add your transparent PNG frame file (recommended size: 1200 x 1800 px) into the root project directory:  
`MyCustomFrame.png`

### Step 2: Register Frame in frame_processor.py
Edit `frame_processor.py` and add your frame key and filename to the `FRAME_TEMPLATES` dictionary:

```python
FRAME_TEMPLATES = {
    "Black Frame (BF)": "BF.png",
    "Wood Frame (FT)": "FT.png",
    "Red Frame (RF)": "RF.png",
    "Frame 33": "Frame33.png",
    "My New Frame": "MyCustomFrame.png"
}
```

### Step 3: Add Swatch Button in static/index.html
Edit `static/index.html` and add a new button inside `<div class="swatches-list">`:

```html
<button class="swatch-btn" data-frame="My New Frame">
  <span>My New Frame</span>
</button>
```

---

## Project Directory Overview

```text
Photo Booth/
├── server.py              # FastAPI server endpoints and static routing
├── frame_processor.py     # Image compositing, Pillow rendering, GDrive upload
├── run_app.sh             # Launch script (macOS/Linux)
├── requirements.txt       # Python dependency requirements
├── .gitignore             # Git ignore configuration
├── README.md              # Project documentation
├── BF.png                 # Black Classic frame template
├── FT.png                 # Warm Wood frame template
├── RF.png                 # Ruby Red frame template
├── Frame33.png            # Modern Frame 33 template
├── client_secrets.json    # Google OAuth client secrets (Not committed to Git)
├── static/                # Web frontend source files
│   ├── index.html         # Main Studio HTML
│   ├── styles.css         # Modern Glassmorphic CSS
│   └── app.js             # WebRTC, Countdown, and API logic
├── input_images/          # Captured raw photo shots
└── output_images/         # Rendered composite photo strips and QR codes
```
