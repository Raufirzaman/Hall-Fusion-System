import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

class FirebaseModel:
    def __init__(self):
        """Initialize Firebase connection"""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            print("✅ Firebase already initialized (using existing connection)")
        except ValueError:
            # Initialize Firebase only if not already done
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://bauet-hms-63f5b-default-rtdb.firebaseio.com/'
            })
            print("✅ Firebase Realtime Database connected")
        
        self.db = db
    
    def get_student(self, student_id):
        """
        Get student data from Realtime Database
        Your data structure: /users/{id}/
        """
        try:
            ref = self.db.reference('users')
            all_users = ref.get()
            
            if not all_users:
                return {'matched': False, 'reason': 'No users in database'}
            
            # Search for student by id field
            for user_key, user_data in all_users.items():
                if user_data.get('id') == student_id:
                    return {
                        'matched': True,
                        'user_key': user_key,  # Store this for updates
                        'data': {
                            'student_id': user_data.get('id'),
                            'name': user_data.get('name'),
                            'email': user_data.get('email'),
                            'room_number': user_data.get('room'),
                            'department': user_data.get('dept_name'),
                            'batch': user_data.get('batch'),
                            'address': user_data.get('address'),
                            'phone': user_data.get('phone_number'),
                            'father_name': user_data.get('father_name'),
                            'mother_name': user_data.get('mother_name'),
                            'dob': user_data.get('dob'),
                            'role': user_data.get('role', 'member'),
                            # Biometric paths (if already registered)
                            'face_image_path': user_data.get('biometrics', {}).get('face_image_path'),
                            'fingerprint_image_path': user_data.get('biometrics', {}).get('fingerprint_image_path')
                        }
                    }
            
            return {'matched': False, 'reason': f'Student ID {student_id} not found'}
            
        except Exception as e:
            print(f"❌ Firebase error: {str(e)}")
            return {'matched': False, 'reason': f'Error: {str(e)}'}
    
    def save_biometric_paths(self, student_id, face_image_path, fingerprint_image_path):
        """
        Save only file paths to Firebase (not the actual images)
        
        Args:
            student_id: Student ID
            face_image_path: Local path to face image
            fingerprint_image_path: Local path to fingerprint image
        
        Returns:
            success: Boolean
        """
        try:
            ref = self.db.reference('users')
            all_users = ref.get()
            
            if not all_users:
                return False
            
            # Find the user
            for user_key, user_data in all_users.items():
                if user_data.get('id') == student_id:
                    # Store paths under biometrics node
                    biometric_ref = ref.child(user_key).child('biometrics')
                    biometric_ref.set({
                        'face_image_path': face_image_path,
                        'fingerprint_image_path': fingerprint_image_path,
                        'registered_at': datetime.now().isoformat(),
                        'status': 'active'
                    })
                    
                    print(f"✅ Saved biometric paths in Firebase for: {student_id}")
                    print(f"   Face path: {face_image_path}")
                    print(f"   Fingerprint path: {fingerprint_image_path}")
                    return True
            
            print(f"❌ Student {student_id} not found in database")
            return False
            
        except Exception as e:
            print(f"❌ Error saving paths: {str(e)}")
            return False
    
    def get_biometric_paths(self, student_id):
        """
        Get stored biometric image paths
        
        Returns:
            dict with face_path and fingerprint_path
        """
        try:
            ref = self.db.reference('users')
            all_users = ref.get()
            
            if not all_users:
                return None
            
            for user_key, user_data in all_users.items():
                if user_data.get('id') == student_id:
                    biometrics = user_data.get('biometrics', {})
                    return {
                        'face_path': biometrics.get('face_image_path'),
                        'fingerprint_path': biometrics.get('fingerprint_image_path'),
                        'registered_at': biometrics.get('registered_at'),
                        'status': biometrics.get('status')
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting paths: {str(e)}")
            return None
    
    def log_authentication(self, student_id, result, method='manual'):
        """
        Log authentication attempt
        Stores in: /authentication_logs/
        """
        try:
            log_ref = self.db.reference('authentication_logs')
            
            log_data = {
                'student_id': student_id,
                'timestamp': datetime.now().isoformat(),
                'verified': result.get('verified', False),
                'score': result.get('score', 0.0),
                'method': method,
                'face_matched': result.get('face_matched', False),
                'fingerprint_matched': result.get('fingerprint_matched', False),
                'firebase_matched': result.get('firebase_matched', False),
                'matched_count': result.get('matched_count', 0)
            }
            
            log_ref.push(log_data)
            print(f"✅ Logged authentication attempt")
            
        except Exception as e:
            print(f"⚠️ Logging error: {str(e)}")
    
    def get_authentication_logs(self, student_id=None, limit=50):
        """Get authentication logs"""
        try:
            log_ref = self.db.reference('authentication_logs')
            logs = log_ref.get()
            
            if not logs:
                return []
            
            # Convert to list
            log_list = []
            for log_key, log_data in logs.items():
                if student_id is None or log_data.get('student_id') == student_id:
                    log_data['log_id'] = log_key
                    log_list.append(log_data)
            
            # Sort by timestamp (most recent first)
            log_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return log_list[:limit]
            
        except Exception as e:
            print(f"❌ Error getting logs: {str(e)}")
            return []
    
    def get_all_students(self):
   
        try:
            ref = self.db.reference('users')
            all_users = ref.get()
        
            if not all_users:
                return []
        
            students = []
            for user_key, user_data in all_users.items():
                biometrics = user_data.get('biometrics', {})
            
                students.append({
                    'id': str(user_data.get('id', 'N/A')),  # Convert to string
                    'name': user_data.get('name', 'Unknown'),
                    'room': user_data.get('room') or 'N/A',  # Handle None
                    'department': user_data.get('dept_name', 'N/A'),
                    'role': user_data.get('role', 'member'),
                    'has_biometrics': biometrics.get('status') == 'active'
                })
        
            return students
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return []