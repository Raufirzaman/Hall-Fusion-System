from app import AuthenticationSystem
from PIL import Image, ImageDraw
import os
import random

def create_test_image(path, style="face"):
    """Create a test image with different styles"""
    if style == "face":
        color = (255, 220, 177)  # Skin tone
    elif style == "fingerprint":
        color = (200, 200, 200)  # Gray
    elif style == "new_face":
        color = (255, 200, 150)  # Slightly different skin tone
    elif style == "new_fingerprint":
        color = (180, 180, 180)  # Different gray
    else:
        color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
    
    img = Image.new('RGB', (400, 400), color=color)
    draw = ImageDraw.Draw(img)
    
    if "face" in style:
        # Draw face features
        draw.ellipse([150, 150, 180, 180], fill=(0, 0, 0))  # Left eye
        draw.ellipse([220, 150, 250, 180], fill=(0, 0, 0))  # Right eye
        draw.arc([150, 220, 250, 280], 0, 180, fill=(0, 0, 0), width=3)  # Smile
        if "new" in style:
            # Add extra feature for new face
            draw.rectangle([180, 100, 220, 130], fill=(100, 50, 0))  # Hair
    else:
        # Draw fingerprint-like pattern
        for i in range(10):
            y = 150 + (i * 20)
            draw.arc([100, y, 300, y + 40], 0, 180, fill=(0, 0, 0), width=2)
    
    img.save(path)
    print(f"   ✅ Created: {path}")

def register_menu(system):
    """Register new biometrics"""
    print("\n" + "="*70)
    print(" REGISTER BIOMETRICS")
    print("="*70)
    
    # Show available students
    students = system.firebase_model.get_all_students()
    
    print("\n📋 Available Students:")
    for student in students:
        bio_status = "✅ Has biometrics" if student['has_biometrics'] else "❌ No biometrics"
        print(f"   ID: {student['id']} | {student['name']} | {bio_status}")
    
    student_id = input("\nEnter Student ID to register: ").strip()
    
    if not student_id:
        print("❌ Invalid ID")
        return
    
    # Create test images
    os.makedirs('storage/temp', exist_ok=True)
    face_path = "storage/temp/reg_face.jpg"
    finger_path = "storage/temp/reg_finger.jpg"
    
    print("\n📸 Creating test images...")
    create_test_image(face_path, "face")
    create_test_image(finger_path, "fingerprint")
    
    print(f"\n📁 Test images created in: storage/temp/")
    print("   ⚠️ Note: In production, capture from real camera/scanner")
    
    input("\n⏸️  Press ENTER to proceed with registration...")
    
    success = system.register_biometrics(student_id, face_path, finger_path)
    
    if success:
        print("\n✅ Registration successful!")
        input("\n⏸️  Press ENTER to continue...")
    else:
        print("\n❌ Registration failed!")
        input("\n⏸️  Press ENTER to continue...")

def update_menu(system):
    """Update existing biometrics - WITH FULL OPTIONS"""
    print("\n" + "="*70)
    print(" UPDATE BIOMETRIC DATA")
    print("="*70)
    
    # Show students with biometrics
    students = system.firebase_model.get_all_students()
    
    print("\n📋 Students with Biometrics:")
    registered_students = [s for s in students if s['has_biometrics']]
    
    if len(registered_students) == 0:
        print("   ❌ No students have registered biometrics yet!")
        print("   Please register biometrics first (Option 1)")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    for i, student in enumerate(registered_students, 1):
        print(f"   {i}. ID: {student['id']} | {student['name']} | Room: {student['room']}")
    
    # Let user choose student
    try:
        choice = input(f"\nSelect student (1-{len(registered_students)}) or enter ID directly: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(registered_students):
            student_id = registered_students[int(choice) - 1]['id']
        else:
            student_id = choice
        
    except (ValueError, IndexError):
        print("❌ Invalid choice")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    # Show current biometric data
    print(f"\n🔍 Current biometric data for Student ID: {student_id}")
    print("-" * 70)
    system.view_student_biometrics(student_id)
    
    # Ask what to update
    print("\n" + "="*70)
    print(" WHAT DO YOU WANT TO UPDATE?")
    print("="*70)
    print("\n1. Update Face Image Only")
    print("2. Update Fingerprint Image Only")
    print("3. Update Both Face and Fingerprint")
    print("4. Cancel")
    
    update_choice = input("\nEnter choice (1-4): ").strip()
    
    if update_choice == '4':
        print("❌ Update cancelled")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    # Create test directory
    os.makedirs('storage/temp', exist_ok=True)
    
    # Prepare new images based on choice
    new_face_path = None
    new_finger_path = None
    
    print("\n📸 Creating NEW test images...")
    
    if update_choice == '1':
        # Update face only
        new_face_path = "storage/temp/new_face.jpg"
        create_test_image(new_face_path, "new_face")
        print("\n   ✅ New face image ready")
        print("   ℹ️ Fingerprint will remain unchanged")
        
    elif update_choice == '2':
        # Update fingerprint only
        new_finger_path = "storage/temp/new_fingerprint.jpg"
        create_test_image(new_finger_path, "new_fingerprint")
        print("\n   ✅ New fingerprint image ready")
        print("   ℹ️ Face image will remain unchanged")
        
    elif update_choice == '3':
        # Update both
        new_face_path = "storage/temp/new_face.jpg"
        new_finger_path = "storage/temp/new_fingerprint.jpg"
        create_test_image(new_face_path, "new_face")
        create_test_image(new_finger_path, "new_fingerprint")
        print("\n   ✅ Both new images ready")
    
    else:
        print("❌ Invalid choice")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    print("\n   ⚠️ Note: In production, capture from real camera/scanner")
    
    input("\n⏸️  Press ENTER to start update process...")
    
    # Perform update
    print("\n" + "="*70)
    print(" UPDATING...")
    print("="*70)
    
    success = system.update_biometrics(
        student_id=student_id,
        face_image_path=new_face_path,
        fingerprint_image_path=new_finger_path
    )
    
    if success:
        print("\n" + "="*70)
        print(" ✅ UPDATE SUCCESSFUL!")
        print("="*70)
        
        # Show updated data
        print("\n🔍 Updated biometric data:")
        print("-" * 70)
        system.view_student_biometrics(student_id)
        
        # Ask if user wants to test authentication
        test_auth = input("\n❓ Do you want to test authentication with updated data? (y/n): ").strip().lower()
        
        if test_auth == 'y':
            print("\n🔐 Testing authentication...")
            
            # Use the same images we just uploaded
            test_face = new_face_path if new_face_path else system.storage_manager.get_face_image_path(student_id)
            test_finger = new_finger_path if new_finger_path else system.storage_manager.get_fingerprint_image_path(student_id)
            
            if test_face and test_finger:
                system.authenticate(student_id, test_face, test_finger)
            else:
                print("❌ Could not find test images")
        
        print("\n✅ Update process complete!")
        input("\n⏸️  Press ENTER to continue...")
    else:
        print("\n❌ UPDATE FAILED!")
        input("\n⏸️  Press ENTER to continue...")

def authenticate_menu(system):
    """Authenticate a student"""
    print("\n" + "="*70)
    print(" AUTHENTICATE STUDENT")
    print("="*70)
    
    # Show students with biometrics
    students = system.firebase_model.get_all_students()
    registered_students = [s for s in students if s['has_biometrics']]
    
    if len(registered_students) == 0:
        print("\n   ❌ No students have registered biometrics yet!")
        print("   Please register biometrics first (Option 1)")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    print("\n📋 Students with Biometrics:")
    for student in registered_students:
        print(f"   ID: {student['id']} | {student['name']}")
    
    student_id = input("\nEnter Student ID to authenticate: ").strip()
    
    if not student_id:
        print("❌ Invalid ID")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    # Create test images
    os.makedirs('storage/temp', exist_ok=True)
    face_path = "storage/temp/auth_face.jpg"
    finger_path = "storage/temp/auth_finger.jpg"
    
    print("\n📸 Creating test images for authentication...")
    create_test_image(face_path, "face")
    create_test_image(finger_path, "fingerprint")
    
    print("\n   ⚠️ Note: In production, capture from real camera/scanner")
    
    input("\n⏸️  Press ENTER to authenticate...")
    
    system.authenticate(student_id, face_path, finger_path)
    
    input("\n⏸️  Press ENTER to continue...")

def view_menu(system):
    """View student biometric info"""
    print("\n" + "="*70)
    print(" VIEW BIOMETRIC DATA")
    print("="*70)
    
    print("\nOptions:")
    print("1. View specific student")
    print("2. View all students")
    
    choice = input("\nChoice (1-2): ").strip()
    
    if choice == '1':
        student_id = input("\nEnter Student ID: ").strip()
        if student_id:
            system.view_student_biometrics(student_id)
        else:
            print("❌ Invalid ID")
    elif choice == '2':
        system.list_students()
    else:
        print("❌ Invalid choice")
    
    input("\n⏸️  Press ENTER to continue...")

def logs_menu(system):
    """View authentication logs"""
    print("\n" + "="*70)
    print(" AUTHENTICATION LOGS")
    print("="*70)
    
    print("\nOptions:")
    print("1. View all logs")
    print("2. View logs for specific student")
    
    choice = input("\nChoice (1-2): ").strip()
    
    if choice == '1':
        logs = system.firebase_model.get_authentication_logs()
    elif choice == '2':
        student_id = input("\nEnter Student ID: ").strip()
        logs = system.firebase_model.get_authentication_logs(student_id)
    else:
        print("❌ Invalid choice")
        input("\n⏸️  Press ENTER to continue...")
        return
    
    if len(logs) == 0:
        print("\n   ❌ No logs found")
    else:
        print(f"\n📋 Found {len(logs)} log entries:")
        print("="*70)
        
        for log in logs[:20]:  # Show last 20
            status = "✅ VERIFIED" if log.get('verified') else "❌ FAILED"
            print(f"\nStudent ID: {log.get('student_id')}")
            print(f"Time: {log.get('timestamp')}")
            print(f"Status: {status}")
            print(f"Score: {log.get('score')}")
            print(f"Face: {'✅' if log.get('face_matched') else '❌'} | "
                  f"Fingerprint: {'✅' if log.get('fingerprint_matched') else '❌'} | "
                  f"Database: {'✅' if log.get('firebase_matched') else '❌'}")
            print("-" * 70)
    
    input("\n⏸️  Press ENTER to continue...")

def main():
    print("\n" + "="*70)
    print(" 🎓 HALL MANAGEMENT - BIOMETRIC AUTHENTICATION SYSTEM")
    print("="*70)
    
    system = AuthenticationSystem()
    
    while True:
        print("\n" + "="*70)
        print(" MAIN MENU")
        print("="*70)
        print("\n1. 📝 Register New Biometrics")
        print("2. 🔄 Update Existing Biometrics (Face/Fingerprint)")
        print("3. 🔐 Authenticate Student")
        print("4. 👁️  View Student Biometric Data")
        print("5. 📋 List All Students")
        print("6. 📊 View Authentication Logs")
        print("7. 💾 Storage Statistics")
        print("8. ❌ Exit")
        
        choice = input("\nEnter choice (1-8): ").strip()
        
        if choice == '1':
            register_menu(system)
        elif choice == '2':
            update_menu(system)
        elif choice == '3':
            authenticate_menu(system)
        elif choice == '4':
            view_menu(system)
        elif choice == '5':
            system.list_students()
            input("\n⏸️  Press ENTER to continue...")
        elif choice == '6':
            logs_menu(system)
        elif choice == '7':
            system.get_storage_stats()
            input("\n⏸️  Press ENTER to continue...")
        elif choice == '8':
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid choice!")
            input("\n⏸️  Press ENTER to continue...")

if __name__ == "__main__":
    main()