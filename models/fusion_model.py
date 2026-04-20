class FusionModel:
    def __init__(self):
        # Weights for each modality
        self.weights = {
            'face': 0.4,        # 40% importance
            'fingerprint': 0.4, # 40% importance
            'firebase': 0.2     # 20% importance
        }
        print("✅ Fusion model ready")
    
    def fuse(self, face_result, fingerprint_result, firebase_result):
        """
        Combine all three results
        
        Returns: Dictionary with final decision
        """
        # Get confidence scores
        face_conf = face_result.get('confidence', 0.0) if face_result.get('matched') else 0.0
        finger_conf = fingerprint_result.get('confidence', 0.0) if fingerprint_result.get('matched') else 0.0
        firebase_conf = 1.0 if firebase_result.get('matched') else 0.0
        
        # Calculate weighted score
        total_score = (
            self.weights['face'] * face_conf +
            self.weights['fingerprint'] * finger_conf +
            self.weights['firebase'] * firebase_conf
        )
        
        # Count how many matched
        num_matched = sum([
            face_result.get('matched', False),
            fingerprint_result.get('matched', False),
            firebase_result.get('matched', False)
        ])
        
        # Decision: Need at least 2 matches AND score > 0.6
        verified = (num_matched >= 2) and (total_score >= 0.6)
        
        return {
            'verified': verified,
            'score': round(total_score, 3),
            'matched_count': num_matched,
            'face_matched': face_result.get('matched', False),
            'fingerprint_matched': fingerprint_result.get('matched', False),
            'firebase_matched': firebase_result.get('matched', False)
        }
