#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frame Processor Module for Open House TSE Photo Booth
Handles image compositing into frames, QR code generation, and Google Drive upload.
"""

import json
from pathlib import Path
from datetime import datetime
from PIL import Image
import qrcode

# ---------- DEFAULT CONSTANTS ----------
SLOTS_PX = [
    (325, 300, 435, 415),  # Slot 1 (Top)
    (325, 745, 435, 420),  # Slot 2 (Middle)
    (325, 1200, 435, 420)  # Slot 3 (Bottom)
]

FRAME_TEMPLATES = {
    "DeepDive Pink": "DeepDive - 1.png",
    "DeepDive Blue": "DeepDive - 2.png",
    "เปิดโลกกิจกรรม": "DeepDive - 3.png",
    "#TSE37 ไม่เด็ดได้ไง": "DeepDive - 4.png",
    "วิศวะไม่ได้ร้าย": "DeepDive - 5.png"
}

def fit_inside(im: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Resize image to fit inside max_w, max_h while keeping aspect ratio and cropping center."""
    w, h = im.size
    target_aspect = max_w / max_h
    current_aspect = w / h

    if current_aspect > target_aspect:
        # Image is wider than slot: crop width
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        # Image is taller than slot: crop height
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        im = im.crop((0, top, w, top + new_h))

    return im.resize((max_w, max_h), Image.Resampling.LANCZOS)

def create_composite_frame(
    photo_paths: list[Path],
    frame_path: Path,
    output_dir: Path,
    session_id: str = None
) -> Path:
    """
    Pastes photos into slots on the given frame overlay.
    photo_paths: list of 3 (or 6) image file paths.
    If session_id is given, overwrites session file to prevent clutter.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    frame = Image.open(frame_path).convert("RGBA")
    W, H = frame.size
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 0))

    if not photo_paths:
        raise ValueError("No photos provided for frame composition")

    for i, (slot_x, slot_y, slot_w, slot_h) in enumerate(SLOTS_PX):
        img_index = i % len(photo_paths)
        src = photo_paths[img_index]
        
        if not Path(src).exists():
            continue

        im = Image.open(src).convert("RGBA")
        im = fit_inside(im, slot_w, slot_h)

        paste_x = slot_x + (slot_w - im.width) // 2
        paste_y = slot_y + (slot_h - im.height) // 2
        canvas.paste(im, (paste_x, paste_y), im)

    # Overlay frame template on top of images
    canvas = Image.alpha_composite(canvas, frame)

    # Atomic file save using temp file to prevent Uvicorn/StaticFiles race conditions
    if session_id:
        out_path = output_dir / f"PhotoStrip_{session_id}.png"
        tmp_path = output_dir / f"PhotoStrip_{session_id}_tmp.png"
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"PhotoStrip_{ts}.png"
        tmp_path = output_dir / f"PhotoStrip_{ts}_tmp.png"

    canvas.save(tmp_path, format="PNG")
    tmp_path.replace(out_path)
    return out_path

def upload_to_gdrive(
    local_path: Path,
    base_dir: Path,
    client_secrets_filename: str = "client_secrets.json",
    credentials_filename: str = "credentials.json"
) -> str:
    """Uploads saved image to Google Drive and returns shareable view URL."""
    try:
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive
    except ImportError:
        print("⚠️ pydrive2 is not installed.")
        return ""

    client_secrets_path = base_dir / client_secrets_filename
    credentials_path = base_dir / credentials_filename

    if not client_secrets_path.exists():
        alt = sorted(base_dir.glob("client_secret_*.json"))
        if alt:
            client_secrets_path = alt[-1]
        else:
            print(f"⚠️ client_secrets.json not found in {base_dir}")
            return "MISSING_CLIENT_SECRETS"

    gauth = GoogleAuth()
    gauth.DEFAULT_SETTINGS['client_config_file'] = str(client_secrets_path)
    gauth.DEFAULT_SETTINGS['oauth_scope'] = ['https://www.googleapis.com/auth/drive.file']
    gauth.DEFAULT_SETTINGS['get_refresh_token'] = True

    if credentials_path.exists():
        gauth.LoadCredentialsFile(str(credentials_path))

    try:
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
    except Exception as e:
        print(f"Auth error: {e}, falling back to command line auth")
        gauth.CommandLineAuth()

    gauth.SaveCredentialsFile(str(credentials_path))
    drive = GoogleDrive(gauth)

    file_drive = drive.CreateFile({'title': local_path.name})
    file_drive.SetContentFile(str(local_path))
    file_drive.Upload()
    file_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})

    file_id = file_drive['id']
    view_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    return view_url

def generate_qr_code(url: str, output_path: Path) -> Path:
    """Generates QR code PNG image from URL atomically."""
    tmp_path = output_path.parent / f"{output_path.stem}_tmp.png"
    qr_img = qrcode.make(url)
    qr_img.save(tmp_path, format="PNG")
    tmp_path.replace(output_path)
    return output_path
