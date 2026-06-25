document.addEventListener('DOMContentLoaded', () => {
    const shortenBtn = document.getElementById('shortenBtn');
    const longUrlInput = document.getElementById('longUrl');
    const resultSection = document.getElementById('resultSection');
    const shortenedUrlInput = document.getElementById('shortenedUrl');
    const copyBtn = document.getElementById('copyBtn');
    const errorMsg = document.getElementById('errorMessage');
    const qrContainer = document.getElementById('qrcode');

    shortenBtn.addEventListener('click', async () => {
        const url = longUrlInput.value;
        errorMsg.innerText = "";

        if (!url) {
            errorMsg.innerText = "Please enter a URL";
            return;
        }

        try {
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                // Update UI
                shortenedUrlInput.value = data.short_url;
                resultSection.classList.remove('hidden');
                
                // Generate QR Code
                qrContainer.innerHTML = ""; // Clear old QR
                new QRCode(qrContainer, {
                    text: data.short_url,
                    width: 128,
                    height: 128,
                    colorDark : "#000000",
                    colorLight : "#ffffff",
                    correctLevel : QRCode.CorrectLevel.H
                });

                // Scroll to result
                resultSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                errorMsg.innerText = data.error || "An error occurred";
            }
        } catch (err) {
            errorMsg.innerText = "Server connection failed";
        }
    });

    // Copy to clipboard functionality
    copyBtn.addEventListener('click', () => {
        shortenedUrlInput.select();
        shortenedUrlInput.setSelectionRange(0, 99999); // For mobile
        navigator.clipboard.writeText(shortenedUrlInput.value);

        const copyIcon = document.getElementById('copyIcon');
        copyIcon.innerText = "Copied!";
        copyBtn.style.background = "rgba(0, 210, 255, 0.2)";
        
        setTimeout(() => {
            copyIcon.innerText = "Copy";
            copyBtn.style.background = "transparent";
        }, 2000);
    });
});