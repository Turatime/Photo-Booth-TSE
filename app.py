#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open House TSE - BeautyPlus Style Photo Booth Client Application
Featuring Real-time Camera Live View, Live Photo Strip Composition Preview,
Instant Frame Theme Swatches, Google Drive Upload, and QR Code display.
"""

import os
import sys
import cv2
import time
import json
import threading
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from PIL import Image, ImageTk

# Import frame processor helper
import frame_processor as fp

# ---------- PATH SETUP ----------
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input_images"
OUTPUT_DIR = BASE_DIR / "output_images"

# Set CustomTkinter Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BeautyPlusPhotoBoothApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("✨ BeautyPlus Style Photo Booth Studio - Open House TSE 2026")
        self.geometry("1380x860")
        self.minsize(1100, 760)

        # Ensure directories exist
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Application State
        self.cap = None
        self.camera_index = 0
        self.is_camera_running = False
        self.is_flipped = True
        
        # Photo storage for current session (3 photos)
        self.session_photos: list[Path | None] = [None, None, None]
        self.selected_frame_key = "DeepDive Pink"
        
        # Countdown state
        self.is_counting_down = False
        self.countdown_val = 0
        self.active_slot_idx = None

        # Output states
        self.last_output_path = None
        self.last_qr_path = None
        self.last_gdrive_url = ""

        # Build BeautyPlus Layout
        self._build_ui()

        # Start Camera Feed
        self.start_camera()

        # Clean exit handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Configure Main Grid Layout (Top Header, Left Camera Box, Right BeautyPlus Result Box)
        self.grid_columnconfigure(0, weight=5) # Left Studio (Camera & Slots)
        self.grid_columnconfigure(1, weight=4) # Right BeautyPlus Result Strip Preview & Controls
        self.grid_rowconfigure(0, weight=0) # Top App Bar
        self.grid_rowconfigure(1, weight=1) # Main Studio Workspace

        # ==========================================
        # TOP APP BAR (BeautyPlus Studio Header)
        # ==========================================
        top_bar = ctk.CTkFrame(self, fg_color="#18181B", height=60, corner_radius=0)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="🌸 BeautyPlus Photo Booth Studio",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#EC4899"
        )
        title_lbl.pack(side="left", padx=20, pady=10)

        sub_lbl = ctk.CTkLabel(
            top_bar,
            text="Open House TSE 2026 | Life4Cuts Studio Edition",
            font=ctk.CTkFont(size=13),
            text_color="#A1A1AA"
        )
        sub_lbl.pack(side="left", padx=5, pady=12)

        # Camera Selector Dropdown
        self.cam_dropdown = ctk.CTkOptionMenu(
            top_bar,
            values=["Camera 0", "Camera 1", "Camera 2"],
            command=self.on_camera_change,
            width=130,
            fg_color="#27272A",
            button_color="#EC4899",
            button_hover_color="#DB2777"
        )
        self.cam_dropdown.set("Camera 0")
        self.cam_dropdown.pack(side="right", padx=20, pady=12)

        # ==========================================
        # LEFT PANEL: Camera Live View & Shot Cards
        # ==========================================
        self.left_panel = ctk.CTkFrame(self, corner_radius=16, fg_color="#18181B")
        self.left_panel.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1) # Camera View
        self.left_panel.grid_rowconfigure(1, weight=0) # Photo Shot Cards
        self.left_panel.grid_rowconfigure(2, weight=0) # Control Buttons
        self.left_panel.grid_columnconfigure(0, weight=1)

        # 1. Live Camera Display Label
        self.camera_label = ctk.CTkLabel(
            self.left_panel,
            text="⚡ กำลังเชื่อมต่อกล้อง...",
            fg_color="#09090B",
            corner_radius=12,
            font=ctk.CTkFont(size=16)
        )
        self.camera_label.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        # 2. Shot Cards (3 Photo Slot Thumbnails)
        shot_cards_box = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        shot_cards_box.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")
        shot_cards_box.grid_columnconfigure((0, 1, 2), weight=1)

        self.slot_cards = []
        for idx in range(3):
            card = ctk.CTkFrame(shot_cards_box, corner_radius=10, fg_color="#27272A")
            card.grid(row=0, column=idx, padx=5, pady=5, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            lbl_thumb = ctk.CTkLabel(
                card,
                text=f"ช็อตที่ {idx+1}\n(ยังไม่ถ่าย)",
                font=ctk.CTkFont(size=12),
                fg_color="#09090B",
                corner_radius=8,
                height=80
            )
            lbl_thumb.pack(padx=8, pady=(8, 4), fill="both")

            btn_retake = ctk.CTkButton(
                card,
                text=f"ถ่ายช็อต {idx+1}",
                font=ctk.CTkFont(size=11),
                height=28,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                command=lambda i=idx: self.select_and_shoot_slot(i)
            )
            btn_retake.pack(padx=8, pady=(0, 8), fill="x")

            self.slot_cards.append({
                "label": lbl_thumb,
                "button": btn_retake
            })

        # 3. Action Buttons Bar
        btn_bar = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        btn_bar.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        btn_bar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.btn_auto_shoot = ctk.CTkButton(
            btn_bar,
            text="🚀 เริ่มถ่าย 3 ช็อต",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#EC4899",
            hover_color="#DB2777",
            height=46,
            corner_radius=10,
            command=self.start_auto_shoot_sequence
        )
        self.btn_auto_shoot.grid(row=0, column=0, padx=3, pady=4, sticky="ew")

        self.btn_flip = ctk.CTkButton(
            btn_bar,
            text="🪞 กลับด้านภาพ (Flipped)",
            font=ctk.CTkFont(size=12),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=46,
            corner_radius=10,
            command=self.toggle_flip
        )
        self.btn_flip.grid(row=0, column=1, padx=3, pady=4, sticky="ew")

        self.btn_snap_single = ctk.CTkButton(
            btn_bar,
            text="📸 ถ่ายช่องว่าง",
            font=ctk.CTkFont(size=12),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            height=46,
            corner_radius=10,
            command=self.snap_current_slot
        )
        self.btn_snap_single.grid(row=0, column=2, padx=3, pady=4, sticky="ew")

        self.btn_reset = ctk.CTkButton(
            btn_bar,
            text="🔄 ถ่ายใหม่",
            font=ctk.CTkFont(size=12),
            fg_color="#EF4444",
            hover_color="#DC2626",
            height=46,
            corner_radius=10,
            command=self.reset_session
        )
        self.btn_reset.grid(row=0, column=3, padx=3, pady=4, sticky="ew")

        # ==========================================
        # RIGHT PANEL: BeautyPlus Photo Strip Result Studio
        # ==========================================
        self.right_panel = ctk.CTkFrame(self, corner_radius=16, fg_color="#18181B")
        self.right_panel.grid(row=1, column=1, padx=(0, 15), pady=15, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=1) # Result Preview Card
        self.right_panel.grid_rowconfigure(1, weight=0) # Frame Theme Picker
        self.right_panel.grid_rowconfigure(2, weight=0) # Bottom Download/QR Actions
        self.right_panel.grid_columnconfigure(0, weight=1)

        # 1. Real-Time Photo Strip Result Preview Box
        result_box = ctk.CTkFrame(self.right_panel, corner_radius=12, fg_color="#09090B")
        result_box.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        result_box.pack_propagate(False)

        self.result_preview_label = ctk.CTkLabel(
            result_box,
            text="✨ ตัวอย่าง Photo Strip แบบสด\n(จะอัปเดตอัตโนมัติเมื่อถ่ายรูป)",
            font=ctk.CTkFont(size=15),
            text_color="#71717A"
        )
        self.result_preview_label.pack(expand=True, fill="both", padx=10, pady=10)

        # 2. BeautyPlus Style Frame Swatches & Theme Selector
        theme_box = ctk.CTkFrame(self.right_panel, corner_radius=12, fg_color="#27272A")
        theme_box.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        theme_header = ctk.CTkLabel(
            theme_box,
            text="🎨 เลือกสีและสไตล์กรอบรูป (BeautyPlus Themes):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F4F4F5"
        )
        theme_header.pack(anchor="w", padx=12, pady=(10, 6))

        swatch_frame = ctk.CTkFrame(theme_box, fg_color="transparent")
        swatch_frame.pack(fill="x", padx=8, pady=(0, 10))
        swatch_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Swatch buttons
        swatches = [
            ("DeepDive Pink", "DeepDive Pink", "#EC4899"),
            ("DeepDive Blue", "DeepDive Blue", "#3B82F6"),
            ("เปิดโลกกิจกรรม", "เปิดโลกกิจกรรม", "#475569"),
            ("#TSE37 ไม่เด็ดได้ไง", "#TSE37 ไม่เด็ดได้ไง", "#B91C1C"),
            ("วิศวะไม่ได้ร้าย", "วิศวะไม่ได้ร้าย", "#D97706")
        ]

        for idx, (name, key, color) in enumerate(swatches):
            btn = ctk.CTkButton(
                swatch_frame,
                text=name,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=color,
                height=36,
                corner_radius=8,
                command=lambda k=key: self.select_frame_theme(k)
            )
            btn.grid(row=0, column=idx, padx=2, pady=2, sticky="ew")

        # 3. Bottom Download & Share Action Bar
        action_box = ctk.CTkFrame(self.right_panel, corner_radius=12, fg_color="transparent")
        action_box.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        action_box.grid_columnconfigure((0, 1), weight=1)

        self.btn_download = ctk.CTkButton(
            action_box,
            text="💾 บันทึกรูปภาพ Photo Strip (HD)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=48,
            corner_radius=10,
            command=self.save_hd_composite
        )
        self.btn_download.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.btn_upload_qr = ctk.CTkButton(
            action_box,
            text="📱 สแกน QR Code รับรูปใส่มือถือ",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#06B6D4",
            hover_color="#0891B2",
            height=48,
            corner_radius=10,
            command=self.upload_gdrive_and_qr
        )
        self.btn_upload_qr.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

    # ==========================================
    # CAMERA STREAM & OVERLAYS
    # ==========================================
    def start_camera(self):
        """Starts OpenCV VideoCapture feed."""
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.camera_label.configure(text=f"⚠️ ไม่สามารถเชื่อมต่อกล้อง {self.camera_index} ได้")
            self.is_camera_running = False
            return

        self.is_camera_running = True
        self.update_video_feed()

    def toggle_flip(self):
        self.is_flipped = not self.is_flipped
        if self.is_flipped:
            self.btn_flip.configure(text="🪞 กลับด้านภาพ (Flipped)")
        else:
            self.btn_flip.configure(text="🪞 ภาพปกติ (Normal)")

    def update_video_feed(self):
        """Live feed thread update ~30 FPS."""
        if not self.is_camera_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            if self.is_flipped:
                frame = cv2.flip(frame, 1) # Mirror feel
            self.current_raw_frame = frame.copy()

            display_frame = self._draw_camera_overlays(frame.copy())

            cv2_img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv2_img)

            lbl_w = max(self.camera_label.winfo_width(), 400)
            lbl_h = max(self.camera_label.winfo_height(), 300)

            pil_img.thumbnail((lbl_w, lbl_h), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)

            self.camera_label.configure(image=ctk_img, text="")

        self.after(33, self.update_video_feed)

    def _draw_camera_overlays(self, frame):
        """Draws face alignment guides and countdown overlay."""
        # Calculate frame slot aspect ratio crop area (435 x 420)
        target_aspect = 435 / 420
        current_aspect = w / h

        if current_aspect > target_aspect:
            guide_h = int(h * 0.88)
            guide_w = int(guide_h * target_aspect)
        else:
            guide_w = int(w * 0.88)
            guide_h = int(guide_w / target_aspect)

        x1 = (w - guide_w) // 2
        y1 = (h - guide_h) // 2
        x2 = x1 + guide_w
        y2 = y1 + guide_h

        # Dim area outside frame crop box
        mask = frame.copy()
        cv2.rectangle(mask, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.rectangle(mask, (x1, y1), (x2, y2), (255, 255, 255), -1)
        # Apply 45% dimming outside crop area
        dimmed = cv2.addWeighted(frame, 0.55, cv2.bitwise_and(frame, mask), 0.45, 0)
        frame = dimmed

        # Draw crisp pink guide box around photo slot area
        cv2.rectangle(frame, (x1, y1), (x2, y2), (236, 72, 153), 3)
        cv2.putText(
            frame,
            "Photo Slot Area",
            (x1 + 12, y1 + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (236, 72, 153),
            2
        )

        # Big Countdown Overlay
        if self.is_counting_down:
            txt = str(self.countdown_val) if self.countdown_val > 0 else "SMILE! 📸"
            font_scale = 4.5 if self.countdown_val > 0 else 2.5
            color = (0, 255, 255) if self.countdown_val > 0 else (100, 255, 100)

            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 8)
            tx = (w - tw) // 2
            ty = (h + th) // 2

            overlay = frame.copy()
            cv2.rectangle(overlay, (tx - 20, ty - th - 20), (tx + tw + 20, ty + 20), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
            cv2.putText(frame, txt, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 8)

        return frame

    def on_camera_change(self, choice: str):
        idx = int(choice.split()[-1])
        self.camera_index = idx
        self.start_camera()

    def select_frame_theme(self, key: str):
        """Switches frame theme and updates BeautyPlus strip preview instantly."""
        self.selected_frame_key = key
        self.refresh_result_preview()

    # ==========================================
    # PHOTO CAPTURE & THUMBNAIL UPDATES
    # ==========================================
    def snap_photo_to_slot(self, slot_idx: int):
        if hasattr(self, 'current_raw_frame') and self.current_raw_frame is not None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            photo_path = INPUT_DIR / f"shot_slot{slot_idx+1}_{ts}.jpg"
            cv2.imwrite(str(photo_path), self.current_raw_frame)
            self.session_photos[slot_idx] = photo_path

            self._update_slot_thumbnail(slot_idx, photo_path)
            self.refresh_result_preview()

    def _update_slot_thumbnail(self, slot_idx: int, photo_path: Path):
        pil_img = Image.open(photo_path)
        pil_img.thumbnail((120, 80), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)

        card_info = self.slot_cards[slot_idx]
        card_info["label"].configure(image=ctk_img, text="")
        card_info["button"].configure(text=f"🔄 ถ่ายใหม่")

    def snap_current_slot(self):
        target_slot = 0
        for idx, photo in enumerate(self.session_photos):
            if photo is None:
                target_slot = idx
                break
        self.select_and_shoot_slot(target_slot)

    def select_and_shoot_slot(self, slot_idx: int):
        if self.is_counting_down:
            return
        self.active_slot_idx = slot_idx
        threading.Thread(target=self._run_single_countdown, args=(slot_idx,), daemon=True).start()

    def _run_single_countdown(self, slot_idx: int):
        self.is_counting_down = True
        for c in range(3, 0, -1):
            self.countdown_val = c
            time.sleep(1)
        self.countdown_val = 0
        time.sleep(0.5)

        self.after(0, lambda: self.snap_photo_to_slot(slot_idx))
        self.is_counting_down = False

    def start_auto_shoot_sequence(self):
        if self.is_counting_down:
            return
        threading.Thread(target=self._run_auto_sequence, daemon=True).start()

    def _run_auto_sequence(self):
        for slot_idx in range(3):
            self.active_slot_idx = slot_idx
            self.is_counting_down = True
            for c in range(3, 0, -1):
                self.countdown_val = c
                time.sleep(1)
            self.countdown_val = 0
            time.sleep(0.5)

            self.after(0, lambda s=slot_idx: self.snap_photo_to_slot(s))
            time.sleep(1.2)

        self.is_counting_down = False

    def reset_session(self):
        self.session_photos = [None, None, None]
        for idx, card_info in enumerate(self.slot_cards):
            card_info["label"].configure(image=None, text=f"ช็อตที่ {idx+1}\n(ยังไม่ถ่าย)")
            card_info["button"].configure(text=f"ถ่ายช็อต {idx+1}")
        self.result_preview_label.configure(
            image=None, 
            text="✨ ตัวอย่าง Photo Strip แบบสด\n(จะอัปเดตอัตโนมัติเมื่อถ่ายรูป)"
        )
        self.last_output_path = None
        self.last_qr_path = None

    # ==========================================
    # BEAUTYPLUS RESULT STRIP PREVIEW & ACTIONS
    # ==========================================
    def refresh_result_preview(self):
        """Generates composite frame and renders live preview on the right panel."""
        valid_photos = [p for p in self.session_photos if p is not None and p.exists()]
        if not valid_photos:
            return

        frame_file = fp.FRAME_TEMPLATES.get(self.selected_frame_key, "DeepDive - 1.png")
        frame_path = BASE_DIR / frame_file
        if not frame_path.exists():
            return

        out_path = fp.create_composite_frame(valid_photos, frame_path, OUTPUT_DIR)
        self.last_output_path = out_path

        # Update Result Strip Live Preview Label
        pil_img = Image.open(out_path)
        lbl_w = max(self.result_preview_label.winfo_width(), 320)
        lbl_h = max(self.result_preview_label.winfo_height(), 480)
        
        pil_img.thumbnail((lbl_w, lbl_h), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)

        self.result_preview_label.configure(image=ctk_img, text="")

    def save_hd_composite(self):
        if self.last_output_path and self.last_output_path.exists():
            self._show_composite_modal(self.last_output_path)
        else:
            self.refresh_result_preview()
            if self.last_output_path:
                self._show_composite_modal(self.last_output_path)

    def _show_composite_modal(self, image_path: Path):
        modal = ctk.CTkToplevel(self)
        modal.title("✨ บันทึกรูปภาพ Photo Strip (HD Preview)")
        modal.geometry("540x780")
        modal.grab_set()

        pil_img = Image.open(image_path)
        pil_img.thumbnail((500, 720), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)

        lbl_img = ctk.CTkLabel(modal, image=ctk_img, text="")
        lbl_img.pack(padx=20, pady=20)

    def upload_gdrive_and_qr(self):
        if self.last_output_path is None or not self.last_output_path.exists():
            self.refresh_result_preview()
            if self.last_output_path is None:
                return

        def task():
            url = fp.upload_to_gdrive(self.last_output_path, BASE_DIR)
            if url == "MISSING_CLIENT_SECRETS":
                self.after(0, lambda: self._show_error_modal(
                    "⚠️ ไม่พบไฟล์ client_secrets.json",
                    "กรุณานำไฟล์ client_secrets.json จาก Google Cloud Console\nวางไว้ในโฟลเดอร์โปรเจกต์ เพื่อใช้งานระบบล็อกอิน Gmail / Google Drive"
                ))
            elif url and url.startswith("http"):
                qr_out = OUTPUT_DIR / f"{self.last_output_path.stem}_qr.png"
                fp.generate_qr_code(url, qr_out)
                self.last_gdrive_url = url
                self.last_qr_path = qr_out

                self.after(0, lambda: self._show_qr_modal(url, qr_out))
            else:
                self.after(0, lambda: self._show_error_modal(
                    "⚠️ ไม่สามารถอัปโหลดไปยัง Google Drive ได้",
                    "เกิดข้อผิดพลาดในการรับรองสิทธิ์หรือการเชื่อมต่ออินเทอร์เน็ต"
                ))

        threading.Thread(target=task, daemon=True).start()

    def _show_error_modal(self, title: str, message: str):
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.geometry("480x240")
        modal.grab_set()

        lbl_title = ctk.CTkLabel(modal, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color="#EF4444")
        lbl_title.pack(padx=20, pady=(20, 10))

        lbl_msg = ctk.CTkLabel(modal, text=message, font=ctk.CTkFont(size=13), justify="center")
        lbl_msg.pack(padx=20, pady=10)

        btn_ok = ctk.CTkButton(modal, text="ตกลง", command=modal.destroy, fg_color="#3B82F6", width=120)
        btn_ok.pack(padx=20, pady=(10, 20))

    def _show_qr_modal(self, url: str, qr_path: Path):
        modal = ctk.CTkToplevel(self)
        modal.title("📱 สแกน QR Code เพื่อรับรูปถ่าย")
        modal.geometry("450x550")
        modal.grab_set()

        title_lbl = ctk.CTkLabel(
            modal,
            text="📱 สแกน QR Code ด้วยมือถือเพื่อดาวน์โหลดรูปภาพ",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_lbl.pack(padx=20, pady=(20, 10))

        pil_qr = Image.open(qr_path)
        pil_qr = pil_qr.resize((300, 300), Image.Resampling.LANCZOS)
        ctk_qr = ctk.CTkImage(light_image=pil_qr, dark_image=pil_qr, size=(300, 300))

        lbl_qr = ctk.CTkLabel(modal, image=ctk_qr, text="")
        lbl_qr.pack(padx=20, pady=10)

        url_entry = ctk.CTkEntry(modal, width=380)
        url_entry.insert(0, url)
        url_entry.pack(padx=20, pady=10)

    def on_close(self):
        self.is_camera_running = False
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = BeautyPlusPhotoBoothApp()
    app.mainloop()
