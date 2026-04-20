import os
import cv2
from datetime import datetime

class StorageManager:
    """
    Manages local file storage for biometric images
    Only stores file paths in Firebase, actual images stay on PC
    """
    
    def __init__(self, base_path='storage'):
        """Initialize storage manager"""
        self.base_path = os.path.abspath(base_path)
        self.faces_path = os.path.join(self.base_path, 'faces')
        self.fingerprints_path = os.path.join(self.base_path, 'fingerprints')
        self.monitoring_path = os.path.join(self.base_path, 'monitoring')
        
        # Create directories
        os.makedirs(self.faces_path, exist_ok=True)
        os.makedirs(self.fingerprints_path, exist_ok=True)
        os.makedirs(self.monitoring_path, exist_ok=True)
        
        print(f"✅ Storage initialized: {self.base_path}")
    
    def save_face_image(self, image, student_id):
        """Save face image to local storage"""
        try:
            # Create student folder
            student_folder = os.path.join(self.faces_path, student_id)
            os.makedirs(student_folder, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'face_{timestamp}.jpg'
            filepath = os.path.join(student_folder, filename)
            
            # Save image
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # Return relative path from project root
            relative_path = os.path.relpath(filepath, start=os.getcwd())
            
            print(f"✅ Face saved: {relative_path}")
            return relative_path
            
        except Exception as e:
            print(f"❌ Error saving face image: {e}")
            raise
    
    def save_fingerprint_image(self, image, student_id):
        """Save fingerprint image to local storage"""
        try:
            # Create student folder
            student_folder = os.path.join(self.fingerprints_path, student_id)
            os.makedirs(student_folder, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'fingerprint_{timestamp}.jpg'
            filepath = os.path.join(student_folder, filename)
            
            # Save image
            cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # Return relative path
            relative_path = os.path.relpath(filepath, start=os.getcwd())
            
            print(f"✅ Fingerprint saved: {relative_path}")
            return relative_path
            
        except Exception as e:
            print(f"❌ Error saving fingerprint image: {e}")
            raise
    
    def save_monitoring_frame(self, frame, location, detection_info):
        """Save monitoring frame with detection"""
        try:
            # Create location folder
            location_folder = os.path.join(self.monitoring_path, location.replace(' ', '_'))
            os.makedirs(location_folder, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            student_id = detection_info.get('student_id', 'unknown')
            filename = f'{student_id}_{timestamp}.jpg'
            filepath = os.path.join(location_folder, filename)
            
            # Save frame
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Return relative path
            relative_path = os.path.relpath(filepath, start=os.getcwd())
            
            return relative_path
            
        except Exception as e:
            print(f"❌ Error saving monitoring frame: {e}")
            return None
    
    def get_face_image_path(self, student_id):
        """Get path to student's face image"""
        student_folder = os.path.join(self.faces_path, student_id)
        
        if not os.path.exists(student_folder):
            return None
        
        # Get latest face image
        images = [f for f in os.listdir(student_folder) if f.endswith('.jpg')]
        
        if not images:
            return None
        
        # Sort by filename (includes timestamp)
        images.sort(reverse=True)
        latest_image = os.path.join(student_folder, images[0])
        
        return os.path.relpath(latest_image, start=os.getcwd())
    
    def get_fingerprint_image_path(self, student_id):
        """Get path to student's fingerprint image"""
        student_folder = os.path.join(self.fingerprints_path, student_id)
        
        if not os.path.exists(student_folder):
            return None
        
        # Get latest fingerprint image
        images = [f for f in os.listdir(student_folder) if f.endswith('.jpg')]
        
        if not images:
            return None
        
        images.sort(reverse=True)
        latest_image = os.path.join(student_folder, images[0])
        
        return os.path.relpath(latest_image, start=os.getcwd())