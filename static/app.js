/**
 * Photo Booth Studio - Clean Camera & Step Wizard Logic
 */

class BeautyPlusApp {
  constructor() {
    this.stream = null;
    this.videoElem = document.getElementById('webcamVideo');
    this.canvasElem = document.getElementById('captureCanvas');
    this.cameraSelect = document.getElementById('cameraSelect');
    this.camStatusBox = document.getElementById('camStatusBox');
    this.camStatusText = document.getElementById('camStatusText');

    // Photo session state (3 photos)
    this.sessionId = 'session_' + Date.now();
    this.sessionPhotos = [null, null, null];
    this.selectedFrameKey = "Black Frame (BF)";
    this.isCountingDown = false;
    this.isFlipped = true;
    this.lastCompositeResult = null;
    this.currentStep = 1;

    this.init();
  }

  async init() {
    this.bindEvents();
    await this.setupCameras();
    await this.startCamera();
  }

  bindEvents() {
    // Camera Select
    if (this.cameraSelect) {
      this.cameraSelect.addEventListener('change', () => this.startCamera());
    }

    // Control Buttons (Step 1)
    const btnAuto = document.getElementById('btnAutoShoot');
    if (btnAuto) btnAuto.addEventListener('click', () => this.startAutoShootSequence());

    const btnFlip = document.getElementById('btnToggleFlip');
    if (btnFlip) btnFlip.addEventListener('click', () => this.toggleFlip());

    const btnReset = document.getElementById('btnReset');
    if (btnReset) btnReset.addEventListener('click', () => this.resetSession());

    // Step Navigation Buttons
    const btnNext = document.getElementById('btnGoToStep2');
    if (btnNext) btnNext.addEventListener('click', () => this.goToStep2());

    const btnBack = document.getElementById('btnBackToStep1');
    if (btnBack) btnBack.addEventListener('click', () => this.goToStep1());

    // Swatch Frame Selector Buttons (Step 2)
    document.querySelectorAll('.swatch-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.swatch-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.selectedFrameKey = btn.dataset.frame;
        this.renderCompositeStrip();
      });
    });

    // Action Button (Step 2) - Upload to Google Drive and Show QR
    const btnUpload = document.getElementById('btnUploadQR');
    if (btnUpload) btnUpload.addEventListener('click', () => this.uploadGDriveAndShowQR());

    // Modal Close
    const btnCloseModal = document.getElementById('btnCloseModal');
    if (btnCloseModal) {
      btnCloseModal.addEventListener('click', () => {
        document.getElementById('qrModal').style.display = 'none';
      });
    }
  }

  // ==========================================
  // STEP SWITCHING & NAVIGATION
  // ==========================================
  goToStep1() {
    this.currentStep = 1;
    document.getElementById('screenStep1').style.display = 'block';
    document.getElementById('screenStep2').style.display = 'none';

    const step1Ind = document.getElementById('stepIndicator1');
    const step2Ind = document.getElementById('stepIndicator2');
    if (step1Ind) step1Ind.classList.add('active');
    if (step2Ind) step2Ind.classList.remove('active');
  }

  goToStep2() {
    const filledPhotos = this.sessionPhotos.filter(p => p !== null);
    if (filledPhotos.length === 0) {
      alert('กรุณาถ่ายรูปอย่างน้อย 1 ช็อตก่อนไปขั้นตอนเลือกกรอบรูป');
      return;
    }

    this.currentStep = 2;
    document.getElementById('screenStep1').style.display = 'none';
    document.getElementById('screenStep2').style.display = 'block';

    const step1Ind = document.getElementById('stepIndicator1');
    const step2Ind = document.getElementById('stepIndicator2');
    if (step1Ind) step1Ind.classList.remove('active');
    if (step2Ind) step2Ind.classList.add('active');

    // Automatically render composite frame preview on Step 2 enter
    this.renderCompositeStrip();
  }

  // ==========================================
  // WEBCAM MEDIA DEVICE HANDLING
  // ==========================================
  async setupCameras() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(d => d.kind === 'videoinput');

      if (this.cameraSelect) this.cameraSelect.innerHTML = '';

      if (videoDevices.length === 0) {
        if (this.camStatusBox) this.camStatusBox.className = 'cam-status-box disconnected';
        if (this.camStatusText) this.camStatusText.textContent = 'Disconnected: ไม่พบกล้องในระบบ';
        if (this.cameraSelect) this.cameraSelect.style.display = 'none';
        return;
      }

      if (this.camStatusBox) this.camStatusBox.className = 'cam-status-box connected';
      if (this.cameraSelect) this.cameraSelect.style.display = 'inline-block';

      videoDevices.forEach((dev, idx) => {
        const opt = document.createElement('option');
        opt.value = dev.deviceId;
        opt.textContent = dev.label || `Camera ${idx + 1}`;
        if (this.cameraSelect) this.cameraSelect.appendChild(opt);
      });

      const activeLabel = videoDevices[0].label || 'Sony A7 IV / Camera';
      if (this.camStatusText) {
        this.camStatusText.textContent = `Connected: ${activeLabel}`;
      }
    } catch (err) {
      console.error('Error listing cameras:', err);
      if (this.camStatusBox) this.camStatusBox.className = 'cam-status-box disconnected';
      if (this.camStatusText) this.camStatusText.textContent = 'Disconnected: ไม่สามารถอ่านกล้องได้';
      if (this.cameraSelect) this.cameraSelect.style.display = 'none';
    }
  }

  async startCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }

    const deviceId = this.cameraSelect ? this.cameraSelect.value : '';
    const constraints = {
      video: deviceId ? { deviceId: { exact: deviceId }, width: { ideal: 1280 }, height: { ideal: 960 } } : true
    };

    try {
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.videoElem.srcObject = this.stream;
      if (this.videoElem) {
        const val = this.isFlipped ? 'scaleX(-1)' : 'scaleX(1)';
        this.videoElem.style.setProperty('transform', val, 'important');
        this.videoElem.style.setProperty('-webkit-transform', val, 'important');
      }

      if (this.camStatusBox) this.camStatusBox.className = 'cam-status-box connected';
      if (this.cameraSelect) this.cameraSelect.style.display = 'inline-block';
    } catch (err) {
      console.error('Camera access error:', err);
      if (this.camStatusBox) this.camStatusBox.className = 'cam-status-box disconnected';
      if (this.camStatusText) this.camStatusText.textContent = 'Disconnected: ไม่สามารถเปิดใช้งานกล้องได้';
      if (this.cameraSelect) this.cameraSelect.style.display = 'none';
    }
  }

  // ==========================================
  // CAPTURE & COUNTDOWN SEQUENCES
  // ==========================================
  enterFullscreenMode() {
    const vp = document.getElementById('viewport');
    if (vp) vp.classList.add('fullscreen-active');
    document.body.classList.add('shooting-fullscreen');

    const header = document.querySelector('.app-header');
    if (header) header.style.display = 'none';
    
    try {
      if (document.documentElement.requestFullscreen && !document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
    } catch (e) {}
  }

  exitFullscreenMode() {
    const vp = document.getElementById('viewport');
    if (vp) vp.classList.remove('fullscreen-active');
    document.body.classList.remove('shooting-fullscreen');

    const header = document.querySelector('.app-header');
    if (header) header.style.display = 'block';

    try {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    } catch (e) {}
  }

  async startAutoShootSequence() {
    if (this.isCountingDown) return;
    this.isCountingDown = true;

    this.goToStep1();
    this.enterFullscreenMode();

    for (let slot = 0; slot < 3; slot++) {
      await this.runCountdown();
      this.captureShotToSlot(slot);
      await new Promise(r => setTimeout(r, 1000));
    }

    this.exitFullscreenMode();
    this.isCountingDown = false;
  }

  async shootSingleSlot(slotIdx) {
    if (this.isCountingDown) return;
    this.isCountingDown = true;

    this.goToStep1();
    this.enterFullscreenMode();

    await this.runCountdown();
    this.captureShotToSlot(slotIdx);

    this.exitFullscreenMode();
    this.isCountingDown = false;
  }

  runCountdown() {
    return new Promise(resolve => {
      const overlay = document.getElementById('countdownOverlay');
      const textElem = document.getElementById('countdownText');
      overlay.style.display = 'flex';

      let count = 3;
      textElem.textContent = count;

      const timer = setInterval(() => {
        count--;
        if (count > 0) {
          textElem.textContent = count;
        } else {
          clearInterval(timer);
          overlay.style.display = 'none';
          this.triggerFlash();
          resolve();
        }
      }, 1000);
    });
  }

  triggerFlash() {
    const flash = document.getElementById('flashOverlay');
    flash.classList.add('flash-active');
    setTimeout(() => flash.classList.remove('flash-active'), 150);
  }

  toggleFlip() {
    this.isFlipped = !this.isFlipped;
    const video = this.videoElem || document.getElementById('webcamVideo');
    const btnFlip = document.getElementById('btnToggleFlip');

    if (video) {
      const transformVal = this.isFlipped ? 'scaleX(-1)' : 'scaleX(1)';
      video.style.setProperty('transform', transformVal, 'important');
      video.style.setProperty('-webkit-transform', transformVal, 'important');
    }

    if (btnFlip) {
      if (this.isFlipped) {
        btnFlip.innerHTML = '<i class="fa-solid fa-right-left"></i> กลับด้านภาพ: เปิด (Flipped)';
        btnFlip.style.borderColor = 'var(--accent-pink)';
        btnFlip.style.background = 'rgba(236, 72, 153, 0.25)';
        btnFlip.style.color = '#FFFFFF';
      } else {
        btnFlip.innerHTML = '<i class="fa-solid fa-right-left"></i> กลับด้านภาพ: ปิด (Normal)';
        btnFlip.style.borderColor = 'var(--card-border)';
        btnFlip.style.background = '#27272A';
        btnFlip.style.color = '#A1A1AA';
      }
    }
  }

  captureShotToSlot(slotIdx) {
    const ctx = this.canvasElem.getContext('2d');
    this.canvasElem.width = this.videoElem.videoWidth || 640;
    this.canvasElem.height = this.videoElem.videoHeight || 480;

    ctx.save();
    if (this.isFlipped) {
      // Mirror view
      ctx.translate(this.canvasElem.width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(this.videoElem, 0, 0, this.canvasElem.width, this.canvasElem.height);
    ctx.restore();

    const dataUrl = this.canvasElem.toDataURL('image/jpeg', 0.92);
    this.sessionPhotos[slotIdx] = dataUrl;

    // Update Shot Thumbnail Card UI
    const thumbDiv = document.getElementById(`thumb${slotIdx}`);
    if (thumbDiv) {
      thumbDiv.innerHTML = `<img src="${dataUrl}" alt="Shot ${slotIdx + 1}">`;
    }

    const card = document.querySelector(`.shot-card[data-slot="${slotIdx}"] .btn-retake`);
    if (card) card.innerHTML = `<i class="fa-solid fa-rotate-right"></i> ถ่ายใหม่`;
  }

  resetSession() {
    this.sessionId = 'session_' + Date.now();
    this.sessionPhotos = [null, null, null];

    for (let i = 0; i < 3; i++) {
      const thumbDiv = document.getElementById(`thumb${i}`);
      if (thumbDiv) {
        thumbDiv.innerHTML = `<i class="fa-solid fa-image"></i><span>ช็อตที่ ${i + 1}</span>`;
      }
      const card = document.querySelector(`.shot-card[data-slot="${i}"] .btn-retake`);
      if (card) card.innerHTML = `<i class="fa-solid fa-camera"></i> ถ่ายช็อต ${i + 1}`;
    }

    const compImg = document.getElementById('compositeResultImg');
    if (compImg) compImg.style.display = 'none';
    this.lastCompositeResult = null;

    // Immediately switch back to camera client view and scroll up
    this.goToStep1();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ==========================================
  // API COMPOSITE & GDRIVE INTEGRATION (STEP 2)
  // ==========================================
  async renderCompositeStrip() {
    const filledPhotos = this.sessionPhotos.filter(p => p !== null);
    if (filledPhotos.length === 0) return;

    const photo1 = this.sessionPhotos[0] || filledPhotos[0];
    const photo2 = this.sessionPhotos[1] || filledPhotos[1] || photo1;
    const photo3 = this.sessionPhotos[2] || filledPhotos[2] || photo1;

    const spinner = document.getElementById('renderSpinner');
    const compImg = document.getElementById('compositeResultImg');
    if (spinner) spinner.style.display = 'flex';
    if (compImg) compImg.style.display = 'none';

    const formData = new FormData();
    formData.append('image1', photo1);
    formData.append('image2', photo2);
    formData.append('image3', photo3);
    formData.append('frame_key', this.selectedFrameKey);
    formData.append('session_id', this.sessionId);

    try {
      const res = await fetch('/api/composite', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (data.status === 'success') {
        if (compImg) {
          compImg.src = `${data.url}?t=${Date.now()}`;
          compImg.style.display = 'block';
        }
        this.lastCompositeResult = data;
      }
    } catch (err) {
      console.error('Composite rendering error:', err);
    } finally {
      if (spinner) spinner.style.display = 'none';
    }
  }

  async uploadGDriveAndShowQR() {
    if (!this.lastCompositeResult || !this.lastCompositeResult.filename) {
      await this.renderCompositeStrip();
      if (!this.lastCompositeResult || !this.lastCompositeResult.filename) {
        alert('กรุณาถ่ายรูปและเลือกกรอบรูปก่อนสแกน QR Code');
        return;
      }
    }

    const modal = document.getElementById('qrModal');
    const qrSpinner = document.getElementById('qrSpinner');
    const qrImg = document.getElementById('qrImg');
    const urlInput = document.getElementById('gdriveUrlInput');

    if (modal) modal.style.display = 'flex';
    if (qrSpinner) qrSpinner.style.display = 'flex';
    if (qrImg) qrImg.style.display = 'none';
    if (urlInput) urlInput.value = '';

    const formData = new FormData();
    formData.append('filename', this.lastCompositeResult.filename);

    try {
      const res = await fetch('/api/upload-gdrive', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (data.status === 'success') {
        if (qrImg) {
          qrImg.src = `${data.qr_url}?t=${Date.now()}`;
          qrImg.style.display = 'block';
        }
        if (urlInput) urlInput.value = data.gdrive_url;
      } else {
        if (urlInput) urlInput.value = data.message || 'GDrive Upload not configured.';
      }
    } catch (err) {
      console.error('GDrive upload error:', err);
      if (urlInput) urlInput.value = 'Upload Failed.';
    } finally {
      if (qrSpinner) qrSpinner.style.display = 'none';
    }
  }
}

// Initialize Photo Booth Web App
document.addEventListener('DOMContentLoaded', () => {
  window.app = new BeautyPlusApp();
});
