document.addEventListener('DOMContentLoaded', () => {
    loadMedia();
    loadDevices();

    // Navigation handling
    const navItems = document.querySelectorAll('nav li');
    const pages = document.querySelectorAll('.page');
    const pageTitle = document.getElementById('page-title');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const pageId = item.getAttribute('data-page');

            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            pages.forEach(p => p.classList.remove('active'));
            document.getElementById(`${pageId}-page`).classList.add('active');

            pageTitle.textContent = item.textContent;
        });
    });
});

async function loadMedia() {
    try {
        const response = await fetch('/api/media');
        const media = await response.json();

        document.getElementById('total-media').textContent = media.length;

        const grid = document.getElementById('media-grid');
        grid.innerHTML = '';

        media.forEach(item => {
            const card = document.createElement('div');
            card.className = 'media-card';

            const icon = item.type === 'image' ? '🖼️' : '🎥';

            card.innerHTML = `
                <div class="media-preview">${icon}</div>
                <div class="media-info">
                    <h4>${item.name}</h4>
                    <div class="media-actions">
                        <span>${(item.size / 1024).toFixed(1)} KB</span>
                        <button class="btn-small" onclick="playMedia(${item.id})">Play Now</button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading media:', error);
    }
}

async function playMedia(id) {
    try {
        const response = await fetch(`/api/play_now/${id}`, { method: 'POST' });
        if (response.ok) {
            console.log("Play command sent");
        }
    } catch (error) {
        console.error('Error sending play command:', error);
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const duration = document.getElementById('media-duration').value;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('duration', duration);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            alert('Upload successful!');
            loadMedia();
        } else {
            const error = await response.json();
            alert(`Upload failed: ${error.error}`);
        }
    } catch (error) {
        console.error('Error uploading file:', error);
    }
}

async function loadDevices() {
    // In a real app, you'd fetch this from /api/devices
    // For now, it's simplified
}
