// ============================================
// DOM READY
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    'use strict';
    
    // ============================================
    // ELEMENTS
    // ============================================
    const shortenBtn = document.getElementById('shortenBtn');
    const longUrlInput = document.getElementById('longUrl');
    const customCodeInput = document.getElementById('customCode');
    const expiresInSelect = document.getElementById('expiresIn');
    const resultSection = document.getElementById('resultSection');
    const shortenedUrlInput = document.getElementById('shortenedUrl');
    const copyBtn = document.getElementById('copyBtn');
    const shareBtn = document.getElementById('shareBtn');
    const qrToggleBtn = document.getElementById('qrToggleBtn');
    const statsBtn = document.getElementById('statsBtn');
    const qrSection = document.getElementById('qrSection');
    const qrContainer = document.getElementById('qrcode');
    const downloadQrBtn = document.getElementById('downloadQrBtn');
    const pasteBtn = document.getElementById('pasteBtn');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');
    
    let currentShortUrl = '';
    let qrCodeInstance = null;
    
    // ============================================
    // AUTO-FOCUS
    // ============================================
    if (longUrlInput) {
        longUrlInput.focus();
    }
    
    // ============================================
    // PASTE FUNCTIONALITY
    // ============================================
    if (pasteBtn) {
        pasteBtn.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                longUrlInput.value = text;
                longUrlInput.focus();
                // Auto-shorten after paste
                setTimeout(() => {
                    if (longUrlInput.value.trim()) {
                        shortenBtn.click();
                    }
                }, 300);
                showToast('📋 Pasted from clipboard');
            } catch {
                showToast('Unable to read clipboard. Please paste manually.', 'error');
            }
        });
    }
    
    // ============================================
    // ENTER KEY SHORTCUT
    // ============================================
    longUrlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (longUrlInput.value.trim()) {
                shortenBtn.click();
            }
        }
    });
    
    // ============================================
    // AUTO-PREFIX URL ON BLUR
    // ============================================
    longUrlInput.addEventListener('blur', function() {
        let url = this.value.trim();
        if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
            this.value = 'https://' + url;
        }
    });
    
    // ============================================
    // SHORTEN FUNCTION
    // ============================================
    async function shortenUrl() {
        const url = longUrlInput.value.trim();
        const customCode = customCodeInput.value.trim();
        const expiresIn = expiresInSelect.value;
        
        // Validate
        if (!url) {
            showToast('Please enter a URL', 'error');
            longUrlInput.focus();
            return;
        }
        
        // Show loading
        shortenBtn.disabled = true;
        shortenBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Shortening...';
        
        try {
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    custom_code: customCode || undefined,
                    expires_in: expiresIn
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentShortUrl = data.short_url;
                shortenedUrlInput.value = data.short_url;
                resultSection.classList.remove('hidden');
                
                // Generate QR Code
                generateQRCode(data.short_url);
                
                // Auto-copy to clipboard
                try {
                    await navigator.clipboard.writeText(data.short_url);
                    showToast('✅ Copied to clipboard!');
                } catch {
                    showToast('✨ Link created!');
                }
                
                // Scroll to result
                setTimeout(() => {
                    resultSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
                
                // Update stats button
                if (statsBtn) {
                    const code = data.short_code || data.short_url.split('/').pop();
                    statsBtn.onclick = () => {
                        window.location.href = `/${code}+`;
                    };
                    statsBtn.style.display = 'inline-flex';
                }
                
            } else {
                showToast(data.error || 'Something went wrong', 'error');
            }
        } catch (err) {
            showToast('Network error. Please try again.', 'error');
        } finally {
            shortenBtn.disabled = false;
            shortenBtn.innerHTML = '<i class="fas fa-bolt"></i> Shorten Now';
        }
    }
    
    // ============================================
    // SHORTEN BUTTON
    // ============================================
    if (shortenBtn) {
        shortenBtn.addEventListener('click', shortenUrl);
    }
    
    // ============================================
    // COPY FUNCTION
    // ============================================
    async function copyLink() {
        const url = shortenedUrlInput.value;
        if (!url) return;
        
        try {
            await navigator.clipboard.writeText(url);
            showToast('✅ Copied to clipboard!');
            
            // Visual feedback
            copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            copyBtn.style.borderColor = 'var(--success)';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                copyBtn.style.borderColor = '';
            }, 2000);
        } catch {
            // Fallback
            shortenedUrlInput.select();
            document.execCommand('copy');
            showToast('✅ Copied!');
        }
    }
    
    if (copyBtn) {
        copyBtn.addEventListener('click', copyLink);
    }
    
    // ============================================
    // SHARE FUNCTION
    // ============================================
    function shareLink() {
        const url = shortenedUrlInput.value;
        if (!url) return;
        
        if (navigator.share) {
            navigator.share({
                title: 'wafyurl - Short Link',
                text: 'Check out this link:',
                url: url
            }).catch(() => {});
        } else {
            copyLink();
            showToast('📋 Link copied to share!');
        }
    }
    
    if (shareBtn) {
        shareBtn.addEventListener('click', shareLink);
    }
    
    // ============================================
    // QR CODE TOGGLE
    // ============================================
    if (qrToggleBtn) {
        qrToggleBtn.addEventListener('click', () => {
            if (qrSection.classList.contains('hidden')) {
                qrSection.classList.remove('hidden');
                qrToggleBtn.innerHTML = '<i class="fas fa-times"></i> Hide QR';
                if (!qrCodeInstance && currentShortUrl) {
                    generateQRCode(currentShortUrl);
                }
            } else {
                qrSection.classList.add('hidden');
                qrToggleBtn.innerHTML = '<i class="fas fa-qrcode"></i> QR Code';
            }
        });
    }
    
    // ============================================
    // QR CODE GENERATION
    // ============================================
    function generateQRCode(url) {
        if (!qrContainer) return;
        
        // Clear old QR
        qrContainer.innerHTML = '';
        
        try {
            qrCodeInstance = new QRCode(qrContainer, {
                text: url,
                width: 160,
                height: 160,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            });
            
            // Show download button
            if (downloadQrBtn) {
                downloadQrBtn.style.display = 'inline-flex';
                downloadQrBtn.onclick = downloadQR;
            }
        } catch (e) {
            console.error('QR generation failed:', e);
        }
    }
    
    // ============================================
    // DOWNLOAD QR CODE
    // ============================================
    function downloadQR() {
        const canvas = qrContainer.querySelector('canvas');
        const img = qrContainer.querySelector('img');
        
        if (canvas) {
            const link = document.createElement('a');
            link.download = 'wafyurl_qr.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        } else if (img) {
            const link = document.createElement('a');
            link.download = 'wafyurl_qr.png';
            link.href = img.src;
            link.click();
        } else {
            showToast('QR code not ready', 'error');
        }
    }
    
    // ============================================
    // TOAST NOTIFICATION
    // ============================================
    function showToast(message, type = 'success') {
        if (!toast || !toastMessage) return;
        
        toastMessage.textContent = message;
        toastIcon.className = type === 'error' ? 'fas fa-exclamation-circle' : 'fas fa-check-circle';
        
        if (type === 'error') {
            toast.style.borderColor = 'var(--error)';
            toast.style.background = 'rgba(255, 71, 87, 0.12)';
            toastIcon.style.color = 'var(--error)';
        } else {
            toast.style.borderColor = 'var(--neon-blue)';
            toast.style.background = 'rgba(0, 210, 255, 0.12)';
            toastIcon.style.color = 'var(--neon-blue)';
        }
        
        toast.classList.add('show');
        
        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    // ============================================
    // KEYBOARD SHORTCUT: Ctrl+K for focus
    // ============================================
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (longUrlInput) {
                longUrlInput.focus();
                longUrlInput.select();
            }
        }
    });
    
    // ============================================
    // HISTORY (localStorage)
    // ============================================
    function saveToHistory(shortUrl, longUrl) {
        try {
            let history = JSON.parse(localStorage.getItem('wafyurl_history') || '[]');
            const entry = {
                short: shortUrl,
                long: longUrl,
                time: new Date().toISOString()
            };
            history = [entry, ...history.filter(h => h.short !== shortUrl)];
            history = history.slice(0, 10);
            localStorage.setItem('wafyurl_history', JSON.stringify(history));
        } catch {}
    }
    
    // Save after shortening
    const originalShorten = shortenUrl;
    shortenUrl = async function() {
        await originalShorten.call(this);
        if (currentShortUrl && longUrlInput.value) {
            saveToHistory(currentShortUrl, longUrlInput.value);
        }
    };
    
    // ============================================
    // EXPOSE GLOBALLY
    // ============================================
    window.wafyurl = {
        shorten: shortenUrl,
        copy: copyLink,
        share: shareLink,
        showToast: showToast,
        generateQR: generateQRCode
    };
    
    console.log('🚀 wafyurl loaded successfully!');
    console.log('📌 Press Ctrl+K to focus the URL input');
});