from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
from PIL import Image
import json
import threading
from app import AuthenticationSystem
import os
from datetime import datetime

# Import models and utilities
from models.face_model import FaceModel
from models.fingerprint_model import FingerprintModel
from utils.firebase_manager import FirebaseManager
from utils.storage_manager import StorageManager

app = Flask(__name__)

# ✅ Simple CORS - allow everything
CORS(app)

# ✅ Initialize once
firebase_db = FirebaseManager()
face_model = FaceModel()
fingerprint_model = FingerprintModel()
storage_manager = StorageManager()

print("✅ Firebase initialized")
print("✅ Face model loaded")
print("✅ Fingerprint model loaded")
print("✅ Storage manager ready")
print("="*60 + "\n")

# ✅ ADD THIS HELPER FUNCTION
def decode_base64_image(base64_string):
    """
    Decode base64 string to OpenCV image
    
    Args:
        base64_string: Base64 encoded image string (with or without data URI prefix)
    
    Returns:
        numpy.ndarray: OpenCV image in BGR format, or None if decoding fails
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64 to bytes
        img_bytes = base64.b64decode(base64_string)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        
        # Decode to OpenCV image (BGR format)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("❌ Failed to decode image - invalid image data")
            return None
        
        print(f"✅ Image decoded successfully - shape: {img.shape}")
        return img
    
    except base64.binascii.Error as e:
        print(f"❌ Base64 decode error: {e}")
        return None
    
    except Exception as e:
        print(f"❌ Image decode error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API is running"""
    return jsonify({
        'success': True,
        'status': 'online',
        'message': 'API is running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get authentication logs"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # Get logs from Firebase
        logs = firebase_db.get_authentication_logs(limit=limit)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    
    except Exception as e:
        print(f"Error getting logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': []
        })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    try:
        # Get all students
        students = firebase_db.get_all_students()
        
        # Count registered vs pending
        total_students = len(students)
        registered_students = len([s for s in students if s.get('has_biometrics')])
        pending_students = total_students - registered_students
        
        # Get today's activity
        logs = firebase_db.get_authentication_logs(limit=100)
        today = datetime.now().date().isoformat()
        today_activity = len([log for log in logs if log.get('timestamp', '').startswith(today)])
        
        # Get violations
        # For now, return 0 - implement violations counting later
        violations = 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_students': total_students,
                'registered_students': registered_students,
                'pending_students': pending_students,
                'today_activity': today_activity,
                'violations': violations
            }
        })
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {
                'total_students': 0,
                'registered_students': 0,
                'pending_students': 0,
                'today_activity': 0,
                'violations': 0
            }
        })


@app.route('/api/activity', methods=['GET'])
def get_activity():
    """Get recent activity"""
    try:
        limit = int(request.args.get('limit', 5))
        
        # Get authentication logs
        logs = firebase_db.get_authentication_logs(limit=limit)
        
        # Format for frontend
        activity = []
        for log in logs:
            activity.append({
                'id': log.get('log_id'),
                'student_id': log.get('student_id'),
                'student_name': log.get('student_name', 'Unknown'),
                'action': log.get('action', 'Authentication'),
                'timestamp': log.get('timestamp'),
                'success': log.get('success', True),
                'method': log.get('method', 'face')
            })
        
        return jsonify({
            'success': True,
            'activity': activity,
            'count': len(activity)
        })
    
    except Exception as e:
        print(f"Error getting activity: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'activity': []
        })


@app.route('/api/violations', methods=['GET'])
def get_violations():
    """Get violations"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # Get violations from Firebase (implement this in firebase_manager)
        # For now, return empty array
        violations = []
        
        return jsonify({
            'success': True,
            'violations': violations,
            'count': len(violations)
        })
    
    except Exception as e:
        print(f"Error getting violations: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'violations': []
        })


@app.route('/api/students', methods=['GET'])
def list_students():
    """Get all students"""
    try:
        students = firebase_db.get_all_students()
        return jsonify({
            'success': True,
            'count': len(students),
            'students': students
        })
    except Exception as e:
        print(f"Error listing students: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'students': []
        })


@app.route('/api/students/<student_id>', methods=['GET'])
def get_student(student_id):
    """Get specific student info"""
    try:
        student = firebase_db.get_student(student_id)
        
        if student:
            # Add biometric paths
            paths = firebase_db.get_biometric_paths(student_id)
            if paths:
                student['biometric_paths'] = paths
            
            return jsonify({
                'success': True,
                'student': student
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Student not found'
            }), 404
    
    except Exception as e:
        print(f"Error getting student: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/register', methods=['POST'])  # ✅ Removed OPTIONS
def register_biometrics():
    """Register face and/or fingerprint"""
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        student_id = data.get('student_id')
        face_base64 = data.get('face_image')
        fingerprint_base64 = data.get('fingerprint_image')
        
        print(f"\n📝 Registration request for: {student_id}")
        
        if not student_id:
            return jsonify({
                'success': False,
                'error': 'Student ID is required'
            }), 400
        
        # Check if student exists
        student = firebase_db.get_student(student_id)
        if not student:
            return jsonify({
                'success': False,
                'error': f'Student {student_id} not found in database'
            }), 404
        
        print(f"   ✅ Student found: {student.get('name', 'Unknown')}")
        
        face_path = None
        fingerprint_path = None
        
        # Process face image
        if face_base64:
            try:
                print("   Processing face image...")
                
                if ',' in face_base64:
                    face_base64 = face_base64.split(',')[1]
                
                face_bytes = base64.b64decode(face_base64)
                face_image = Image.open(io.BytesIO(face_bytes))
                face_image = face_image.convert('RGB')
                
                face_array = np.array(face_image)
                face_array = cv2.cvtColor(face_array, cv2.COLOR_RGB2BGR)
                
                face_path = storage_manager.save_face_image(face_array, student_id)
                print(f"   ✅ Face saved: {face_path}")
                
                success = face_model.register_face(face_array, student_id, mode='single')
                
                if not success:
                    return jsonify({
                        'success': False,
                        'error': 'Face registration failed'
                    }), 400
                
                print(f"   ✅ Face registered in model")
                
            except Exception as e:
                print(f"   ❌ Face error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Face processing failed: {str(e)}'
                }), 400
        
        # Process fingerprint
        if fingerprint_base64:
            try:
                print("   Processing fingerprint...")
                
                if ',' in fingerprint_base64:
                    fingerprint_base64 = fingerprint_base64.split(',')[1]
                
                fingerprint_bytes = base64.b64decode(fingerprint_base64)
                fingerprint_image = Image.open(io.BytesIO(fingerprint_bytes))
                fingerprint_image = fingerprint_image.convert('RGB')
                
                fingerprint_array = np.array(fingerprint_image)
                fingerprint_array = cv2.cvtColor(fingerprint_array, cv2.COLOR_RGB2BGR)
                
                fingerprint_path = storage_manager.save_fingerprint_image(
                    fingerprint_array, student_id
                )
                print(f"   ✅ Fingerprint saved: {fingerprint_path}")
                
                success = fingerprint_model.register_fingerprint(
                    fingerprint_array, student_id
                )
                
                if success:
                    print(f"   ✅ Fingerprint registered")
                
            except Exception as e:
                print(f"   ❌ Fingerprint error: {e}")
        
        # Update Firebase
        if face_path or fingerprint_path:
            try:
                firebase_db.save_biometric_paths(
                    student_id, 
                    face_image_path=face_path,
                    fingerprint_image_path=fingerprint_path
                )
                print(f"   ✅ Firebase updated")
            except Exception as e:
                print(f"   ⚠️ Firebase update warning: {e}")
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'has_face': bool(face_path),
            'has_fingerprint': bool(fingerprint_path),
            'face_path': face_path,
            'fingerprint_path': fingerprint_path,
            'message': 'Registration successful'
        })
    
    except Exception as e:
        print(f"❌ Registration error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate student using face and/or fingerprint"""
    
    try:
        print("\n" + "="*60)
        print("🔐 AUTHENTICATION REQUEST")
        print("="*60)
        
        data = request.get_json()
        
        # Get images
        face_base64 = data.get('face_image')
        fingerprint_base64 = data.get('fingerprint_image')
        
        student_id = None
        confidence = 0
        face_match = False
        fingerprint_match = False
        authenticated = False
        
        # Try face authentication
        if face_base64:
            print("\n🔍 Processing face authentication...")
            try:
                face_image = decode_base64_image(face_base64)
                if face_image is not None:
                    result = face_model.authenticate_face(face_image)
                    if result['match']:
                        student_id = result['student_id']
                        confidence = result['confidence']
                        face_match = True
                        authenticated = True
                        print(f"✅ Face authenticated: {student_id} ({confidence:.2%})")
                    else:
                        print(f"❌ Face not recognized: {result.get('error', 'No match')}")
            except Exception as e:
                print(f"❌ Face authentication error: {e}")
        
        # Try fingerprint authentication (if face failed)
        if not authenticated and fingerprint_base64:
            print("\n🔍 Processing fingerprint authentication...")
            try:
                fingerprint_image = decode_base64_image(fingerprint_base64)
                if fingerprint_image is not None:
                    result = fingerprint_model.authenticate_fingerprint(fingerprint_image)
                    if result['match']:
                        student_id = result['student_id']
                        confidence = result['confidence']
                        fingerprint_match = True
                        authenticated = True
                        print(f"✅ Fingerprint authenticated: {student_id} ({confidence:.2%})")
                    else:
                        print(f"❌ Fingerprint not recognized")
            except Exception as e:
                print(f"❌ Fingerprint authentication error: {e}")
        
        # Get student information if authenticated
        if authenticated and student_id:
            try:
                student = firebase_db.get_student(student_id)
                
                if student:
                    # ✅ Try to log, but don't fail if logging fails
                    try:
                        firebase_db.log_authentication({
                            'student_id': student_id,
                            'student_name': student.get('name', 'Unknown'),
                            'action': 'Authentication',
                            'success': True,
                            'method': 'fusion' if (face_match and fingerprint_match) else ('face' if face_match else 'fingerprint'),
                            'confidence': confidence,
                            'face_match': face_match,
                            'fingerprint_match': fingerprint_match,
                            'timestamp': datetime.now().isoformat()
                        })
                        print("✅ Authentication logged to Firebase")
                    except Exception as log_error:
                        # ⚠️ Just warn, don't fail the authentication
                        print(f"⚠️ Warning: Failed to log to Firebase: {log_error}")
                        print("   (Authentication still successful)")
                    
                    print(f"\n✅ Authentication successful!")
                    print(f"   Student: {student.get('name')} ({student_id})")
                    print(f"   Confidence: {confidence:.2%}")
                    print("="*60 + "\n")
                    
                    # ✅ Return response regardless of logging status
                    response_data = {
                        'authenticated': True,
                        'student_id': student_id,
                        'student_name': student.get('name', 'Unknown'),
                        'room': student.get('room', 'N/A'),
                        'department': student.get('department', 'N/A'),
                        'confidence': confidence,
                        'face_match': face_match,
                        'fingerprint_match': fingerprint_match,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    return jsonify(response_data)
                
                else:
                    print(f"⚠️ Student {student_id} not found in database")
                    return jsonify({
                        'authenticated': False,
                        'error': 'Student not found in database',
                        'student_id': student_id,
                        'confidence': confidence
                    }), 404
            
            except Exception as db_error:
                print(f"❌ Database error: {db_error}")
                # ✅ Still return authentication result even if DB fails
                return jsonify({
                    'authenticated': True,
                    'student_id': student_id,
                    'student_name': 'Unknown (DB Error)',
                    'confidence': confidence,
                    'face_match': face_match,
                    'fingerprint_match': fingerprint_match,
                    'error': 'Database connection issue',
                    'timestamp': datetime.now().isoformat()
                })
        
        else:
            # Not authenticated
            print(f"\n❌ Authentication failed")
            print(f"   No matching student found")
            print(f"   Confidence: {confidence:.2%}")
            print("="*60 + "\n")
            
            # ✅ Try to log failed attempt
            try:
                firebase_db.log_authentication({
                    'student_id': None,
                    'student_name': 'Unknown',
                    'action': 'Authentication',
                    'success': False,
                    'method': 'face' if face_base64 else 'fingerprint',
                    'confidence': confidence,
                    'face_match': False,
                    'fingerprint_match': False,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as log_error:
                print(f"⚠️ Failed to log failed attempt: {log_error}")
            
            response_data = {
                'authenticated': False,
                'error': 'No matching student found',
                'confidence': confidence,
                'face_match': face_match,
                'fingerprint_match': fingerprint_match,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response_data), 401
    
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        
        return jsonify({
            'authenticated': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/debug/encodings', methods=['GET'])
def debug_encodings():
    """Debug endpoint to check loaded encodings"""
    try:
        face_encodings_info = {
            'count': len(face_model.face_encodings),
            'students': list(face_model.face_encodings.keys()),
            'file_exists': os.path.exists('models/face_encodings.pkl'),
            'file_path': os.path.abspath('models/face_encodings.pkl')
        }
        
        fingerprint_encodings_info = {
            'count': len(fingerprint_model.fingerprint_encodings),
            'students': list(fingerprint_model.fingerprint_encodings.keys()),
            'file_exists': os.path.exists('models/fingerprint_encodings.pkl'),
            'file_path': os.path.abspath('models/fingerprint_encodings.pkl')
        }
        
        return jsonify({
            'success': True,
            'face_encodings': face_encodings_info,
            'fingerprint_encodings': fingerprint_encodings_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': f'The requested URL was not found on the server.'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Hall Fusion System API Starting...")
    print("="*50)
    print("📡 Server: http://localhost:5000")
    print("🔥 Firebase: Connected")
    print("🤖 Face Model: Ready")
    print("👆 Fingerprint Model: Ready")
    print("💾 Storage: Ready")
    print("\n📍 Available Endpoints:")
    print("   GET  /api/health")
    print("   GET  /api/stats")
    print("   GET  /api/logs")
    print("   GET  /api/activity")
    print("   GET  /api/students")
    print("   GET  /api/students/<id>")
    print("   POST /api/register")
    print("="*50 + "\n")
    
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    # Change debug=True to debug=False for production

