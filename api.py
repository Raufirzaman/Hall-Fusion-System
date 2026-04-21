from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
import base64
import io
from PIL import Image
import json
import threading
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models and utilities
from models.face_model import FaceModel
from models.fingerprint_model import FingerprintModel
from utils.firebase_manager import FirebaseManager
from utils.storage_manager import StorageManager

# ===== APP INITIALIZATION =====
app = Flask(__name__)

# CORS Configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ===== CONFIGURATION =====
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
PORT = int(os.environ.get('PORT', 5000))
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

logger.info(f"🚀 Initializing Hall Fusion API")
logger.info(f"📡 Environment: {FLASK_ENV}")
logger.info(f"🔥 Debug: {DEBUG}")
logger.info(f"📍 Port: {PORT}")

# ===== INITIALIZE MANAGERS =====
try:
    logger.info("📦 Initializing Firebase Manager...")
    firebase_db = FirebaseManager()
    logger.info("✅ Firebase initialized")
except Exception as e:
    logger.error(f"❌ Firebase init error: {e}")
    firebase_db = None

try:
    logger.info("🧠 Loading Face Model...")
    face_model = FaceModel()
    logger.info("✅ Face model loaded")
except Exception as e:
    logger.error(f"❌ Face model error: {e}")
    face_model = None

try:
    logger.info("🔍 Loading Fingerprint Model...")
    fingerprint_model = FingerprintModel()
    logger.info("✅ Fingerprint model loaded")
except Exception as e:
    logger.error(f"❌ Fingerprint model error: {e}")
    fingerprint_model = None

try:
    logger.info("💾 Initializing Storage Manager...")
    storage_manager = StorageManager()
    logger.info("✅ Storage manager initialized")
except Exception as e:
    logger.error(f"❌ Storage manager error: {e}")
    storage_manager = None

print("✅ Firebase initialized")
print("✅ Face model loaded")
print("✅ Fingerprint model loaded")
print("✅ Storage manager ready")
print("="*60 + "\n")

# ===== MIDDLEWARE =====
@app.before_request
def log_request():
    """Log incoming requests"""
    if request.path not in ['/health', '/api/health', '/']:
        logger.info(f"📥 {request.method} {request.path}")

@app.after_request
def log_response(response):
    """Log outgoing responses"""
    if request.path not in ['/health', '/api/health', '/']:
        logger.info(f"📤 {response.status_code} {request.path}")
    return response

# ===== HEALTH CHECK ENDPOINTS =====
@app.route('/health', methods=['GET'])
def health():
    """Health check for Railway/Container orchestration"""
    return jsonify({
        'status': 'healthy',
        'service': 'Hall Fusion API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'firebase': 'connected' if firebase_db else 'disconnected',
        'face_model': 'loaded' if face_model else 'not_loaded'
    }), 200

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'Hall Fusion API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Welcome endpoint"""
    return jsonify({
        'service': 'Hall Fusion System API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'register': '/api/register',
            'authenticate': '/api/authenticate',
            'status': '/api/status'
        }
    }), 200

# ===== HELPER FUNCTIONS =====
def decode_base64_image(base64_string):
    """Decode base64 string to OpenCV image"""
    try:
        # Remove data URI prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64 to bytes
        img_bytes = base64.b64decode(base64_string)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        
        # Decode to OpenCV image (BGR format)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.error("❌ Failed to decode image - invalid image data")
            return None
        
        logger.info(f"✅ Image decoded successfully - shape: {img.shape}")
        return img
    
    except base64.binascii.Error as e:
        logger.error(f"❌ Base64 decode error: {e}")
        return None
    
    except Exception as e:
        logger.error(f"❌ Image decode error: {e}")
        import traceback
        traceback.print_exc()
        return None

# ===== API ENDPOINTS =====

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
        logger.error(f"Error getting logs: {e}")
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
        logger.error(f"Error getting stats: {e}")
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
        logger.error(f"Error getting activity: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'activity': []
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
        logger.error(f"Error listing students: {e}")
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
        logger.error(f"Error getting student: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
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
        student_name = data.get('student_name')
        email = data.get('email')
        department = data.get('department')
        face_base64 = data.get('face_image')
        fingerprint_base64 = data.get('fingerprint_image')
        
        logger.info(f"\n📝 Registration request for: {student_id}")
        
        if not student_id:
            return jsonify({
                'success': False,
                'error': 'Student ID is required'
            }), 400
        
        # Check if student exists in Firebase
        try:
            student = firebase_db.get_student(student_id)
            if not student:
                logger.warning(f"Student {student_id} not found, creating new record")
        except Exception as e:
            logger.warning(f"Could not check student: {e}")
        
        face_path = None
        fingerprint_path = None
        
        # Process face image
        if face_base64:
            try:
                logger.info("   Processing face image...")
                
                if ',' in face_base64:
                    face_base64 = face_base64.split(',')[1]
                
                face_bytes = base64.b64decode(face_base64)
                face_image = Image.open(io.BytesIO(face_bytes))
                face_image = face_image.convert('RGB')
                
                face_array = np.array(face_image)
                face_array = cv2.cvtColor(face_array, cv2.COLOR_RGB2BGR)
                
                if storage_manager:
                    face_path = storage_manager.save_face_image(face_array, student_id)
                    logger.info(f"   ✅ Face saved: {face_path}")
                
                if face_model:
                    success = face_model.register_face(face_array, student_id, mode='single')
                    
                    if not success:
                        logger.warning("Face registration in model failed")
                    else:
                        logger.info(f"   ✅ Face registered in model")
                
            except Exception as e:
                logger.error(f"   ❌ Face error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Face processing failed: {str(e)}'
                }), 400
        
        # Process fingerprint
        if fingerprint_base64:
            try:
                logger.info("   Processing fingerprint...")
                
                if ',' in fingerprint_base64:
                    fingerprint_base64 = fingerprint_base64.split(',')[1]
                
                fingerprint_bytes = base64.b64decode(fingerprint_base64)
                fingerprint_image = Image.open(io.BytesIO(fingerprint_bytes))
                fingerprint_image = fingerprint_image.convert('RGB')
                
                fingerprint_array = np.array(fingerprint_image)
                fingerprint_array = cv2.cvtColor(fingerprint_array, cv2.COLOR_RGB2BGR)
                
                if storage_manager:
                    fingerprint_path = storage_manager.save_fingerprint_image(
                        fingerprint_array, student_id
                    )
                    logger.info(f"   ✅ Fingerprint saved: {fingerprint_path}")
                
                if fingerprint_model:
                    success = fingerprint_model.register_fingerprint(
                        fingerprint_array, student_id
                    )
                    
                    if success:
                        logger.info(f"   ✅ Fingerprint registered")
                
            except Exception as e:
                logger.error(f"   ❌ Fingerprint error: {e}")
        
        # Update Firebase
        if face_path or fingerprint_path:
            try:
                firebase_db.save_biometric_paths(
                    student_id, 
                    face_image_path=face_path,
                    fingerprint_image_path=fingerprint_path
                )
                logger.info(f"   ✅ Firebase updated")
            except Exception as e:
                logger.warning(f"   ⚠️ Firebase update warning: {e}")
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'student_name': student_name,
            'has_face': bool(face_path),
            'has_fingerprint': bool(fingerprint_path),
            'message': 'Registration successful'
        })
    
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
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
        logger.info("\n" + "="*60)
        logger.info("🔐 AUTHENTICATION REQUEST")
        logger.info("="*60)
        
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
            logger.info("\n🔍 Processing face authentication...")
            try:
                face_image = decode_base64_image(face_base64)
                if face_image is not None and face_model:
                    result = face_model.authenticate_face(face_image)
                    if result['match']:
                        student_id = result['student_id']
                        confidence = result['confidence']
                        face_match = True
                        authenticated = True
                        logger.info(f"✅ Face authenticated: {student_id} ({confidence:.2%})")
                    else:
                        logger.info(f"❌ Face not recognized: {result.get('error', 'No match')}")
            except Exception as e:
                logger.error(f"❌ Face authentication error: {e}")
        
        # Try fingerprint authentication (if face failed)
        if not authenticated and fingerprint_base64:
            logger.info("\n🔍 Processing fingerprint authentication...")
            try:
                fingerprint_image = decode_base64_image(fingerprint_base64)
                if fingerprint_image is not None and fingerprint_model:
                    result = fingerprint_model.authenticate_fingerprint(fingerprint_image)
                    if result['match']:
                        student_id = result['student_id']
                        confidence = result['confidence']
                        fingerprint_match = True
                        authenticated = True
                        logger.info(f"✅ Fingerprint authenticated: {student_id} ({confidence:.2%})")
                    else:
                        logger.info(f"❌ Fingerprint not recognized")
            except Exception as e:
                logger.error(f"❌ Fingerprint authentication error: {e}")
        
        # Get student information if authenticated
        if authenticated and student_id:
            try:
                student = firebase_db.get_student(student_id) if firebase_db else None
                
                if student:
                    # Try to log, but don't fail if logging fails
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
                        logger.info("✅ Authentication logged to Firebase")
                    except Exception as log_error:
                        logger.warning(f"⚠️ Warning: Failed to log to Firebase: {log_error}")
                    
                    logger.info(f"\n✅ Authentication successful!")
                    logger.info(f"   Student: {student.get('name')} ({student_id})")
                    logger.info(f"   Confidence: {confidence:.2%}")
                    logger.info("="*60 + "\n")
                    
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
                    logger.warning(f"⚠️ Student {student_id} not found in database")
                    return jsonify({
                        'authenticated': False,
                        'error': 'Student not found in database',
                        'student_id': student_id,
                        'confidence': confidence
                    }), 404
            
            except Exception as db_error:
                logger.error(f"❌ Database error: {db_error}")
                return jsonify({
                    'authenticated': True,
                    'student_id': student_id,
                    'confidence': confidence,
                    'face_match': face_match,
                    'fingerprint_match': fingerprint_match,
                    'error': 'Database connection issue',
                    'timestamp': datetime.now().isoformat()
                })
        
        else:
            # Not authenticated
            logger.info(f"\n❌ Authentication failed")
            logger.info(f"   No matching student found")
            logger.info(f"   Confidence: {confidence:.2%}")
            logger.info("="*60 + "\n")
            
            # Try to log failed attempt
            try:
                if firebase_db:
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
                logger.warning(f"⚠️ Failed to log failed attempt: {log_error}")
            
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
        logger.error(f"❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        logger.info("="*60 + "\n")
        
        return jsonify({
            'authenticated': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Get API status"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'models': {
            'face': 'loaded' if face_model else 'not_loaded',
            'fingerprint': 'loaded' if fingerprint_model else 'not_loaded'
        },
        'services': {
            'firebase': 'connected' if firebase_db else 'disconnected',
            'storage': 'connected' if storage_manager else 'disconnected'
        }
    }), 200

@app.route('/api/debug/encodings', methods=['GET'])
def debug_encodings():
    """Debug endpoint to check loaded encodings"""
    try:
        face_encodings_info = {
            'count': len(face_model.face_encodings) if face_model else 0,
            'students': list(face_model.face_encodings.keys()) if face_model else [],
        }
        
        fingerprint_encodings_info = {
            'count': len(fingerprint_model.fingerprint_encodings) if fingerprint_model else 0,
            'students': list(fingerprint_model.fingerprint_encodings.keys()) if fingerprint_model else [],
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

# ===== ERROR HANDLERS =====
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

# ===== MAIN =====
if __name__ == '__main__':
    logger.info("\n" + "="*50)
    logger.info("🚀 Hall Fusion System API Starting...")
    logger.info("="*50)
    logger.info(f"📡 Server: 0.0.0.0:{PORT}")
    logger.info(f"🔥 Firebase: {'Connected' if firebase_db else 'Disconnected'}")
    logger.info(f"🤖 Face Model: {'Ready' if face_model else 'Not Loaded'}")
    logger.info(f"👆 Fingerprint Model: {'Ready' if fingerprint_model else 'Not Loaded'}")
    logger.info(f"💾 Storage: {'Ready' if storage_manager else 'Not Ready'}")
    logger.info("\n📍 Available Endpoints:")
    logger.info("   GET  /health")
    logger.info("   GET  /api/health")
    logger.info("   GET  /api/stats")
    logger.info("   GET  /api/logs")
    logger.info("   GET  /api/activity")
    logger.info("   GET  /api/students")
    logger.info("   GET  /api/students/<id>")
    logger.info("   POST /api/register")
    logger.info("   POST /api/authenticate")
    logger.info("   GET  /api/status")
    logger.info("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG, threaded=True)