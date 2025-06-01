# -*- coding: utf-8 -*-
# optimized_key_detector.py - High Performance Key Detection
import cv2
import numpy as np
from launcher_config import BotConfig
from concurrent.futures import ThreadPoolExecutor

class KeyDetector:
    def __init__(self, templates):
        
        self.templates = templates
        self.key_sequence_area = None
        self.sensitivity = BotConfig.SENSITIVITY
        
        # Pre-compute template pyramids for multi-scale matching
        self.template_pyramids = self._create_template_pyramids()
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _create_template_pyramids(self):
        """Create template pyramids for multi-scale matching."""
        pyramids = {}
        scales = [0.8, 1.0, 1.2]  # Support for scale variations
        
        for key, template in self.templates.items():
            pyramids[key] = []
            for scale in scales:
                if scale != 1.0:
                    h, w = template.shape
                    new_h, new_w = int(h * scale), int(w * scale)
                    scaled_template = cv2.resize(template, (new_w, new_h), 
                                                  interpolation=cv2.INTER_CUBIC)
                else:
                    scaled_template = template.copy()
                pyramids[key].append((scale, scaled_template))
        
        return pyramids
    
    def auto_detect_minigame_area(self, screen):
        """Improve minigame area detection with adaptive algorithms."""
        gray_full = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        
        # Use CLAHE to enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_full = clahe.apply(gray_full)

        # Define ROI with intelligent expansion
        if self.key_sequence_area:
            x0, y0, w0, h0 = self.key_sequence_area
            pad = min(50, max(20, int(min(w0, h0) * 0.2)))  # Dynamic padding
            x1, y1 = max(0, x0 - pad), max(0, y0 - pad)
            x2, y2 = min(gray_full.shape[1], x0 + w0 + pad), min(gray_full.shape[0], y0 + h0 + pad)
            gray = gray_full[y1:y2, x1:x2]
            roi_offset = (x1, y1)
        else:
            gray = gray_full
            roi_offset = (0, 0)

        # Adaptive threshold based on local statistics
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Dynamic threshold adjustment
        if std_brightness < 15:  # Low contrast
            threshold = max(self.sensitivity - 0.15, 0.4)
        elif mean_brightness < 60:  # Dark image
            threshold = max(self.sensitivity - 0.1, 0.5)
        elif mean_brightness > 200:  # Bright image
            threshold = min(self.sensitivity + 0.1, 0.9)
        else:
            threshold = self.sensitivity

        # Multi-scale template matching with early termination
        matches = []
        detected_keys = set()
        
        # Process templates in parallel
        futures = []
        for key in self.templates.keys():
            future = self.executor.submit(self._match_template_multiscale, gray, key, threshold)
            futures.append((key, future))
        
        # Collect results
        for key, future in futures:
            key_matches = future.result()
            if key_matches:
                matches.extend(key_matches)
                detected_keys.add(key)
                
                # Early exit if all keys detected
                if len(detected_keys) == len(self.templates):
                    break

        if not matches:
            return False

        # Apply non-maximum suppression to remove overlapping detections
        matches = self._apply_nms(matches)
        
        # Adjust matches with ROI offset
        adjusted_matches = [(x + roi_offset[0], y + roi_offset[1], w, h, conf) for x, y, w, h, conf in matches]

        if not adjusted_matches:
            return False

        # Compute optimized bounding box
        x_coords = [x for x, y, w, h, conf in adjusted_matches]
        y_coords = [y for x, y, w, h, conf in adjusted_matches]
        w_coords = [w for x, y, w, h, conf in adjusted_matches]
        h_coords = [h for x, y, w, h, conf in adjusted_matches]
        
        x_min = min(x_coords)
        y_min = min(y_coords)
        x_max = max(x + w for x, w in zip(x_coords, w_coords))
        y_max = max(y + h for y, h in zip(y_coords, h_coords))

        # Add margin for stability
        margin = 10
        self.key_sequence_area = (
            max(0, x_min - margin), 
            max(0, y_min - margin),
            min(screen.shape[1] - (x_min - margin), x_max - x_min + 2 * margin),
            min(screen.shape[0] - (y_min - margin), y_max - y_min + 2 * margin)
        )
        
        return True
    
    def _match_template_multiscale(self, gray, key, threshold):
        """Multi-scale template matching for a single key."""
        matches = []
        
        for scale, template in self.template_pyramids[key]:
            h_t, w_t = template.shape
            
            # Skip if template is larger than search area
            if h_t > gray.shape[0] or w_t > gray.shape[1]:
                continue
                
            # Fast template matching with optimized method
            res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            
            # Find peaks above threshold
            locations = np.where(res >= threshold)
            
            for y, x in zip(*locations):
                confidence = res[y, x]
                matches.append((x, y, w_t, h_t, confidence))
        
        return matches
    
    def _apply_nms(self, matches, overlap_threshold=0.3):
        """Non-maximum suppression to remove overlapping detections."""
        if not matches:
            return []
        
        # Sort by confidence (descending)
        matches = sorted(matches, key=lambda x: x[4], reverse=True)
        
        keep = []
        while matches:
            # Keep the highest confidence match
            current = matches.pop(0)
            keep.append(current)
            
            # Remove overlapping matches
            matches = [m for m in matches if self._calculate_iou(current, m) < overlap_threshold]
        
        return keep
    
    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union (IoU)."""
        x1, y1, w1, h1 = box1[:4]
        x2, y2, w2, h2 = box2[:4]
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        union = w1 * h1 + w2 * h2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def detect_key_sequence(self, image):
        """Detect key sequence using improved algorithms."""
        if not self.templates or not self.key_sequence_area:
            return []
        
        try:
            x, y, w, h = self.key_sequence_area
            sequence_region = image[y:y+h, x:x+w]
            
            # Preprocessing for better detection
            gray_region = cv2.cvtColor(sequence_region, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
            gray_region = clahe.apply(gray_region)
            
            # Parallel template matching
            futures = []
            for key in self.templates.keys():
                future = self.executor.submit(self._detect_single_key, gray_region, key)
                futures.append((key, future))
            
            detected_keys = []
            for key, future in futures:
                key_detections = future.result()
                detected_keys.extend(key_detections)
            
            # Sort by x position (left to right)
            detected_keys.sort(key=lambda k: k['x'])
            
            # Apply intelligent filtering
            filtered_keys = self._intelligent_filter(detected_keys)
            
            # Extract sequence
            sequence = [key_info['key'] for key_info in filtered_keys]
            return sequence
            
        except Exception as e:
            return []
    
    def _detect_single_key(self, gray_region, key):
        """Detect a single key using multi-scale approach."""
        detections = []
        
        for scale, template in self.template_pyramids[key]:
            h_t, w_t = template.shape
            
            if h_t > gray_region.shape[0] or w_t > gray_region.shape[1]:
                continue
            
            result = cv2.matchTemplate(gray_region, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= self.sensitivity)
            
            for pt in zip(*locations[::-1]):
                x_pos, y_pos = pt
                confidence = result[y_pos, x_pos]
                
                detections.append({
                    'key': key,
                    'x': x_pos,
                    'y': y_pos,
                    'confidence': confidence,
                    'scale': scale,
                    'width': w_t,
                    'height': h_t
                })
        
        return detections
    
    def _intelligent_filter(self, detected_keys):
        """Intelligent filtering using clustering and confidence weighting."""
        if not detected_keys:
            return []
        
        # Group by approximate x position
        groups = []
        min_distance = BotConfig.MIN_DISTANCE
        
        for key_info in detected_keys:
            placed = False
            for group in groups:
                if any(abs(key_info['x'] - existing['x']) < min_distance for existing in group):
                    group.append(key_info)
                    placed = True
                    break
            
            if not placed:
                groups.append([key_info])
        
        # Select best detection from each group
        filtered_keys = [max(group, key=lambda x: x['confidence']) for group in groups]
        
        return filtered_keys
    
    def get_detection_area(self):
        """Return the detection area."""
        return self.key_sequence_area
    
    def __del__(self):
        """Cleanup thread pool."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)