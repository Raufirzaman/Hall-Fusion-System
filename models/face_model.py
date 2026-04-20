import cv2
import numpy as np
import pickle
import os
from datetime import datetime

class FaceModel:
    def __init__(self):
        """Initialize face recognition model"""
        self.use_insightface = False
        self.face_encodings = {}
        
        # Get absolute path to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(project_root, 'models')
        
        # Create models directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        
        self.encodings_file = os.path.join(models_dir, 'face_encodings.pkl')
        
        # Try to use InsightFace (ArcFace) - Best accuracy
        try:
            from insightface.app import FaceAnalysis
            
            print("   🔄 Loading InsightFace (ArcFace) model...")
            self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            self.use_insightface = True
            print("   ✅ InsightFace loaded successfully (99.8% accuracy)")
            print("   📊 Model: ArcFace with RetinaFace detector")
            
        except ImportError:
            print("   ⚠️ InsightFace not installed, trying face_recognition...")
            
            # Fallback to face_recognition (dlib)
            try:
                import face_recognition
                self.face_recognition = face_recognition
                self.use_face_recognition = True
                print("   ✅ face_recognition loaded (99.4% accuracy)")
                print("   📊 Model: dlib ResNet-34")
                
            except ImportError:
                print("   ⚠️ face_recognition not installed, using OpenCV fallback")
                print("   ⚠️ WARNING: Basic accuracy only (~60-70%)")
                print("   💡 Install InsightFace for production use:")
                print("      pip install insightface onnxruntime")
                
                # Use OpenCV Haar Cascades as last resort
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                self.use_face_recognition = False
        
        # Load existing encodings
        self.load_encodings()
        
        print(f"   💾 Encodings file: {self.encodings_file}")
        print(f"   👥 Registered faces: {len(self.face_encodings)}")
    
    def load_encodings(self):
        """Load saved face encodings"""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    self.face_encodings = pickle.load(f)
                print(f"   ✅ Loaded {len(self.face_encodings)} face encodings")
                for student_id in self.face_encodings.keys():
                    print(f"      - {student_id}")
            except Exception as e:
                print(f"   ⚠️ Error loading encodings: {e}")
                self.face_encodings = {}
        else:
            print(f"   ℹ️ No existing encodings found (new system)")
            self.face_encodings = {}
    
    def save_encodings(self):
        """Save face encodings to disk"""
        try:
            os.makedirs(os.path.dirname(self.encodings_file), exist_ok=True)
            
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.face_encodings, f)
            
            if os.path.exists(self.encodings_file):
                file_size = os.path.getsize(self.encodings_file)
                print(f"   ✅ Saved {len(self.face_encodings)} encodings")
                print(f"   📊 File size: {file_size:,} bytes")
            else:
                print(f"   ❌ Failed to create file")
                
        except Exception as e:
            print(f"   ❌ Error saving encodings: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_face_encoding(self, image):
        """Extract face encoding and save location"""
        try:
            if self.use_insightface:
                faces = self.app.get(image)
                
                if len(faces) == 0:
                    self.last_face_location = None
                    return None
                
                largest_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                
                # Save face location
                self.last_face_location = {
                    'x': int(largest_face.bbox[0]),
                    'y': int(largest_face.bbox[1]),
                    'width': int(largest_face.bbox[2] - largest_face.bbox[0]),
                    'height': int(largest_face.bbox[3] - largest_face.bbox[1])
                }
                
                # Get 512D embedding
                embedding = largest_face.embedding
                
                # Normalize embedding
                embedding = embedding / np.linalg.norm(embedding)
                
                bbox = largest_face.bbox
                print(f"   ✅ Face detected: position ({int(bbox[0])}, {int(bbox[1])}), "
                      f"size {int(bbox[2]-bbox[0])}x{int(bbox[3]-bbox[1])}")
                print(f"   📊 ArcFace embedding: {embedding.shape}, norm: {np.linalg.norm(embedding):.4f}")
                
                return embedding
            
            elif hasattr(self, 'use_face_recognition') and self.use_face_recognition:
                return self._extract_face_recognition(image)
            
            else:
                return self._extract_opencv(image)
        
        except Exception as e:
            print(f"   ❌ Error extracting face: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_insightface(self, image):
        """Extract 512D embedding using InsightFace (ArcFace)"""
        try:
            # Detect faces and get embeddings
            faces = self.app.get(image)
            
            if len(faces) == 0:
                print("   ⚠️ No face detected")
                return None
            
            # Get the largest face
            largest_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            
            # Get 512D embedding
            embedding = largest_face.embedding
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            bbox = largest_face.bbox
            print(f"   ✅ Face detected: position ({int(bbox[0])}, {int(bbox[1])}), "
                  f"size {int(bbox[2]-bbox[0])}x{int(bbox[3]-bbox[1])}")
            print(f"   📊 ArcFace embedding: {embedding.shape}, norm: {np.linalg.norm(embedding):.4f}")
            
            return embedding
        
        except Exception as e:
            print(f"   ❌ InsightFace error: {e}")
            return None
    
    def _extract_face_recognition(self, image):
        """Extract 128D encoding using face_recognition (dlib)"""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face encodings
            encodings = self.face_recognition.face_encodings(rgb_image)
            
            if len(encodings) == 0:
                print("   ⚠️ No face detected")
                return None
            
            print(f"   ✅ Face detected (dlib)")
            print(f"   📊 dlib encoding: {encodings[0].shape}")
            
            return encodings[0]
        
        except Exception as e:
            print(f"   ❌ face_recognition error: {e}")
            return None
    
    def _extract_opencv(self, image):
        """Extract encoding using OpenCV Haar Cascades (fallback)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(50, 50)
            )
            
            if len(faces) == 0:
                print("   ⚠️ No face detected")
                return None
            
            # Get largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            print(f"   ✅ Face detected: position ({x}, {y}), size {w}x{h}")
            
            # Extract face ROI with padding
            padding = int(h * 0.2)
            y1 = max(0, y - padding)
            y2 = min(gray.shape[0], y + h + padding)
            x1 = max(0, x - padding)
            x2 = min(gray.shape[1], x + w + padding)
            
            face_roi = gray[y1:y2, x1:x2]
            face_roi = cv2.resize(face_roi, (128, 128))
            face_roi = cv2.GaussianBlur(face_roi, (5, 5), 0)
            
            # Flatten
            encoding = face_roi.flatten().astype(np.float32) / 255.0
            
            print(f"   📊 OpenCV encoding: {encoding.shape}")
            
            return encoding
        
        except Exception as e:
            print(f"   ❌ OpenCV error: {e}")
            return None
    
    def register_face(self, image, student_id, mode='single'):
        """Register face for a student"""
        try:
            print(f"\n{'='*60}")
            print(f"📝 FACE REGISTRATION")
            print(f"{'='*60}")
            print(f"   Student ID: {student_id}")
            print(f"   Image shape: {image.shape}")
            print(f"   Model: {'InsightFace (ArcFace)' if self.use_insightface else 'OpenCV (Haar)'}")
            
            encoding = self.extract_face_encoding(image)
            
            if encoding is None:
                print(f"   ❌ Failed to extract face encoding")
                print(f"{'='*60}\n")
                return False
            
            # Store encoding with metadata
            self.face_encodings[student_id] = {
                'encoding': encoding,
                'registered_at': datetime.now().isoformat(),
                'model': 'insightface' if self.use_insightface else 'opencv',
                'encoding_shape': encoding.shape,
                'encoding_dtype': str(encoding.dtype)
            }
            
            print(f"   ✅ Encoding stored in memory")
            print(f"   📋 Total registered: {len(self.face_encodings)}")
            
            # Save to disk
            print(f"   💾 Saving to disk...")
            self.save_encodings()
            
            # Verify
            if os.path.exists(self.encodings_file):
                print(f"   ✅ Registration complete")
            else:
                print(f"   ❌ File not created")
                print(f"{'='*60}\n")
                return False
            
            print(f"{'='*60}\n")
            return True
        
        except Exception as e:
            print(f"   ❌ Registration error: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return False
    
    def authenticate_face(self, image, threshold=None):
        """Authenticate face against registered encodings"""
        try:
            print(f"\n{'='*60}")
            print(f"🔐 FACE AUTHENTICATION")
            print(f"{'='*60}")
            
            # Set default threshold based on model
            if threshold is None:
                if self.use_insightface:
                    threshold = 0.35  # Cosine similarity for ArcFace
                elif hasattr(self, 'use_face_recognition') and self.use_face_recognition:
                    threshold = 0.6   # Euclidean distance for dlib
                else:
                    threshold = 0.45  # Cosine similarity for OpenCV
            
            print(f"   Model: {'InsightFace (ArcFace)' if self.use_insightface else 'OpenCV (Haar)'}")
            print(f"   Threshold: {threshold}")
            print(f"   Registered faces: {list(self.face_encodings.keys())}")
            
            # Extract encoding
            input_encoding = self.extract_face_encoding(image)
            
            if input_encoding is None:
                print(f"   ❌ No face detected")
                print(f"{'='*60}\n")
                return {
                    'match': False,
                    'student_id': None,
                    'confidence': 0,
                    'error': 'No face detected in image'
                }
            
            if len(self.face_encodings) == 0:
                print(f"   ⚠️ No registered faces in database")
                print(f"   File: {self.encodings_file}")
                print(f"   Exists: {os.path.exists(self.encodings_file)}")
                print(f"{'='*60}\n")
                return {
                    'match': False,
                    'student_id': None,
                    'confidence': 0,
                    'error': 'No registered faces. Please register first.'
                }
            
            print(f"\n   📊 Comparing against {len(self.face_encodings)} registered face(s)...")
            
            best_match = None
            best_score = 0 if self.use_insightface else float('inf')
            all_scores = {}
            
            for student_id, data in self.face_encodings.items():
                registered_encoding = data['encoding']
                
                if self.use_insightface:
                    # Use cosine similarity for InsightFace
                    similarity = np.dot(input_encoding, registered_encoding)
                    score = similarity
                    all_scores[student_id] = float(similarity)
                    
                    print(f"      📌 {student_id}: similarity = {similarity:.4f} ({similarity*100:.2f}%)")
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = student_id
                
                else:
                    # Use Euclidean distance for dlib/OpenCV
                    distance = np.linalg.norm(input_encoding - registered_encoding)
                    
                    # Convert distance to similarity for display
                    similarity = 1 / (1 + distance)
                    score = distance
                    all_scores[student_id] = float(similarity)
                    
                    print(f"      📌 {student_id}: distance = {distance:.4f}, similarity = {similarity:.4f}")
                    
                    if distance < best_score:
                        best_score = distance
                        best_match = student_id
            
            # Check threshold
            if self.use_insightface:
                # For cosine similarity, higher is better
                is_match = best_score >= threshold
                confidence = float(best_score)
                print(f"\n   🏆 Best match: {best_match}")
                print(f"   📊 Similarity: {best_score:.4f} ({best_score*100:.2f}%)")
                print(f"   🎯 Threshold: {threshold:.4f} ({threshold*100:.2f}%)")
            else:
                # For distance, lower is better
                is_match = best_score <= threshold
                confidence = 1 / (1 + best_score)
                print(f"\n   🏆 Best match: {best_match}")
                print(f"   📊 Distance: {best_score:.4f}")
                print(f"   📊 Confidence: {confidence:.4f} ({confidence*100:.2f}%)")
                print(f"   🎯 Threshold: {threshold:.4f}")
            
            if is_match:
                print(f"   ✅ AUTHENTICATED: {best_match}")
                print(f"{'='*60}\n")
                return {
                    'match': True,
                    'student_id': best_match,
                    'confidence': confidence,
                    'all_similarities': all_scores,
                    'error': None
                }
            else:
                print(f"   ❌ REJECTED: Below threshold")
                print(f"{'='*60}\n")
                return {
                    'match': False,
                    'student_id': best_match,
                    'confidence': confidence,
                    'all_similarities': all_scores,
                    'error': f'Confidence {confidence:.2%} below threshold {threshold:.2%}'
                }
        
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return {
                'match': False,
                'student_id': None,
                'confidence': 0,
                'error': str(e)
            }