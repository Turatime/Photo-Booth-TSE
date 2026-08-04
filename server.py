#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open House TSE - BeautyPlus Photo Booth Web Server (FastAPI)
Serves the web application and handles clean session-based frame compositing & GDrive upload.
"""

import os
import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from PIL import Image

import frame_processor as fp

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INPUT_DIR = BASE_DIR / "input_images"
OUTPUT_DIR = BASE_DIR / "output_images"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BeautyPlus Photo Booth Studio")

# Serve static frame templates and output images
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/output_images", StaticFiles(directory=str(OUTPUT_DIR)), name="output_images")

@app.get("/", response_class=FileResponse)
async def serve_home():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h2>BeautyPlus Photo Booth Web App loading...</h2>")

@app.get("/api/frames")
async def get_frames():
    """Returns available frame templates and their URLs."""
    frames = []
    for name, filename in fp.FRAME_TEMPLATES.items():
        p = BASE_DIR / filename
        if p.exists():
            frames.append({
                "key": name,
                "name": name,
                "file": filename,
                "url": f"/frame_file/{filename}"
            })
    return JSONResponse(frames)

@app.get("/frame_file/{filename}")
async def serve_frame_file(filename: str):
    file_path = BASE_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Frame image not found")

@app.post("/api/composite")
async def process_composite(
    image1: str = Form(...),
    image2: str = Form(...),
    image3: str = Form(...),
    frame_key: str = Form("DeepDive Pink"),
    session_id: str = Form(None)
):
    """
    Receives 3 base64 images from browser webcam and session_id, renders composite 3-slot frame with Pillow,
    overwriting session files cleanly without cluttering storage.
    """
    try:
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        photos = [image1, image2, image3]
        saved_paths = []

        # Overwrite the 3 photo slot files for this specific session
        for idx, b64data in enumerate(photos):
            if "," in b64data:
                b64data = b64data.split(",")[1]
            img_bytes = base64.b64decode(b64data)
            img_path = INPUT_DIR / f"shot_{idx+1}_{session_id}.jpg"
            tmp_path = INPUT_DIR / f"shot_{idx+1}_{session_id}.jpg.tmp"
            with open(tmp_path, "wb") as f:
                f.write(img_bytes)
            tmp_path.replace(img_path)
            saved_paths.append(img_path)

        frame_file = fp.FRAME_TEMPLATES.get(frame_key, "DeepDive - 1.png")
        frame_path = BASE_DIR / frame_file

        if not frame_path.exists():
            frame_path = BASE_DIR / "DeepDive - 1.png"

        # Overwrite composite frame output file for this specific session
        out_path = fp.create_composite_frame(saved_paths, frame_path, OUTPUT_DIR, session_id=session_id)
        rel_url = f"/output_images/{out_path.name}"

        return JSONResponse({
            "status": "success",
            "filename": out_path.name,
            "url": rel_url,
            "session_id": session_id,
            "full_path": str(out_path)
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/upload-gdrive")
async def upload_gdrive(filename: str = Form(...)):
    """Uploads saved composite image to Google Drive & returns QR code URL."""
    try:
        local_path = OUTPUT_DIR / filename
        if not local_path.exists():
            raise HTTPException(status_code=404, detail="Output image not found")

        gdrive_url = fp.upload_to_gdrive(local_path, BASE_DIR)
        if gdrive_url == "MISSING_CLIENT_SECRETS":
            return JSONResponse({
                "status": "warning",
                "message": "⚠️ ไม่พบไฟล์ client_secrets.json กรุณาวางไฟล์จาก Google Cloud Console ในโฟลเดอร์โปรเจกต์",
                "url": ""
            })
        elif not gdrive_url or not gdrive_url.startswith("http"):
            return JSONResponse({
                "status": "warning",
                "message": "⚠️ การอัปโหลด Google Drive ไม่สำเร็จ หรือยังไม่ได้ล็อกอิน",
                "url": ""
            })

        qr_out = OUTPUT_DIR / f"{local_path.stem}_qr.png"
        fp.generate_qr_code(gdrive_url, qr_out)

        return JSONResponse({
            "status": "success",
            "gdrive_url": gdrive_url,
            "qr_url": f"/output_images/{qr_out.name}"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
