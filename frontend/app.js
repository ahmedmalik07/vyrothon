document.addEventListener('DOMContentLoaded', () => {
    // 🔥 Vercel Deployment Setup:
    // This is connected safely to the localhost.run public HTTPS tunnel!
    const API_BASE = 'https://aa7b4c7c137a98.lhr.life';

    // --- Navigation ---
    const navLinks = document.querySelectorAll('.nav-links li');
    const views = document.querySelectorAll('.view');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.forEach(l => l.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));
            
            link.classList.add('active');
            const target = document.getElementById(link.dataset.target);
            target.classList.add('active');

            if (link.dataset.target === 'explorer-view') fetchFaces();
        });
    });

    // --- View 1: Auth Engine ---
    const fileInput = document.getElementById('selfie-file');
    const uploadZone = document.getElementById('upload-zone');
    const authBtn = document.getElementById('auth-btn');
    const authResult = document.getElementById('auth-result');
    const galleryContainer = document.getElementById('gallery-container');
    const fileNameDisplay = document.getElementById('file-name-display');

    // Drag Drop
    uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
    uploadZone.addEventListener('drop', e => {
        e.preventDefault(); uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; updateFileUI(); }
    });
    uploadZone.addEventListener('click', () => { if(!webcamStream) fileInput.click(); });
    fileInput.addEventListener('change', updateFileUI);

    function updateFileUI() {
        if(webcamStream) stopWebcam();
        if(fileInput.files.length) {
            fileNameDisplay.textContent = fileInput.files[0].name;
            authBtn.disabled = false;
        }
    }

    // Webcam
    const startCameraBtn = document.getElementById('start-camera-btn');
    const captureBtn = document.getElementById('capture-btn');
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('webcam-canvas');
    const uploadContent = document.getElementById('upload-content');
    
    let webcamStream = null;

    startCameraBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = webcamStream;
            video.style.display = 'block';
            captureBtn.style.display = 'block';
            uploadContent.style.display = 'none';
            startCameraBtn.style.display = 'none';
        } catch(e) { alert('Camera access denied'); }
    });

    captureBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        canvas.toBlob(blob => {
            const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
            const dt = new DataTransfer(); dt.items.add(file);
            fileInput.files = dt.files;
            
            uploadContent.innerHTML = `<img src="${URL.createObjectURL(blob)}" style="width:100%; border-radius:8px;">`;
            updateFileUI();
            stopWebcam();
            uploadContent.style.display = 'flex';
        }, 'image/jpeg');
    });

    function stopWebcam() {
        if(webcamStream) { webcamStream.getTracks().forEach(t => t.stop()); webcamStream = null; }
        video.style.display = 'none'; captureBtn.style.display = 'none'; startCameraBtn.style.display = 'block';
    }

    // Execute Auth
    authBtn.addEventListener('click', async () => {
        if (!fileInput.files.length) return;
        
        authBtn.disabled = true; authBtn.textContent = 'Processing Vector...';
        authResult.classList.remove('hidden', 'success', 'error');

        const fd = new FormData(); fd.append('file', fileInput.files[0]);
        
        try {
            const res = await fetch(`${API_BASE}/auth/selfie`, { method: 'POST', body: fd });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail);

            authResult.className = 'alert success';
            authResult.innerHTML = `<strong>Identity Verified!</strong><br><span id="auth-person-name" style="font-size: 1.2rem; display:block; margin: 0.5rem 0; color: var(--primary);">Loading Neural Map...</span>Grab ID: ${data.grab_id}<br>Match Confidence: ${(data.confidence*100).toFixed(1)}%`;
            fetchImagesAndRender(data.grab_id, galleryContainer, true);
        } catch(e) {
            authResult.className = 'alert error';
            authResult.innerHTML = `<strong>Access Denied</strong><br>${e.message}`;
            galleryContainer.innerHTML = `<div class="empty-state"><p>Authentication Failed</p></div>`;
        } finally {
            authBtn.disabled = false; authBtn.textContent = 'Authenticate';
        }
    });

    function fetchImagesAndRender(grab_id, container, isMainAuthView = false) {
        container.innerHTML = '<p style="padding:2rem;">Fetching secure photos...</p>';
        fetch(`${API_BASE}/images/${grab_id}`)
            .then(r => r.json())
            .then(data => {
                if(data.images && data.images.length > 0) {
                    
                    // Extract name from the first image's folder path
                    const parts = data.images[0].filepath.split(/[\\/]/);
                    const nameRaw = parts.length > 1 ? parts[parts.length - 2] : "Unknown";
                    const personName = nameRaw.replace(/_/g, " ");

                    if (isMainAuthView) {
                        const nameSpan = document.getElementById('auth-person-name');
                        if (nameSpan) nameSpan.innerHTML = `Welcome back, <strong>${personName}</strong>!`;
                    }
                    
                    container.innerHTML = '';
                    data.images.forEach(img => {
                        const parts = img.filepath.split(/[\\/]/);
                        const nameRaw = parts.length > 1 ? parts[parts.length - 2] : "Unknown";
                        const name = nameRaw.replace(/_/g, " ");

                        const div = document.createElement('div');
                        div.className = 'photo-item';
                        div.innerHTML = `
                            <img src="${API_BASE}/images/file/${img.id}" class="photo-img">
                            <p class="photo-name">${name}</p>
                            <p class="photo-file" title="${img.filename}">${img.filename}</p>
                        `;
                        container.appendChild(div);
                    });
                } else {
                    container.innerHTML = `<div class="empty-state"><p>No photos found.</p></div>`;
                }
            });
    }

    // --- View 2: Database Explorer ---
    const refreshFacesBtn = document.getElementById('refresh-faces-btn');
    const tableBody = document.getElementById('faces-table-body');
    const idCountDisplay = document.getElementById('total-id-count');
    
    refreshFacesBtn.addEventListener('click', fetchFaces);

    async function fetchFaces() {
        tableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Loading index...</td></tr>';
        refreshFacesBtn.disabled = true;
        
        try {
            const res = await fetch(`${API_BASE}/faces`);
            const data = await res.json();
            
            idCountDisplay.textContent = data.total_identities;
            tableBody.innerHTML = '';
            
            if(data.faces.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Database is empty. Run ingestion first.</td></tr>';
            } else {
                data.faces.forEach(f => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="font-family:monospace; font-size:0.85rem;">${f.grab_id}</td>
                        <td>${f.image_count}</td>
                        <td><button class="btn secondary view-photos-btn" data-id="${f.grab_id}" style="padding:0.25rem 0.5rem; font-size:0.8rem;">View Album</button></td>
                    `;
                    tableBody.appendChild(tr);
                });

                document.querySelectorAll('.view-photos-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const gid = e.target.getAttribute('data-id');
                        openAdminModal(gid);
                    });
                });
            }
        } catch(e) {
            tableBody.innerHTML = `<tr><td colspan="3" style="color:var(--error);">${e.message}</td></tr>`;
        } finally {
            refreshFacesBtn.disabled = false;
        }
    }

    const modal = document.getElementById('admin-modal');
    const modalGallery = document.getElementById('modal-gallery');
    document.querySelector('.close-modal').addEventListener('click', () => modal.style.display = 'none');
    
    function openAdminModal(grab_id) {
        modal.style.display = 'flex';
        fetchImagesAndRender(grab_id, modalGallery);
    }

    // --- View 3: Data Ingestion (Live Terminal) ---
    const ingestTrigger = document.getElementById('trigger-ingest-btn');
    const ingestPath = document.getElementById('ingest-path');
    const terminalLogs = document.getElementById('terminal-logs');

    function addLog(msg, type='system') {
        const p = document.createElement('p');
        p.className = `log ${type}`;
        
        // Add timestamp
        const time = new Date().toLocaleTimeString().split(' ')[0];
        p.innerHTML = `[${time}] ${msg}`;
        terminalLogs.appendChild(p);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    ingestTrigger.addEventListener('click', async () => {
        const folder = ingestPath.value;
        if(!folder) return alert("Enter a path.");

        ingestTrigger.disabled = true;
        terminalLogs.innerHTML = '';
        addLog(`Initiating Recursive Crawler on directory: ${folder}`);
        addLog(`Bypassing cache... Analyzing byte sequences...`, 'warn');
        
        // Setup a simulated interval of tasks while the real request happens
        const pendingMsgs = [
            'Detected valid image encodings. Extracting EXIF layers...',
            'Spinning up dlib face extractor network...',
            'Scanning for human faces (HOG + Euclidean)...',
            'Applying mathematical vector mapping (128-d space)...',
            'Normalizing array distances against db...',
            'Assigning secure grab_ids...',
            'Building SQLAlchemy Many-to-Many Graph structure...'
        ];
        
        let i = 0;
        const fakeProgress = setInterval(() => {
            if (i < pendingMsgs.length) { addLog(pendingMsgs[i]); i++; }
        }, 1500);

        try {
            const res = await fetch(`${API_BASE}/ingest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder: folder })
            });
            const data = await res.json();
            clearInterval(fakeProgress);

            if(!res.ok) throw new Error(data.detail);

            addLog(`✅ INGESTION COMPLETE.`, 'success');
            addLog(`-----------------------------------`);
            addLog(`Indexed Images: ${data.indexed_images}`, 'success');
            addLog(`Unique Faces Found: ${data.total_faces}`, 'success');
            addLog(`Skipped (Duplicates/Corrupt): ${data.skipped_images}`, 'warn');
            
            // refresh db stats if they switch tabs
            fetchFaces();

        } catch(e) {
            clearInterval(fakeProgress);
            addLog(`❌ INGESTION FAILED: ${e.message}`, 'error');
        } finally {
            ingestTrigger.disabled = false;
        }
    });
});
