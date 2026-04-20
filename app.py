from models.face_model import FaceModel
from models.fingerprint_model import FingerprintModel
from models.firebase_model import FirebaseModel
from models.fusion_model import FusionModel
from utils.storage_manager import StorageManager

class AuthenticationSystem:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Starting Authentication System")
        print("="*50 + "\n")
        
        self.storage_manager = StorageManager()
        self.face_model = FaceModel()
        self.fingerprint_model = FingerprintModel()
        self.firebase_model = FirebaseModel()
        self.fusion_model = FusionModel()
        
        print("\n✅ All models loaded!\n")
    
    def register_biometrics(self, student_id, face_image_path, fingerprint_image_path):
        """
        Register biometrics for EXISTING student in database
        Images are saved locally, only paths go to Firebase
        """
        print(f"\n📝 Registering biometrics for: {student_id}")
        print("-" * 50)
        
        # Check if student exists in Firebase
        firebase_result = self.firebase_model.get_student(student_id)
        
        if not firebase_result['matched']:
            print(f"❌ Student {student_id} not found in database")
            print("   Please add student to Firebase Realtime Database first")
            return False
        
        student_data = firebase_result['data']
        print(f"✅ Found student: {student_data['name']}")
        
        # Step 1: Save images locally
        print("\n📁 Saving images locally...")
        saved_face_path = self.storage_manager.save_face_image(
            face_image_path, student_id
        )
        saved_fingerprint_path = self.storage_manager.save_fingerprint_image(
            fingerprint_image_path, student_id
        )
        
        # Step 2: Register face encoding in model
        print("\n🔍 Processing face...")
        face_ok = self.face_model.register_face(saved_face_path, student_id)
        
        # Step 3: Register fingerprint in model
        print("\n👆 Processing fingerprint...")
        finger_ok = self.fingerprint_model.register_fingerprint(saved_fingerprint_path, student_id)
        
        # Step 4: Save paths to Firebase (NOT the images)
        if face_ok and finger_ok:
            print("\n☁️ Saving paths to Firebase...")
            firebase_ok = self.firebase_model.save_biometric_paths(
                student_id, 
                saved_face_path,
                saved_fingerprint_path
            )
            
            if firebase_ok:
                print("\n✅ BIOMETRIC REGISTRATION SUCCESSFUL")
                print(f"   Images stored at: {self.storage_manager.base_path}")
                print(f"   Paths saved to Firebase ✅")
                return True
        
        print("\n❌ BIOMETRIC REGISTRATION FAILED\n")
        return False
    
    def authenticate(self, student_id, face_image_path, fingerprint_image_path):
        """Authenticate a student"""
        print(f"\n🔐 Authenticating: {student_id}")
        print("="*50)
        
        # Step 1: Face recognition
        print("\n1️⃣ Checking face...")
        face_result = self.face_model.recognize_face(face_image_path)
        if face_result['matched']:
            print(f"   ✅ Face matched (confidence: {face_result['confidence']:.2f})")
        else:
            print(f"   ❌ Face not matched (confidence: {face_result.get('confidence', 0.0):.2f})")
        
        # Step 2: Fingerprint verification
        print("\n2️⃣ Checking fingerprint...")
        fingerprint_result = self.fingerprint_model.verify_fingerprint(
            fingerprint_image_path, student_id
        )
        if fingerprint_result['matched']:
            print(f"   ✅ Fingerprint matched (confidence: {fingerprint_result['confidence']:.2f})")
        else:
            print(f"   ❌ Fingerprint not matched (confidence: {fingerprint_result.get('confidence', 0.0)::.2f})")
        
        # Step 3: Firebase check
        print("\n3️⃣ Checking database...")
        firebase_result = self.firebase_model.get_student(student_id)
        if firebase_result['matched']:
            print(f"   ✅ Student found: {firebase_result['data']['name']}")
        else:
            print(f"   ❌ Student not found")
        
        # Step 4: FUSION
        print("\n4️⃣ Making final decision...")
        result = self.fusion_model.fuse(face_result, fingerprint_result, firebase_result)
        
        # Log to Firebase
        self.firebase_model.log_authentication(student_id, result)
        
        print("\n" + "="*50)
        print("📊 FUSION RESULT:")
        print("="*50)
        print(f"Final Score: {result['score']}")
        print(f"Matched Modalities: {result['matched_count']}/3")
        print(f"Face: {'✅' if result['face_matched'] else '❌'}")
        print(f"Fingerprint: {'✅' if result['fingerprint_matched'] else '❌'}")
        print(f"Database: {'✅' if result['firebase_matched'] else '❌'}")
        print(f"\n{'✅ VERIFIED' if result['verified'] else '❌ NOT VERIFIED'}")
        print("="*50 + "\n")
        
        return result
    
    def list_students(self):
        students = self.firebase_model.get_all_students()  # ← This line was MISSING!
    
        if len(students) == 0:
            print("\n📋 STUDENTS IN DATABASE:")
            print("="*80)
            print("   ❌ No students found in database")
            print("="*80 + "\n")
            return students
    
        print("\n📋 STUDENTS IN DATABASE:")
        print("="*80)
    
        for student in students:
            bio_status = "✅ Registered" if student.get('has_biometrics', False) else "❌ Not registered"
        
            # Handle None values safely
            student_id = str(student.get('id', 'N/A'))
            name = student.get('name', 'Unknown')
            room = str(student.get('room') or 'N/A')  # Convert None to 'N/A'
        
            # Truncate if too long
            if len(student_id) > 20:
                student_id = student_id[:17] + "..."
            if len(name) > 30:
                name = name[:27] + "..."
        
            # Format with proper padding
            print(f"ID: {student_id:20s} | Name: {name:30s} | Room: {room:5s} | Biometrics: {bio_status}")
    
        print("="*80 + "\n")
    
        return students
    
    def view_student_biometrics(self, student_id):
        """View stored biometric information"""
        print(f"\n🔍 Viewing biometrics for: {student_id}")
        print("-" * 50)
        
        # Get from Firebase
        paths = self.firebase_model.get_biometric_paths(student_id)
        
        if paths is None:
            print("❌ No biometric data found")
            return
        
        print(f"✅ Biometrics registered at: {paths.get('registered_at')}")
        print(f"   Status: {paths.get('status')}")
        print(f"   Face image: {paths.get('face_path')}")
        print(f"   Fingerprint image: {paths.get('fingerprint_path')}")
        
        # Check if files exist
        import os
        if os.path.exists(paths.get('face_path', '')):
            print("   Face file: ✅ Exists")
        else:
            print("   Face file: ❌ Not found")
        
        if os.path.exists(paths.get('fingerprint_path', '')):
            print("   Fingerprint file: ✅ Exists")
        else:
            print("   Fingerprint file: ❌ Not found")
    
    def get_storage_stats(self):
        """Show storage statistics"""
        stats = self.storage_manager.get_storage_stats()
        
        print("\n💾 STORAGE STATISTICS:")
        print("="*50)
        for category, data in stats.items():
            print(f"{category.capitalize()}: {data['file_count']} files ({data['size_mb']} MB)")
        print("="*50 + "\n")

if __name__ == "__main__":
    system = AuthenticationSystem()
    
    print("\n👉 System is ready!")
    print("   Your existing students from Firebase:")
    system.list_students()
    print("\n   Next: Run test_system.py to register biometrics\n")
# Add this method to AuthenticationSystem class

def authenticate_flexible(self, student_id, face_image_path=None, fingerprint_image_path=None, mode='full'):
    """
    Flexible authentication with different modal combinations
    
    Modes:
    - 'full': Face + Fingerprint + Database (3 modals)
    - 'face+fingerprint': Only biometrics (2 modals)
    - 'face+db': Face + Database (2 modals)
    - 'fingerprint+db': Fingerprint + Database (2 modals)
    - 'face_only': Only face (1 modal)
    - 'fingerprint_only': Only fingerprint (1 modal)
    - 'db_only': Only database check (1 modal)
    """
    
    print(f"\n{'='*50}")
    print(f"🔐 Flexible Authentication: {student_id}")
    print(f"   Mode: {mode}")
    print(f"{'='*50}\n")
    
    results = {
        'face': None,
        'fingerprint': None,
        'firebase': None
    }
    
    # Check database (always if in mode)
    if mode in ['full', 'face+db', 'fingerprint+db', 'db_only']:
        print("1️⃣ Checking database...")
        firebase_result = self.firebase_model.get_student(student_id)
        results['firebase'] = firebase_result['matched']
        
        if firebase_result['matched']:
            print(f"   ✅ Student found: {firebase_result['data']['name']}")
        else:
            print("   ❌ Student not found")
    
    # Check face (if provided and in mode)
    if face_image_path and mode in ['full', 'face+fingerprint', 'face+db', 'face_only']:
        print("\n2️⃣ Checking face...")
        face_result = self.face_model.recognize_face(face_image_path)
        results['face'] = face_result['matched'] and face_result.get('student_id') == student_id
        
        if results['face']:
            print(f"   ✅ Face matched (confidence: {face_result['confidence']:.2f})")
        else:
            print("   ❌ Face not matched")
    
    # Check fingerprint (if provided and in mode)
    if fingerprint_image_path and mode in ['full', 'face+fingerprint', 'fingerprint+db', 'fingerprint_only']:
        print("\n3️⃣ Checking fingerprint...")
        fingerprint_result = self.fingerprint_model.verify_fingerprint(
            fingerprint_image_path, student_id
        )
        results['fingerprint'] = fingerprint_result['matched']
        
        if results['fingerprint']:
            print(f"   ✅ Fingerprint matched (confidence: {fingerprint_result['confidence']:.2f})")
        else:
            print("   ❌ Fingerprint not matched")
    
    # Make decision based on mode
    print(f"\n4️⃣ Making decision ({mode})...")
    
    # Count matched modals
    matched_count = sum(1 for v in results.values() if v is True)
    total_modals = sum(1 for v in results.values() if v is not None)
    
    # Decision rules by mode
    if mode == 'full':
        # 3 modals: Need at least 2/3
        verified = matched_count >= 2
        threshold = 2
    elif mode in ['face+fingerprint', 'face+db', 'fingerprint+db']:
        # 2 modals: Need both
        verified = matched_count >= 2
        threshold = 2
    elif mode in ['face_only', 'fingerprint_only', 'db_only']:
        # 1 modal: Need that one
        verified = matched_count >= 1
        threshold = 1
    else:
        verified = False
        threshold = 0
    
    # Prepare result
    result = {
        'verified': verified,
        'student_id': student_id,
        'mode': mode,
        'matched_modals': matched_count,
        'total_modals': total_modals,
        'threshold': threshold,
        'details': {
            'face': results['face'],
            'fingerprint': results['fingerprint'],
            'database': results['firebase']
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Log to Firebase
    self.firebase_model.log_authentication(student_id, result)
    
    # Print result
    print(f"\n{'='*50}")
    print("📊 RESULT:")
    print(f"{'='*50}")
    print(f"Status: {'✅ VERIFIED' if verified else '❌ FAILED'}")
    print(f"Matched: {matched_count}/{total_modals} (threshold: {threshold})")
    print(f"{'='*50}\n")
    
    return result

# Use localhost consistently
# Removed JavaScript code as it does not belong in a Python file.

