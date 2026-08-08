document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // ============================================
    // ELEMENTS
    // ============================================
    
    const shortenBtn = document.getElementById('shortenBtn');
    const longUrlInput = document.getElementById('longUrl');
    const customCodeInput = document.getElementById('customCode');
    const expiresInSelect = document.getElementById('expiresIn');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('togglePassword');
    const resultSection = document.getElementById('resultSection');
    const shortenedUrlInput = document.getElementById('shortenedUrl');
    const copyBtn = document.getElementById('copyBtn');
    const shareBtn = document.getElementById('shareBtn');
    const qrToggleBtn = document.getElementById('qrToggleBtn');
    const previewBtn = document.getElementById('previewBtn');
    const statsBtn = document.getElementById('statsBtn');
    const qrSection = document.getElementById('qrSection');
    const qrContainer = document.getElementById('qrcode');
    const downloadQrBtn = document.getElementById('downloadQrBtn');
    const pasteBtn = document.getElementById('pasteBtn');
    const bulkToggleBtn = document.getElementById('bulkToggleBtn');
    const bulkArea = document.getElementById('bulkArea');
    const bulkUrls = document.getElementById('bulkUrls');
    const bulkShortenBtn = document.getElementById('bulkShortenBtn');
    const bulkResults = document.getElementById('bulkResults');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');
    const previewModal = document.getElementById('previewModal');
    const previewImage = document.getElementById('previewImage');
    const previewTitle = document.getElementById('previewTitle');
    const previewDesc = document.getElementById('previewDesc');
    
    let currentShortUrl = '';
    let qrCodeInstance = null;
    let currentShortCode = '';
    
    // ============================================
    // PASSWORD TOGGLE (Show/Hide)
    // ============================================
    
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            }
        });
    }
    
    // ============================================
    // AUTO-FOCUS
    // ============================================
    
    if (longUrlInput) longUrlInput.focus();
    
    // ============================================
    // PASTE FUNCTIONALITY
    // ============================================
    
    if (pasteBtn) {
        pasteBtn.addEventListener('click', async function() {
            try {
                const text = await navigator.clipboard.readText();
                longUrlInput.value = text;
                longUrlInput.focus();
                setTimeout(function() {
                    if (longUrlInput.value.trim()) {
                        shortenBtn.click();
                    }
                }, 300);
                showToast('Pasted from clipboard');
            } catch {
                showToast('Unable to read clipboard', 'error');
            }
        });
    }
    
    // ============================================
    // ENTER KEY SHORTCUT
    // ============================================
    
    longUrlInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (longUrlInput.value.trim()) {
                shortenBtn.click();
            }
        }
    });
    
    // ============================================
    // AUTO-PREFIX URL
    // ============================================
    
    longUrlInput.addEventListener('blur', function() {
        let url = this.value.trim();
        if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
            this.value = 'https://' + url;
        }
    });
    
    // ============================================
    // BULK TOGGLE
    // ============================================
    
    if (bulkToggleBtn) {
        bulkToggleBtn.addEventListener('click', function() {
            if (bulkArea.classList.contains('hidden')) {
                bulkArea.classList.remove('hidden');
                this.innerHTML = '<i class="fas fa-times"></i> Hide Bulk';
            } else {
                bulkArea.classList.add('hidden');
                this.innerHTML = '<i class="fas fa-layer-group"></i> Bulk Shorten';
            }
        });
    }
    
    // ============================================
    // SHORTEN FUNCTION
    // ============================================
    
    async function shortenUrl() {
        const url = longUrlInput.value.trim();
        const customCode = customCodeInput.value.trim();
        const expiresIn = expiresInSelect.value;
        const password = passwordInput ? passwordInput.value.trim() : '';
        
        if (!url) {
            showToast('Please enter a URL', 'error');
            longUrlInput.focus();
            return;
        }
        
        shortenBtn.disabled = true;
        shortenBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Shortening...';
        
        try {
            const payload = {
                url: url,
                custom_code: customCode || undefined,
                expires_in: expiresIn
            };
            
            if (password) {
                payload.password = password;
            }
            
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentShortUrl = data.short_url;
                currentShortCode = data.short_code || data.short_url.split('/').pop();
                shortenedUrlInput.value = data.short_url;
                resultSection.classList.remove('hidden');
                
                generateQRCode(data.short_url);
                
                try {
                    await navigator.clipboard.writeText(data.short_url);
                    showToast('Copied to clipboard!');
                } catch {
                    showToast('Link created!');
                }
                
                setTimeout(function() {
                    resultSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
                
                if (statsBtn) {
                    statsBtn.style.display = 'inline-flex';
                    statsBtn.onclick = function() {
                        window.location.href = '/' + currentShortCode + '+';
                    };
                }
                
                if (previewBtn) {
                    previewBtn.onclick = function() {
                        showPreview(currentShortUrl);
                    };
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
    
    if (shortenBtn) {
        shortenBtn.addEventListener('click', shortenUrl);
    }
    
    // ============================================
    // BULK SHORTEN
    // ============================================
    
    if (bulkShortenBtn) {
        bulkShortenBtn.addEventListener('click', async function() {
            const text = bulkUrls.value;
            const urls = text.split(/[\n,]+/).map(function(u) { return u.trim(); }).filter(function(u) { return u; });
            
            if (urls.length === 0) {
                showToast('Please enter at least one URL', 'error');
                return;
            }
            if (urls.length > 20) {
                showToast('Maximum 20 URLs at a time', 'error');
                return;
            }
            
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            bulkResults.innerHTML = '';
            
            const results = [];
            for (const url of urls) {
                try {
                    const res = await fetch('/shorten', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url: url })
                    });
                    const data = await res.json();
                    results.push({
                        original: url,
                        short: data.short_url || 'Failed',
                        success: data.success || false
                    });
                } catch {
                    results.push({
                        original: url,
                        short: 'Error',
                        success: false
                    });
                }
            }
            
            bulkResults.innerHTML = results.map(function(r) {
                var statusIcon = r.success ? 
                    '<span class="status-icon success"><i class="fas fa-check-circle"></i></span>' : 
                    '<span class="status-icon error"><i class="fas fa-times-circle"></i></span>';
                return '<div class="bulk-item">' +
                    statusIcon +
                    '<span class="original">' + escapeHtml(r.original) + '</span>' +
                    '<span class="short">' + escapeHtml(r.short) + '</span>' +
                    (r.success ? '<button class="btn-copy-mini" onclick="copyText(\'' + escapeHtml(r.short) + '\')"><i class="fas fa-copy"></i></button>' : '') +
                    '</div>';
            }).join('');
            
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-bolt"></i> Shorten All';
            showToast(results.filter(function(r) { return r.success; }).length + ' links shortened');
        });
    }
    
    // ============================================
    // COPY FUNCTION
    // ============================================
    
    async function copyLink() {
        const url = shortenedUrlInput.value;
        if (!url) return;
        
        try {
            await navigator.clipboard.writeText(url);
            showToast('Copied to clipboard!');
            copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(function() {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            }, 2000);
        } catch {
            shortenedUrlInput.select();
            document.execCommand('copy');
            showToast('Copied!');
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
            }).catch(function() {});
        } else {
            copyLink();
            showToast('Link copied to share');
        }
    }
    
    if (shareBtn) {
        shareBtn.addEventListener('click', shareLink);
    }
    
    // ============================================
    // QR TOGGLE
    // ============================================
    
    if (qrToggleBtn) {
        qrToggleBtn.addEventListener('click', function() {
            if (qrSection.classList.contains('hidden')) {
                qrSection.classList.remove('hidden');
                this.innerHTML = '<i class="fas fa-times"></i> Hide QR';
                if (!qrCodeInstance && currentShortUrl) {
                    generateQRCode(currentShortUrl);
                }
            } else {
                qrSection.classList.add('hidden');
                this.innerHTML = '<i class="fas fa-qrcode"></i> QR Code';
            }
        });
    }
    
    // ============================================
    // QR GENERATION
    // ============================================
    
    function generateQRCode(url) {
        if (!qrContainer) return;
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
            
            if (downloadQrBtn) {
                downloadQrBtn.style.display = 'inline-flex';
                downloadQrBtn.onclick = downloadQR;
            }
        } catch (e) {
            console.error('QR generation failed:', e);
        }
    }
    
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
    // PREVIEW
    // ============================================
    
    async function showPreview(shortUrl) {
        if (!previewModal) return;
        
        previewModal.classList.remove('hidden');
        previewTitle.textContent = 'Loading preview...';
        previewDesc.textContent = '';
        previewImage.src = '';
        
        try {
            const code = shortUrl.split('/').pop();
            const linkRes = await fetch('/api/link/' + code);
            const linkData = await linkRes.json();
            
            if (!linkData.original_url) {
                throw new Error('No URL found');
            }
            
            const previewRes = await fetch('/api/preview?url=' + encodeURIComponent(linkData.original_url));
            const previewData = await previewRes.json();
            
            previewTitle.textContent = previewData.title || 'No title available';
            previewDesc.textContent = previewData.description || 'No description available';
            if (previewData.image) {
                previewImage.src = previewData.image;
                previewImage.style.display = 'block';
            } else {
                previewImage.style.display = 'none';
            }
        } catch (err) {
            previewTitle.textContent = 'Preview not available';
            previewDesc.textContent = 'Could not fetch link preview.';
            previewImage.style.display = 'none';
        }
    }
    
    window.closePreview = function() {
        if (previewModal) {
            previewModal.classList.add('hidden');
        }
    };
    
    if (previewModal) {
        previewModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closePreview();
            }
        });
    }
    
    // ============================================
    // TOAST FUNCTION
    // ============================================
    
    function showToast(message, type) {
        type = type || 'success';
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
        toast._timeout = setTimeout(function() {
            toast.classList.remove('show');
        }, 3000);
    }
    
    // ============================================
    // UTILITY: ESCAPE HTML
    // ============================================
    
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ============================================
    // UTILITY: COPY TEXT (Global)
    // ============================================
    
    window.copyText = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('Copied!');
            }).catch(function() {
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }
    };
    
    function fallbackCopy(text) {
        var input = document.createElement('input');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showToast('Copied!');
    }
    
    // ============================================
    // KEYBOARD SHORTCUTS: Ctrl+K
    // ============================================
    
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (longUrlInput) {
                longUrlInput.focus();
                longUrlInput.select();
            }
        }
    });
    
    console.log('wafyurl loaded successfully!');
    console.log('Press Ctrl+K to focus the URL input');
});