function updateFileName(input, targetId) {
  const fileName = input.files.length > 0 ? input.files[0].name : 'No file selected';
  document.getElementById(targetId).textContent = fileName;
}

const API = "http://localhost:8000";
let currentMode = 'image';
let isProcessing = false;
let webcamStream = null;
let videoInterval = null;
let sessionId = null;  // Session ID for tracking

const elements = {
  uploadBtn: () => document.getElementById("upload-btn"),
  loading: () => document.getElementById("loading"),
  resultCard: () => document.getElementById("result-card"),
  resultImg: () => document.getElementById("result-image"),
  resultJson: () => document.getElementById("result-json"),
  resultInfo: () => document.getElementById("result-info"),
  canvas: () => document.getElementById("process-canvas"),
  webcamVideo: () => document.getElementById("webcam-video"),
  webcamOverlay: () => document.getElementById("webcam-overlay"),
  uploadedVideo: () => document.getElementById("uploaded-video"),
  videoOverlay: () => document.getElementById("video-overlay"),
  videoFile: () => document.getElementById("video-file"),
  imageFile: () => document.getElementById("file")
};

function switchInputMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.innerText.toLowerCase().includes(mode.toLowerCase()));
  });

  document.getElementById('image-input-area').style.display = mode === 'image' ? 'block' : 'none';
  document.getElementById('video-input-area').style.display = mode === 'video' ? 'block' : 'none';
  document.getElementById('webcam-input-area').style.display = mode === 'webcam' ? 'block' : 'none';

  stopAll();
}

function stopAll() {
  stopVideoProcessing();
  stopWebcam();
  elements.resultCard().style.display = 'none';
  clearOverlay(elements.webcamOverlay());
  clearOverlay(elements.videoOverlay());
}

function clearOverlay(canvas) {
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

async function uploadImage() {
  const file = elements.imageFile().files[0];
  if (!file) {
    alert("Please select an image!");
    return;
  }
  await sendFrame(file, false);
}

// Video Processing Logic
function processVideo() {
  const video = elements.uploadedVideo();
  const file = elements.videoFile().files[0];

  if (!file && !video.src) {
    alert("Please select a video first!");
    return;
  }

  if (file && !video.src) {
    const url = URL.createObjectURL(file);
    video.src = url;
    document.getElementById('video-display-container').style.display = 'block';
  }

  // Generate new session ID for this video processing session
  sessionId = crypto.randomUUID();
  console.log('[Tracking] Started video session:', sessionId);

  isProcessing = true;
  document.getElementById('process-video-btn').style.display = 'none';
  document.getElementById('stop-video-btn').style.display = 'inline-block';

  video.play();
  startDetectionLoop(video, elements.videoOverlay());
}

function stopVideoProcessing() {
  isProcessing = false;
  const video = elements.uploadedVideo();
  video.pause();
  document.getElementById('process-video-btn').style.display = 'inline-block';
  document.getElementById('stop-video-btn').style.display = 'none';
  if (videoInterval) clearTimeout(videoInterval);

  // Clear session ID
  if (sessionId) {
    console.log('[Tracking] Stopped video session:', sessionId);
    sessionId = null;
  }
}

// Webcam Logic
async function startWebcam() {
  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
    const video = elements.webcamVideo();
    video.srcObject = webcamStream;
    document.getElementById('webcam-container').style.display = 'block';
    document.getElementById('start-webcam-btn').style.display = 'none';
    document.getElementById('stop-webcam-btn').style.display = 'inline-block';

    // Generate new session ID for this webcam session
    sessionId = crypto.randomUUID();
    console.log('[Tracking] Started webcam session:', sessionId);

    isProcessing = true;
    startDetectionLoop(video, elements.webcamOverlay());
  } catch (err) {
    console.error("Webcam error:", err);
    alert("Unable to access Webcam: " + err.message);
  }
}

function stopWebcam() {
  isProcessing = false;
  if (webcamStream) {
    webcamStream.getTracks().forEach(track => track.stop());
    webcamStream = null;
  }
  const video = elements.webcamVideo();
  video.srcObject = null;
  document.getElementById('start-webcam-btn').style.display = 'inline-block';
  document.getElementById('stop-webcam-btn').style.display = 'none';
  if (videoInterval) clearTimeout(videoInterval);

  // Clear session ID
  if (sessionId) {
    console.log('[Tracking] Stopped webcam session:', sessionId);
    sessionId = null;
  }
}

async function startDetectionLoop(videoSource, overlayCanvas) {
  if (videoInterval) clearTimeout(videoInterval);

  const detectFrame = async () => {
    if (!isProcessing) return;

    const canvas = elements.canvas();
    const context = canvas.getContext('2d');

    // Set internal processing canvas dimensions to match video
    canvas.width = videoSource.videoWidth;
    canvas.height = videoSource.videoHeight;

    if (canvas.width > 0 && canvas.height > 0) {
      context.drawImage(videoSource, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.6));
      if (blob) {
        const data = await sendFrame(blob, true);
        if (data) {
          drawResults(data, overlayCanvas, videoSource);
        }
      }
    }

    if (isProcessing) {
      videoInterval = setTimeout(detectFrame, 100); // Reduced delay for smoother experience
    }
  };

  detectFrame();
}

function drawResults(data, canvas, video) {
  const ctx = canvas.getContext('2d');

  // Set canvas display size to match video element size
  canvas.width = video.clientWidth;
  canvas.height = video.clientHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!data.results) return;

  const scaleX = canvas.width / data.width;
  const scaleY = canvas.height / data.height;

  data.results.forEach(res => {
    const isMask = res.label.toLowerCase().includes("mask") && !res.label.toLowerCase().includes("no");
    const color = isMask ? "#22c55e" : "#ef4444";
    const box = res.box;

    const x = box.startX * scaleX;
    const y = box.startY * scaleY;
    const w = (box.endX - box.startX) * scaleX;
    const h = (box.endY - box.startY) * scaleY;

    // Draw box
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);

    // Draw label background
    ctx.fillStyle = color;
    const labelText = `${isMask ? "Mask" : "No Mask"} ${(res.confidence * 100).toFixed(0)}%`;
    ctx.font = "bold 14px Segoe UI, Arial";
    const labelWidth = ctx.measureText(labelText).width + 10;
    ctx.fillRect(x, y - 25, labelWidth, 25);

    // Draw text
    ctx.fillStyle = "white";
    ctx.fillText(labelText, x + 5, y - 7);
  });
}

async function sendFrame(blob, isLive = false) {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("You need to log in!");
    window.location.href = "/index.html";
    return;
  }

  if (!isLive) {
    elements.loading().style.display = "block";
    elements.resultCard().style.display = "none";
  }

  const formData = new FormData();
  formData.append("file", blob, "frame.jpg");

  // Add session_id for tracking if in live mode (webcam/video)
  if (isLive && sessionId) {
    formData.append("session_id", sessionId);
  }

  const endpoint = isLive ? "/predict/from-file-json" : "/predict/from-file";

  try {
    const res = await fetch(API + endpoint, {
      method: "POST",
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });

    if (!res.ok) throw new Error("API Error");

    const data = await res.json();
    updateUI(data, !isLive);
    return data;
  } catch (error) {
    console.error("Detection error:", error);
    if (!isLive) alert("Processing error!");
    return null;
  } finally {
    if (!isLive) elements.loading().style.display = "none";
  }
}

function updateUI(data, showImage = true) {
  const resultCard = elements.resultCard();
  const resultImg = elements.resultImg();
  const resultInfo = elements.resultInfo();
  const resultJson = elements.resultJson();

  if (showImage && data.image_base64) {
    resultImg.src = "data:image/jpeg;base64," + data.image_base64;
    resultImg.style.display = "block";
  } else if (!showImage) {
    resultImg.style.display = "none";
  }

  let infoHtml = `<h4 style="margin: 0 0 10px 0; color: #333;">Results:</h4>`;
  infoHtml += `<p style="margin: 0 0 10px 0;">Detected <strong>${data.faces_detected}</strong> face(s).</p>`;

  if (data.results && data.results.length > 0) {
    data.results.forEach((res) => {
      const isMask = res.label.toLowerCase().includes("mask") && !res.label.toLowerCase().includes("no");
      const badgeClass = isMask ? "badge-mask" : "badge-no-mask";
      const labelEn = isMask ? "Wearing Mask" : "No Mask";

      infoHtml += `
        <div style="margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; background: #f9f9f9; padding: 6px 10px; border-radius: 6px; font-size: 13px;">
          <span class="badge ${badgeClass}" style="font-size: 11px;">${labelEn}</span>
          <span style="color: #666;">${(res.confidence * 100).toFixed(0)}%</span>
        </div>
      `;
    });
  }

  resultInfo.innerHTML = infoHtml;
  resultJson.innerText = JSON.stringify(data, null, 2);

  if (showImage) {
    resultCard.style.display = "block";
  }
}

// Initial setup
window.addEventListener('load', () => {
  // Check for video file change to update preview
  document.getElementById('video-file')?.addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      const video = elements.uploadedVideo();
      video.src = url;
      document.getElementById('video-display-container').style.display = 'block';
      clearOverlay(elements.videoOverlay());
    }
  });
});
