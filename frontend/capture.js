class CameraCapture {
    constructor() {
        this.videoElement = document.getElementById('cameraPreview');
        this.canvasElement = document.getElementById('photoCanvas');
        this.ctx = this.canvasElement.getContext('2d');
        this.stream = null;
        this.isCapturing = false;
        this.cameraSection = document.getElementById('cameraSection');
    }

    // Start camera
    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false
            });
            
            this.videoElement.srcObject = this.stream;
            this.cameraSection.classList.remove('hidden');
            
            // Wait for video to be ready
            await new Promise(resolve => {
                this.videoElement.onloadedmetadata = () => {
                    this.videoElement.play();
                    resolve();
                };
            });
            
            return true;
        } catch (error) {
            console.error('Error accessing camera:', error);
            return false;
        }
    }

    // Capture photo from video stream
    capturePhoto() {
        if (!this.stream) {
            throw new Error('Camera not started');
        }

        // Set canvas dimensions to match video
        this.canvasElement.width = this.videoElement.videoWidth;
        this.canvasElement.height = this.videoElement.videoHeight;
        
        // Draw current video frame to canvas
        this.ctx.save();
        this.ctx.scale(-1, 1); // Mirror the image
        this.ctx.drawImage(
            this.videoElement, 
            -this.canvasElement.width, 
            0, 
            this.canvasElement.width, 
            this.canvasElement.height
        );
        this.ctx.restore();
        
        // Get base64 image data
        const imageData = this.canvasElement.toDataURL('image/jpeg', 0.8);
        return imageData;
    }

    // Stop camera stream
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.videoElement.srcObject = null;
            this.cameraSection.classList.add('hidden');
        }
    }

    // Take multiple photos for better accuracy
    async captureMultiplePhotos(count = 3, delay = 300) {
        const photos = [];
        
        for (let i = 0; i < count; i++) {
            // Add slight delay between captures
            if (i > 0) {
                await this.sleep(delay);
            }
            
            // Add visual feedback
            this.showCaptureFlash();
            
            // Capture photo
            const photo = this.capturePhoto();
            photos.push(photo);
        }
        
        return photos;
    }

    // Visual feedback for photo capture
    showCaptureFlash() {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: white;
            opacity: 0.7;
            z-index: 9999;
            pointer-events: none;
            animation: flash 0.2s;
        `;
        
        document.body.appendChild(overlay);
        
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 200);
    }

    // Helper function
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Check if camera is available
    static async isCameraAvailable() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return false;
        }
        
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.some(device => device.kind === 'videoinput');
        } catch (error) {
            return false;
        }
    }
}

// Global camera instance
window.camera = new CameraCapture();