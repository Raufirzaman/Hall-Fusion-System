import firebase_admin
from firebase_admin import credentials, db
import os
from datetime import datetime

class FirebaseManager:
    """
    Single Firebase manager for the entire application
    Handles all database operations
    """
    
    def __init__(self):
        """Initialize Firebase connection"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            print("✅ Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'firebase-credentials.json')
            
            if not os.path.exists(cred_path):
                # Try serviceAccountKey.json as fallback
                cred_path = os.path.join(os.path.dirname(__file__), '..', 'serviceAccountKey.json')
            
            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"Firebase credentials not found. Please place serviceAccountKey.json in project root"
                )
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://bauet-hms-63f5b-default-rtdb.firebaseio.com/'
            })
            print("✅ Firebase initialized successfully")
        
        # Database references
        self.db = db
        self.students_ref = db.reference('users')  # Changed to 'users' based on your structure
        self.violations_ref = db.reference('violations')
        self.monitoring_ref = db.reference('monitoring')
        self.authentication_ref = db.reference('authentication_logs')
    
    def get_student(self, student_id):
        """Get student data by ID from /users/{id}/"""
        try:
            all_users = self.students_ref.get()
            
            if not all_users:
                return None
            
            # Search for student by id field
            for user_key, user_data in all_users.items():
                if str(user_data.get('id')) == str(student_id):
                    return {
                        'id': user_data.get('id'),
                        'name': user_data.get('name'),
                        'email': user_data.get('email'),
                        'room': user_data.get('room'),
                        'department': user_data.get('dept_name'),
                        'batch': user_data.get('batch'),
                        'phone': user_data.get('phone_number'),
                        'role': user_data.get('role', 'member'),
                        'has_face': bool(user_data.get('biometrics', {}).get('face_image_path')),
                        'has_fingerprint': bool(user_data.get('biometrics', {}).get('fingerprint_image_path')),
                        'has_biometrics': user_data.get('biometrics', {}).get('status') == 'active',
                        '_user_key': user_key  # Internal use
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting student {student_id}: {e}")
            return None
    
    def update_student(self, student_id, data):
        """Update student data"""
        try:
            all_users = self.students_ref.get()
            
            if not all_users:
                return False
            
            # Find the user
            for user_key, user_data in all_users.items():
                if str(user_data.get('id')) == str(student_id):
                    self.students_ref.child(user_key).update(data)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error updating student {student_id}: {e}")
            return False
    
    def save_biometric_paths(self, student_id, face_image_path=None, fingerprint_image_path=None):
        """Save biometric image paths to Firebase"""
        try:
            all_users = self.students_ref.get()
            
            if not all_users:
                return False
            
            # Find the user
            for user_key, user_data in all_users.items():
                if str(user_data.get('id')) == str(student_id):
                    # Get existing biometrics data
                    existing_bio = user_data.get('biometrics', {})
                    
                    # Update biometrics node
                    biometric_data = {
                        'registered_at': existing_bio.get('registered_at', datetime.now().isoformat()),
                        'last_updated': datetime.now().isoformat(),
                        'status': 'active'
                    }
                    
                    if face_image_path:
                        biometric_data['face_image_path'] = face_image_path
                    elif existing_bio.get('face_image_path'):
                        biometric_data['face_image_path'] = existing_bio['face_image_path']
                    
                    if fingerprint_image_path:
                        biometric_data['fingerprint_image_path'] = fingerprint_image_path
                    elif existing_bio.get('fingerprint_image_path'):
                        biometric_data['fingerprint_image_path'] = existing_bio['fingerprint_image_path']
                    
                    biometric_ref = self.students_ref.child(user_key).child('biometrics')
                    biometric_ref.set(biometric_data)
                    
                    print(f"✅ Saved biometric paths in Firebase for: {student_id}")
                    return True
            
            print(f"❌ Student {student_id} not found in database")
            return False
            
        except Exception as e:
            print(f"❌ Error saving paths: {str(e)}")
            return False
    
    def get_biometric_paths(self, student_id):
        """Get stored biometric image paths"""
        try:
            all_users = self.students_ref.get()
            
            if not all_users:
                return None
            
            for user_key, user_data in all_users.items():
                if str(user_data.get('id')) == str(student_id):
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
    
    def add_violation(self, violation_data):
        """Add violation record"""
        try:
            new_ref = self.violations_ref.push()
            violation_data['id'] = new_ref.key
            violation_data['timestamp'] = datetime.now().isoformat()
            new_ref.set(violation_data)
            return violation_data['id']
        except Exception as e:
            print(f"Error adding violation: {e}")
            return None
    
    def get_all_students(self):
        """Get all students from /users/"""
        try:
            all_users = self.students_ref.get()
            
            if not all_users:
                return []
            
            students = []
            for user_key, user_data in all_users.items():
                biometrics = user_data.get('biometrics', {})
                
                students.append({
                    'id': str(user_data.get('id', 'N/A')),
                    'name': user_data.get('name', 'Unknown'),
                    'room': user_data.get('room', 'N/A'),
                    'department': user_data.get('dept_name', 'N/A'),
                    'role': user_data.get('role', 'member'),
                    'has_biometrics': biometrics.get('status') == 'active',
                    'has_face': bool(biometrics.get('face_image_path')),
                    'has_fingerprint': bool(biometrics.get('fingerprint_image_path'))
                })
            
            return students
            
        except Exception as e:
            print(f"❌ Error getting students: {str(e)}")
            return []
    
    def log_authentication(self, log_data):
        """Log authentication attempt"""
        try:
            new_ref = self.authentication_ref.push()
            log_data['id'] = new_ref.key
            log_data['timestamp'] = datetime.now().isoformat()
            new_ref.set(log_data)
            return log_data['id']
        except Exception as e:
            print(f"Error logging authentication: {e}")
            return None
    
    def get_authentication_logs(self, student_id=None, limit=50):
        """Get authentication logs"""
        try:
            logs = self.authentication_ref.get()
            
            if not logs:
                return []
            
            # Convert to list
            log_list = []
            for log_key, log_data in logs.items():
                if student_id is None or str(log_data.get('student_id')) == str(student_id):
                    log_data['log_id'] = log_key
                    log_list.append(log_data)
            
            # Sort by timestamp (most recent first)
            log_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return log_list[:limit]
            
        except Exception as e:
            print(f"❌ Error getting logs: {str(e)}")
            return []
    
    def log_monitoring_event(self, event_data):
        """Log monitoring detection event"""
        try:
            new_ref = self.monitoring_ref.push()
            event_data['id'] = new_ref.key
            event_data['timestamp'] = datetime.now().isoformat()
            new_ref.set(event_data)
            return event_data['id']
        except Exception as e:
            print(f"Error logging monitoring event: {e}")
            return None
    
    def get_monitoring_events(self, location=None, start_time=None, end_time=None):
        """Get monitoring events"""
        try:
            events = self.monitoring_ref.get()
            
            if not events:
                return []
            
            # Convert to list and filter
            event_list = []
            for event_key, event_data in events.items():
                # Apply filters
                if location and event_data.get('location') != location:
                    continue
                
                # Add to list
                event_data['event_id'] = event_key
                event_list.append(event_data)
            
            # Sort by timestamp
            event_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return event_list
            
        except Exception as e:
            print(f"❌ Error getting monitoring events: {str(e)}")
            return []