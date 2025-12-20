// capture.js - Enhanced with facial recognition on failed attempts

class SecurityCamera {
    constructor() {
        this.videoElement = null;
        this.canvasElement = null;
        this.ctx = null;
        this.stream = null;
        this.isCameraActive = false;
        this.failedAttempts = new Map(); // email -> count
        this.maxAttemptsBeforeCapture = 3;
        this.API_BASE_URL = 'http://localhost:5000';
    }

    initializeElements() {
        // Create camera elements if they don't exist
        if (!document.getElementById('cameraPreview')) {
            this.createCameraElements();
        }
        this.videoElement = document.getElementById('cameraPreview');
        this.canvasElement = document.getElementById('photoCanvas');
        this.ctx = this.canvasElement.getContext('2d');
    }

    createCameraElements() {
        // Create hidden camera elements
        const video = document.createElement('video');
        video.id = 'cameraPreview';
        video.autoplay = true;
        video.playsinline = true;
        video.style.display = 'none';

        const canvas = document.createElement('canvas');
        canvas.id = 'photoCanvas';
        canvas.style.display = 'none';

        document.body.appendChild(video);
        document.body.appendChild(canvas);
    }

    async startCamera() {
        try {
            this.initializeElements();
            
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false
            });
            
            this.videoElement.srcObject = this.stream;
            this.isCameraActive = true;
            
            // Wait for video to be ready
            await new Promise(resolve => {
                this.videoElement.onloadedmetadata = () => {
                    this.videoElement.play();
                    resolve();
                };
            });
            
            return true;
        } catch (error) {
            console.error('Camera error:', error);
            return false;
        }
    }

    capturePhoto() {
        if (!this.isCameraActive || !this.stream) {
            throw new Error('Camera not started');
        }

        // Set canvas dimensions
        this.canvasElement.width = this.videoElement.videoWidth;
        this.canvasElement.height = this.videoElement.videoHeight;
        
        // Draw video frame to canvas (mirrored for selfie view)
        this.ctx.save();
        this.ctx.scale(-1, 1);
        this.ctx.drawImage(
            this.videoElement, 
            -this.canvasElement.width, 
            0, 
            this.canvasElement.width, 
            this.canvasElement.height
        );
        this.ctx.restore();
        
        // Get base64 image
        return this.canvasElement.toDataURL('image/jpeg', 0.8);
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.isCameraActive = false;
            if (this.videoElement) {
                this.videoElement.srcObject = null;
            }
        }
    }

    async captureFaceForVerification(email) {
        try {
            // Start camera
            const started = await this.startCamera();
            if (!started) {
                throw new Error('Failed to start camera');
            }

            // Wait briefly for focus
            await new Promise(resolve => setTimeout(resolve, 500));

            // Capture photo
            const photo = this.capturePhoto();
            
            // Stop camera
            this.stopCamera();
            
            // Update failed attempts counter
            this.incrementFailedAttempt(email);
            
            return {
                success: true,
                image: photo,
                email: email,
                attemptCount: this.getFailedAttempts(email)
            };
        } catch (error) {
            console.error('Face capture error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    incrementFailedAttempt(email) {
        const current = this.failedAttempts.get(email) || 0;
        this.failedAttempts.set(email, current + 1);
    }

    getFailedAttempts(email) {
        return this.failedAttempts.get(email) || 0;
    }

    resetFailedAttempts(email) {
        this.failedAttempts.delete(email);
    }

    async sendToBackendForVerification(email, faceImage, attemptData) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/verify-face`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    face_image: faceImage,
                    attempt_number: attemptData.attemptCount,
                    timestamp: new Date().toISOString()
                })
            });

            return await response.json();
        } catch (error) {
            console.error('Backend verification error:', error);
            return {
                success: false,
                error: 'Failed to verify face'
            };
        }
    }

    async checkAndCaptureFace(email, credentialsCorrect) {
        // Reset counter if credentials are correct
        if (credentialsCorrect) {
            this.resetFailedAttempts(email);
            return null;
        }

        // Increment failed attempts
        this.incrementFailedAttempt(email);
        const attemptCount = this.getFailedAttempts(email);

        // Capture face on 3rd failed attempt
        if (attemptCount === this.maxAttemptsBeforeCapture) {
            console.log(`Capturing face for email: ${email} (Attempt ${attemptCount})`);
            return await this.captureFaceForVerification(email);
        }

        // Capture face every attempt after 3rd
        if (attemptCount > this.maxAttemptsBeforeCapture) {
            console.log(`Capturing face for email: ${email} (Attempt ${attemptCount})`);
            return await this.captureFaceForVerification(email);
        }

        return null;
    }
}

// Global security camera instance
window.securityCamera = new SecurityCamera();