# Save as fix_insightface.py

import os
import shutil
from pathlib import Path

def fix_insightface():
    print("🔄 Fixing InsightFace models...")
    print("=" * 60)
    
    # Get insightface directory
    home = Path.home()
    insightface_dir = home / '.insightface' / 'models' / 'buffalo_l'
    
    print(f"\n📁 Model directory: {insightface_dir}")
    
    # Delete corrupted models
    if insightface_dir.exists():
        print(f"\n🗑️ Deleting corrupted models...")
        try:
            shutil.rmtree(insightface_dir)
            print("✅ Deleted old models")
        except Exception as e:
            print(f"⚠️ Warning: {e}")
    
    # Reinstall fresh models
    print("\n📥 Downloading fresh InsightFace models...")
    print("   (This may take 2-5 minutes on first run)")
    print("   (Models are ~500MB)")
    
    try:
        from insightface.app import FaceAnalysis
        
        print("\n🔄 Initializing FaceAnalysis (auto-downloads models)...")
        app = FaceAnalysis(providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))
        
        print("\n✅ Models downloaded and loaded successfully!")
        print(f"✅ FaceAnalysis ready!")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 InsightFace Model Recovery Tool")
    print("=" * 60)
    
    if fix_insightface():
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("\nYou can now run: python api.py")
    else:
        print("\n" + "=" * 60)
        print("❌ Failed to fix models")
        print("=" * 60)