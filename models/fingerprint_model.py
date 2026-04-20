import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from datetime import datetime

class FingerprintModel:
    def __init__(self):
        """Initialize fingerprint recognition with SIFT"""
        self.fingerprint_encodings = {}
        
        # Use SIFT (Scale-Invariant Feature Transform)
        # More robust than ORB for fingerprints
        self.sift = cv2.SIFT_create(nfeatures=1000)
        
        # BFMatcher for feature matching
        self.bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        
        # Get paths
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(project_root, 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        self.encodings_file = os.path.join(models_dir, 'fingerprint_encodings.pkl')
        
        self.load_encodings()
        
        print(f"   ✅ Fingerprint model initialized with SIFT")
        print(f"   👆 Registered fingerprints: {len(self.fingerprint_encodings)}")
    
    def load_encodings(self):
        """Load saved fingerprint encodings"""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    self.fingerprint_encodings = pickle.load(f)
                print(f"   ✅ Loaded {len(self.fingerprint_encodings)} fingerprint encodings")
            except Exception as e:
                print(f"   ⚠️ Error loading encodings: {e}")
                self.fingerprint_encodings = {}
        else:
            print(f"   ℹ️ No existing fingerprint encodings")
            self.fingerprint_encodings = {}
    
    def save_encodings(self):
        """Save fingerprint encodings to disk"""
        try:
            os.makedirs(os.path.dirname(self.encodings_file), exist_ok=True)
            
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.fingerprint_encodings, f)
            
            if os.path.exists(self.encodings_file):
                file_size = os.path.getsize(self.encodings_file)
                print(f"   ✅ Saved {len(self.fingerprint_encodings)} fingerprint encodings")
                print(f"   📊 File size: {file_size:,} bytes")
            else:
                print(f"   ❌ Failed to create file")
                
        except Exception as e:
            print(f"   ❌ Error saving encodings: {e}")
            import traceback
            traceback.print_exc()
    
    def preprocess_fingerprint(self, image):
        """Enhanced preprocessing for fingerprint images"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Resize to standard size
            gray = cv2.resize(gray, (300, 400))
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Sharpen image
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            gray = cv2.filter2D(gray, -1, kernel)
            
            # Normalize
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
            
            return gray
        
        except Exception as e:
            print(f"   ❌ Preprocessing error: {e}")
            return None
    
    def extract_fingerprint_features(self, image):
        """Extract fingerprint features using SIFT"""
        try:
            print(f"   🔍 Extracting fingerprint features...")
            
            # Preprocess
            preprocessed = self.preprocess_fingerprint(image)
            
            if preprocessed is None:
                print(f"   ❌ Preprocessing failed")
                return None, None
            
            # Detect keypoints and compute descriptors
            keypoints, descriptors = self.sift.detectAndCompute(preprocessed, None)
            
            if descriptors is None or len(descriptors) == 0:
                print(f"   ⚠️ No fingerprint features detected")
                return None, None
            
            print(f"   ✅ Detected {len(keypoints)} keypoints")
            
            return keypoints, descriptors
        
        except Exception as e:
            print(f"   ❌ Feature extraction error: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def register_fingerprint(self, image, student_id):
        """Register fingerprint for a student"""
        try:
            print(f"\n{'='*60}")
            print(f"👆 FINGERPRINT REGISTRATION")
            print(f"{'='*60}")
            print(f"   Student ID: {student_id}")
            print(f"   Image shape: {image.shape}")
            
            keypoints, descriptors = self.extract_fingerprint_features(image)
            
            if descriptors is None:
                print(f"   ❌ Failed to extract features")
                print(f"{'='*60}\n")
                return False
            
            # Store descriptors and keypoint info
            self.fingerprint_encodings[student_id] = {
                'descriptors': descriptors,
                'num_keypoints': len(keypoints),
                'registered_at': datetime.now().isoformat(),
                'method': 'SIFT'
            }
            
            print(f"   ✅ Features stored in memory")
            print(f"   📋 Total registered: {len(self.fingerprint_encodings)}")
            
            # Save to disk
            print(f"   💾 Saving to disk...")
            self.save_encodings()
            
            print(f"   ✅ Registration complete")
            print(f"{'='*60}\n")
            return True
        
        except Exception as e:
            print(f"   ❌ Registration error: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return False
    
    def authenticate_fingerprint(self, image, threshold=30):
        """Authenticate fingerprint using feature matching"""
        try:
            print(f"\n{'='*60}")
            print(f"👆 FINGERPRINT AUTHENTICATION")
            print(f"{'='*60}")
            print(f"   Method: SIFT feature matching")
            print(f"   Threshold: {threshold} good matches required")
            print(f"   Registered fingerprints: {list(self.fingerprint_encodings.keys())}")
            
            # Extract features from input
            keypoints_input, descriptors_input = self.extract_fingerprint_features(image)
            
            if descriptors_input is None:
                print(f"   ❌ No fingerprint detected")
                print(f"{'='*60}\n")
                return {
                    'match': False,
                    'student_id': None,
                    'confidence': 0,
                    'error': 'No fingerprint detected'
                }
            
            if len(self.fingerprint_encodings) == 0:
                print(f"   ⚠️ No registered fingerprints in database")
                print(f"{'='*60}\n")
                return {
                    'match': False,
                    'student_id': None,
                    'confidence': 0,
                    'error': 'No registered fingerprints'
                }
            
            print(f"\n   📊 Comparing against {len(self.fingerprint_encodings)} registered fingerprint(s)...")
            
            best_match = None
            best_match_count = 0
            all_matches = {}
            
            for student_id, data in self.fingerprint_encodings.items():
                registered_descriptors = data['descriptors']
                
                # Match features
                matches = self.bf.match(descriptors_input, registered_descriptors)
                
                # Sort by distance (lower is better)
                matches = sorted(matches, key=lambda x: x.distance)
                
                # Count good matches (distance < 100)
                good_matches = [m for m in matches if m.distance < 100]
                match_count = len(good_matches)
                
                all_matches[student_id] = match_count
                
                print(f"      📌 {student_id}: {match_count} good matches")
                
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_match = student_id
            
            # Calculate confidence (percentage of matched keypoints)
            if best_match_count > 0:
                confidence = min(best_match_count / len(keypoints_input), 1.0)
            else:
                confidence = 0
            
            print(f"\n   🏆 Best match: {best_match}")
            print(f"   📊 Match count: {best_match_count}")
            print(f"   📊 Confidence: {confidence:.2%}")
            print(f"   🎯 Threshold: {threshold} matches")
            
            # Check if meets threshold
            if best_match_count >= threshold:
                print(f"   ✅ AUTHENTICATED: {best_match}")
                print(f"{'='*60}\n")
                return {
                    'match': True,
                    'student_id': best_match,
                    'confidence': float(confidence),
                    'match_count': best_match_count,
                    'all_matches': all_matches,
                    'error': None
                }
            else:
                print(f"   ❌ REJECTED: {best_match_count} < {threshold} matches")
                print(f"{'='*60}\n")
                return {
                    'match': False,
                    'student_id': best_match,
                    'confidence': float(confidence),
                    'match_count': best_match_count,
                    'all_matches': all_matches,
                    'error': f'Only {best_match_count} matches (need {threshold})'
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