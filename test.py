import os
import sys

print("="*60)
print("🔍 Checking Hall Fusion System Setup")
print("="*60)

# Get project root
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"\n📁 Project Root: {project_root}")

# Check models directory
models_dir = os.path.join(project_root, 'models')
print(f"\n📂 Models Directory: {models_dir}")
print(f"   Exists: {os.path.exists(models_dir)}")

if not os.path.exists(models_dir):
    print(f"   Creating directory...")
    os.makedirs(models_dir, exist_ok=True)
    print(f"   ✅ Created")

# Check write permissions
test_file = os.path.join(models_dir, 'test_write.txt')
try:
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print(f"   ✅ Write permissions: OK")
except Exception as e:
    print(f"   ❌ Write permissions: FAILED - {e}")

# Check for existing encoding files
face_encodings = os.path.join(models_dir, 'face_encodings.pkl')
fingerprint_encodings = os.path.join(models_dir, 'fingerprint_encodings.pkl')

print(f"\n📄 Encoding Files:")
print(f"   Face encodings: {face_encodings}")
print(f"      Exists: {os.path.exists(face_encodings)}")
if os.path.exists(face_encodings):
    print(f"      Size: {os.path.getsize(face_encodings)} bytes")

print(f"   Fingerprint encodings: {fingerprint_encodings}")
print(f"      Exists: {os.path.exists(fingerprint_encodings)}")
if os.path.exists(fingerprint_encodings):
    print(f"      Size: {os.path.getsize(fingerprint_encodings)} bytes")

# Check storage directory
storage_dir = os.path.join(project_root, 'storage')
print(f"\n💾 Storage Directory: {storage_dir}")
print(f"   Exists: {os.path.exists(storage_dir)}")

if not os.path.exists(storage_dir):
    print(f"   Creating directory...")
    os.makedirs(storage_dir, exist_ok=True)
    print(f"   ✅ Created")

print("\n" + "="*60)
print("✅ Setup check complete!")
print("="*60)