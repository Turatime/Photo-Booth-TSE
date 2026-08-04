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
├── client_secrets.json.example # Template for Google OAuth setup (Copy to client_secrets.json)
├── client_secrets.json        # Google OAuth client secrets (Ignored by Git for security)
├── static/                    # Web frontend source files
│   ├── index.html             # Main Studio HTML
│   ├── styles.css             # Modern Glassmorphic CSS
│   └── app.js                 # WebRTC, Countdown, and API logic
├── input_images/              # Captured raw photo shots
└── output_images/             # Rendered composite photo strips and QR codes

---
### ขั้นตอนการหา `client_id` และ `client_secret` (ทำตาม 5 สเต็ปนี้ได้เลยครับ)

สเต็ปที่ 1: เข้าสู่เว็บไซต์ Google Cloud Console
1. ไปที่เว็บไซต์  [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. ล็อกอินด้วยบัญชี **Google / Gmail** ของคุณ

สเต็ปที่ 2: สร้างโปรเจกต์ใหม่ (Create Project)
1. กดที่เมนูด้านบนซ้าย (ข้างๆ โลโก้ Google Cloud) ➔ เลือก **"New Project" (โปรเจกต์ใหม่)**
2. ตั้งชื่อโปรเจกต์ เช่น `Photo-Booth-Drive` แล้วกด **Create**

สเต็ปที่ 3: เปิดใช้งาน Google Drive API
1. ไปที่เมนูแถบซ้ายเลือก **APIs & Services** ➔ **Enabled APIs & Services**
2. กดปุ่ม **"+ ENABLE APIS AND SERVICES"** ด้านบน
3. ค้นหาคำว่า **Google Drive API** ➔ กดเลือกแล้วกดปุ่ม **ENABLE** (เปิดใช้งาน)

สเต็ปที่ 4: ตั้งค่า OAuth Consent Screen (หน้าจอยินยอม)
1. ไปที่เมนูแถบซ้าย **APIs & Services** ➔ **OAuth consent screen**
2. เลือก User Type เป็น **External** ➔ กด **CREATE**
3. กรอกข้อมูลเบื้องต้น:
   - **App name**: `Photo Booth`
   - **User support email**: เลือกอีเมล Gmail ของคุณ
   - **Developer contact information**: กรอกอีเมล Gmail ของคุณ
4. กด **SAVE AND CONTINUE** ไปเรื่อยๆ
5. *(สำคัญ)* ในหัวข้อ **Test users** ให้กด **"+ ADD USERS"** แล้วใส่อีเมล Gmail ของคุณลงไป เพื่อให้บัญชีของคุณมีสิทธิ์ล็อกอินทดสอบ

สเต็ปที่ 5: สร้างและดาวน์โหลด `client_id` และ `client_secret`
1. ไปที่เมนูแถบซ้าย **APIs & Services** ➔ **Credentials**
2. กดปุ่ม **"+ CREATE CREDENTIALS"** ด้านบน ➔ เลือก **OAuth client ID**
3. ในช่อง Application type ให้เลือกเป็น **Desktop App** (หรือ **Web application**)
4. ตั้งชื่อเป็น `Photo Booth Client` ➔ กด **CREATE**
5. หน้าต่างจะเด้งแสดง Client ID และ Client Secret ขึ้นมา!
   - คุณสามารถกดปุ่ม **"DOWNLOAD JSON"** ➔ แล้วเปลี่ยนชื่อไฟล์ที่โหลดมาเป็น **`client_secrets.json`**
   - นำไปวางในโฟลเดอร์โปรเจกต์ Photo Booth (`/Users/timemy/Desktop/Photo Booth/`) ได้ทันทีครับ!

---