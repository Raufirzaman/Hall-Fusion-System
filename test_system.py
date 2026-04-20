from app import AuthenticationSystem
from PIL import Image, ImageDraw
import os

def create_dummy_image(name, path):
    """Create a simple test image"""
    img = Image.new('RGB', (400, 400), color=(255, 220, 177))
    draw = ImageDraw.Draw(img)
    
    # Draw simple face
    draw.ellipse([150, 150, 180, 180], fill=(0, 0, 0))  # Left eye
    draw.ellipse([220, 150, 250, 180], fill=(0, 0, 0))  # Right eye
    draw.arc([150, 220, 250, 280], 0, 180, fill=(0, 0, 0), width=3)  # Smile
    
    img.save(path)
    print(f"✅ Created test image: {path}")

def main():
    print("\n" + "="*70)
    print(" TESTING FUSION SYSTEM (Images on PC, Paths in Firebase)")
    print("="*70 + "\n")
    
    # Create test images
    os.makedirs('storage/temp', exist_ok=True)
    
    print("📸 Creating test images...")
    create_dummy_image("Face", "storage/temp/test_face.jpg")
    create_dummy_image("Fingerprint", "storage/temp/test_finger.jpg")
    
    # Initialize system
    system = AuthenticationSystem()
    
    # Show existing students
    students = system.list_students()
    
    if len(students) == 0:
        print("\n⚠️ No students found in Firebase!")
        print("   Please add students to Firebase Realtime Database first.")
        return
    
    # Select first student for testing
    test_student = students[0]
    student_id = test_student['id']
    
    print(f"\n📝 We'll test with: {test_student['name']} (ID: {student_id})")
    
    input("\n⏸️  Press ENTER to register biometrics...")
    
    # Test 1: Register biometrics
    print("\n" + "="*70)
    print(" TEST 1: REGISTER BIOMETRICS")
    print("="*70)
    
    success = system.register_biometrics(
        student_id=student_id,
        face_image_path="storage/temp/test_face.jpg",
        fingerprint_image_path="storage/temp/test_finger.jpg"
    )
    
    if not success:
        print("\n❌ Registration failed. Cannot continue.")
        return
    
    input("\n⏸️  Press ENTER to view stored biometric info...")
    
    # View what was stored
    system.view_student_biometrics(student_id)
    
    input("\n⏸️  Press ENTER to test authentication...")
    
    # Test 2: Authenticate (using the same images)
    print("\n" + "="*70)
    print(" TEST 2: AUTHENTICATION")
    print("="*70)
    
    result = system.authenticate(
        student_id=student_id,
        face_image_path="storage/temp/test_face.jpg",
        fingerprint_image_path="storage/temp/test_finger.jpg"
    )
    
    input("\n⏸️  Press ENTER to view storage stats...")
    
    # Show storage stats
    system.get_storage_stats()
    
    # Summary
    print("\n" + "="*70)
    print(" TEST COMPLETE")
    print("="*70)
    print(f"\n✅ Registration: SUCCESS")
    print(f"{'✅' if result['verified'] else '❌'} Authentication: {'VERIFIED' if result['verified'] else 'NOT VERIFIED'}")
    print(f"\n📁 Check your storage folder:")
    print(f"   {os.path.abspath('storage')}")
    print(f"\n☁️ Check Firebase Console:")
    print(f"   Database → users → {student_id} → biometrics")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()