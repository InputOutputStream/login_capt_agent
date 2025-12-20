import cv2
import numpy as np
import pickle
import base64
from io import BytesIO
from PIL import Image
import face_recognition  # We'll use face_recognition library directly
from config import Config

class FaceRecognition:
    def __init__(self):
        self.known_faces = []
        self.known_names = []
        # We're only using face_recognition library, not MediaPipe
    
    def base64_to_image(self, base64_string):
        """Convert base64 string to OpenCV image"""
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img_rgb
    
    def image_to_base64(self, image):
        """Convert OpenCV image to base64 string"""
        _, buffer = cv2.imencode('.jpg', image)
        base64_string = base64.b64encode(buffer).decode('utf-8')
        return base64_string
    
    def detect_faces(self, image):
        """Detect faces using face_recognition library"""
        try:
            # Find all face locations and encodings in the image
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            faces = []
            for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                face = image[top:bottom, left:right]
                
                faces.append({
                    'bbox': (left, top, right-left, bottom-top),
                    'face': face,
                    'embedding': encoding
                })
            
            return faces
        except Exception as e:
            print(f"Face detection error: {e}")
            return []
    
    def extract_face_embedding(self, image):
        """Extract face embedding from image"""
        faces = self.detect_faces(image)
        
        if faces:
            # Return the first face found
            return faces[0]['embedding']
        
        return None
    
    def compare_faces(self, embedding1, embedding2, threshold=None):
        """Compare two face embeddings"""
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        if threshold is None:
            threshold = Config.FACE_MATCH_THRESHOLD
        
        # Calculate Euclidean distance
        distance = np.linalg.norm(embedding1 - embedding2)
        similarity = 1.0 - min(distance / 0.6, 1.0)  # Normalize to [0, 1]
        
        return similarity
    
    def verify_user(self, captured_images, stored_embedding, threshold=None):
        """Verify user by comparing captured images with stored embedding"""
        if stored_embedding is None:
            return False, 0.0
        
        best_similarity = 0.0
        
        for img_base64 in captured_images:
            # Convert base64 to image
            image = self.base64_to_image(img_base64)
            
            # Extract face embedding
            embedding = self.extract_face_embedding(image)
            
            if embedding is not None:
                # Compare with stored embedding
                similarity = self.compare_faces(embedding, stored_embedding, threshold)
                best_similarity = max(best_similarity, similarity)
        
        # Check if similarity meets threshold
        threshold = threshold or Config.FACE_MATCH_THRESHOLD
        verified = best_similarity >= threshold
        
        return verified, best_similarity
    
    def save_face_encoding(self, embedding, user_id):
        """Save face encoding to file"""
        import os
        os.makedirs(Config.KNOWN_FACES_DIR, exist_ok=True)
        filename = f"{Config.KNOWN_FACES_DIR}/user_{user_id}.pkl"
        
        with open(filename, 'wb') as f:
            pickle.dump(embedding, f)
    
    def load_face_encoding(self, user_id):
        """Load face encoding from file"""
        filename = f"{Config.KNOWN_FACES_DIR}/user_{user_id}.pkl"
        
        try:
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return None
    
    def save_captured_face(self, image, filename_prefix):
        """Save captured face image for analysis"""
        import os
        from datetime import datetime
        os.makedirs(Config.CAPTURED_FACES_DIR, exist_ok=True)
        filename = f"{Config.CAPTURED_FACES_DIR}/{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Convert RGB to BGR for OpenCV save
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, image_bgr)
        
        return filename