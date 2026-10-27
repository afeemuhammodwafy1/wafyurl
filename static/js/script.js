document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // ============================================
    // ELEMENTS
    // ============================================
    
    const shortenBtn = document.getElementById('shortenBtn');
    const longUrlInput = document.getElementById('longUrl');
    const customCodeInput = document.getElementById('customCode');
    const expiresInSelect = document.getElementById('expiresIn');
    const expiresAtInput = document.getElementById('expiresAt');
    const customExpiryGroup = document.getElementById('customExpiryGroup');
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
    const advancedToggle = document.getElementById('advancedToggle');
    const advancedOptions = document.getElementById('advancedOptions');
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
    
    // Avoid stealing focus on page load, especially on mobile devices.
    
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
    
    if (longUrlInput) {
        longUrlInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (longUrlInput.value.trim() && shortenBtn) shortenBtn.click();
            }
        });
    }
    
    // ============================================
    // AUTO-PREFIX URL
    // ============================================
    
    if (longUrlInput) {
        longUrlInput.addEventListener('blur', function() {
            const value = this.value.trim();
            if (value && !value.startsWith('http://') && !value.startsWith('https://')) {
                this.value = 'https://' + value;
            }
        });
    }
    
    // ============================================
    // ADVANCED OPTIONS
    // ============================================

    if (advancedToggle && advancedOptions) {
        advancedToggle.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', String(!expanded));
            advancedOptions.classList.toggle('hidden', expanded);
        });
    }

    if (expiresInSelect && customExpiryGroup) {
        const syncExpiryField = function() {
            const custom = expiresInSelect.value === 'custom';
            customExpiryGroup.classList.toggle('hidden', !custom);
            if (expiresAtInput) expiresAtInput.required = custom;
        };
        expiresInSelect.addEventListener('change', syncExpiryField);
        syncExpiryField();
    }

    const pageParams = new URLSearchParams(window.location.search);
    if (pageParams.get('customize') === '1' && advancedToggle && advancedOptions) advancedToggle.click();

    // ============================================
    // BULK TOGGLE
    // ============================================
    
    if (bulkToggleBtn) {
        bulkToggleBtn.addEventListener('click', function() {
            const expanded = !bulkArea.classList.contains('hidden');
            bulkArea.classList.toggle('hidden', expanded);
            this.setAttribute('aria-expanded', String(!expanded));
            this.innerHTML = expanded
                ? '<span><i class="fa-solid fa-layer-group"></i> Need to shorten multiple links?</span><span class="bulk-toggle-label">Open bulk tools <i class="fa-solid fa-chevron-down"></i></span>'
                : '<span><i class="fa-solid fa-xmark"></i> Hide bulk tools</span><span class="bulk-toggle-label">Close <i class="fa-solid fa-chevron-up"></i></span>';
        });
    }
    
    if (pageParams.get('tool') === 'bulk' && bulkToggleBtn && bulkArea) bulkToggleBtn.click();

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
        
        if (expiresIn === 'custom' && (!expiresAtInput || !expiresAtInput.value || new Date(expiresAtInput.value).getTime() <= Date.now())) {
            showToast('Choose an expiration date and time in the future', 'error');
            if (expiresAtInput) expiresAtInput.focus();
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
            if (expiresIn === 'custom') payload.expires_at = new Date(expiresAtInput.value).toISOString();
            
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
                    statsBtn.style.display = data.has_password ? 'none' : 'inline-flex';
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
            const urls = bulkUrls.value.split(/[\n,]+/).map(function(value) { return value.trim(); }).filter(Boolean);
            if (!urls.length) {
                showToast('Please enter at least one URL', 'error');
                return;
            }
            if (urls.length > 50) {
                showToast('Maximum 50 URLs per batch', 'error');
                return;
            }

            this.disabled = true;
            this.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
            bulkResults.replaceChildren();
            try {
                const response = await fetch('/bulk-shortener', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls: urls })
                });
                const payload = await response.json();
                if (!response.ok) throw new Error(payload.error || 'Bulk shortening failed');

                payload.results.forEach(function(result) {
                    const row = document.createElement('div');
                    row.className = 'bulk-item';
                    const status = document.createElement('span');
                    status.className = 'status-icon ' + (result.success ? 'success' : 'error');
                    status.innerHTML = result.success ? '<i class="fa-solid fa-circle-check"></i>' : '<i class="fa-solid fa-circle-xmark"></i>';
                    const original = document.createElement('span');
                    original.className = 'original';
                    original.textContent = result.original;
                    original.title = result.original;
                    const short = document.createElement('span');
                    short.className = 'short';
                    short.textContent = result.short_url || result.error || 'Failed';
                    short.title = result.short_url || result.error || 'Failed';
                    row.append(status, original, short);
                    if (result.success && result.short_url) {
                        const copy = document.createElement('button');
                        copy.className = 'btn-copy-mini';
                        copy.type = 'button';
                        copy.title = 'Copy short link';
                        copy.setAttribute('aria-label', 'Copy short link');
                        copy.innerHTML = '<i class="fa-regular fa-copy"></i>';
                        copy.addEventListener('click', function() { window.copyText(result.short_url); });
                        row.append(copy);
                    }
                    bulkResults.append(row);
                });
                showToast(payload.succeeded + ' of ' + payload.total + ' links shortened', payload.failed ? 'error' : 'success');
            } catch (error) {
                showToast(error.message || 'Network error. Please try again.', 'error');
            } finally {
                this.disabled = false;
                this.innerHTML = 'Shorten all';
            }
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
            if (!linkRes.ok) throw new Error(linkData.error || 'Preview unavailable');
            
            if (!linkData.original_url) {
                throw new Error('No URL found');
            }
            
            const previewRes = await fetch('/api/preview?url=' + encodeURIComponent(linkData.original_url));
            const previewData = await previewRes.json();
            if (!previewRes.ok) throw new Error(previewData.error || 'Preview unavailable');
            
            previewTitle.textContent = previewData.title || 'No title available';
            previewDesc.textContent = previewData.description || 'No description available';
            if (previewData.image && /^https?:\/\//i.test(previewData.image)) {
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
        if (toastIcon) toastIcon.className = type === 'error' ? 'fa-solid fa-circle-exclamation' : 'fa-solid fa-circle-check';
        toast.classList.toggle('error', type === 'error');
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
    
    // Keep production console output quiet.
});

// FAQ accordion: keep at most one answer open at a time.
document.addEventListener('DOMContentLoaded', () => {
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach((item) => {
    item.addEventListener('toggle', () => {
      if (!item.open) return;
      faqItems.forEach((other) => { if (other !== item) other.open = false; });
    });
  });
});
