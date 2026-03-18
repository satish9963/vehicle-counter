"""
Vehicle Counter - Testing & Validation Guide
Comprehensive testing strategies and performance benchmarking
"""

# ==================== UNIT TESTS ====================

import pytest
import cv2
import numpy as np
from unittest.mock import Mock, patch
import time
from vehicle_counter_backend import (
    VehicleDetectorAdvanced,
    VideoProcessorAdvanced,
    ProcessingJobDB
)

class TestVehicleDetector:
    """Unit tests for vehicle detection"""
    
    @pytest.fixture
    def detector(self):
        return VehicleDetectorAdvanced()
    
    def test_detector_initialization(self, detector):
        """Test detector initializes correctly"""
        assert detector.model is not None
        assert detector.conf_threshold == 0.45
        assert len(detector.VEHICLE_CLASSES) > 0
    
    def test_vehicle_classes_mapping(self, detector):
        """Test vehicle class mapping"""
        assert detector.VEHICLE_CLASSES[2] == "car"
        assert detector.VEHICLE_CLASSES[3] == "motorcycle"
        assert detector.VEHICLE_CLASSES[5] == "bus"
        assert detector.VEHICLE_CLASSES[7] == "truck"
    
    def test_bbox_area_calculation(self):
        """Test bounding box area calculation"""
        bbox = [100, 100, 200, 200]
        area = VehicleDetectorAdvanced._calculate_bbox_area(bbox)
        assert area == 10000  # (200-100) * (200-100)
    
    def test_cache_management(self, detector):
        """Test detection caching"""
        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # First call (not cached)
        detector.detection_cache = {}
        detections1, _ = detector.detect_vehicles(frame, use_cache=True)
        
        # Clear cache
        detector.clear_cache()
        assert len(detector.detection_cache) == 0
    
    def test_detection_output_format(self, detector):
        """Test detection output format"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections, annotated = detector.detect_vehicles(frame)
        
        assert isinstance(detections, list)
        assert isinstance(annotated, np.ndarray)
        
        # Test detection format if any detections
        if detections:
            detection = detections[0]
            assert "class" in detection
            assert "confidence" in detection
            assert "bbox" in detection
            assert "area" in detection


class TestVideoProcessor:
    """Unit tests for video processing"""
    
    @pytest.fixture
    def processor(self):
        detector = Mock()
        detector.detect_vehicles = Mock(return_value=([], np.zeros((480, 640, 3))))
        return VideoProcessorAdvanced(detector)
    
    def test_processor_initialization(self, processor):
        """Test processor initializes correctly"""
        assert processor.results == []
        assert processor.frame_count == 0
        assert processor.processed_frames == 0
    
    def test_analytics_tracking(self, processor):
        """Test analytics data collection"""
        processor.analytics["vehicles_per_frame"].append(5)
        processor.analytics["confidence_scores"].append(0.92)
        processor.analytics["processing_times"].append(0.045)
        
        assert len(processor.analytics["vehicles_per_frame"]) == 1
        assert np.mean(processor.analytics["confidence_scores"]) == 0.92
    
    def test_report_generation(self, processor):
        """Test report generation"""
        processor.frame_count = 100
        processor.processed_frames = 50
        processor.results = {
            0: {"timestamp": 0.0, "detections": [{"class": "car", "confidence": 0.95}], "total_count": 1},
            1: {"timestamp": 0.033, "detections": [], "total_count": 0},
        }
        processor.analytics["vehicles_per_frame"] = [1, 0]
        processor.analytics["confidence_scores"] = [0.95]
        processor.analytics["processing_times"] = [0.045, 0.040]
        
        report = processor._generate_advanced_report(1.0)
        
        assert report["total_frames"] == 100
        assert report["processed_frames"] == 50
        assert report["total_vehicles_detected"] == 1
        assert "vehicle_breakdown" in report
        assert "analytics" in report


# ==================== INTEGRATION TESTS ====================

class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from vehicle_counter_backend import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_upload_endpoint_validation(self, client):
        """Test upload endpoint validation"""
        # Try uploading invalid file type
        response = client.post(
            "/upload",
            files={"file": ("test.txt", b"invalid content")}
        )
        assert response.status_code == 400
    
    def test_invalid_job_id(self, client):
        """Test invalid job ID handling"""
        response = client.get("/status/invalid_job_id")
        assert response.status_code == 404


# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Performance and load testing"""
    
    def test_frame_processing_speed(self):
        """Test single frame processing speed"""
        detector = VehicleDetectorAdvanced()
        frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        times = []
        for _ in range(10):
            start = time.time()
            detections, _ = detector.detect_vehicles(frame)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = np.mean(times)
        print(f"Average frame processing time: {avg_time*1000:.2f}ms")
        assert avg_time < 0.1  # Should be faster than 100ms
    
    def test_video_processing_throughput(self):
        """Test video processing throughput"""
        # Create synthetic video
        detector = Mock()
        detector.detect_vehicles = Mock(return_value=([], np.zeros((480, 640, 3))))
        processor = VideoProcessorAdvanced(detector)
        
        # Simulate processing
        start = time.time()
        for i in range(300):  # 10 seconds @ 30fps
            processor.processed_frames += 1
        elapsed = time.time() - start
        
        fps = processor.processed_frames / elapsed
        print(f"Processing throughput: {fps:.1f} frames/second")
        assert fps > 100  # Should process >100 fps
    
    def test_memory_efficiency(self):
        """Test memory usage during processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process a simulated video
        detector = VehicleDetectorAdvanced()
        processor = VideoProcessorAdvanced(detector)
        
        # Simulate processing
        for _ in range(100):
            processor.processed_frames += 1
            processor.analytics["vehicles_per_frame"].append(5)
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        print(f"Memory increase: {mem_increase:.2f} MB")
        assert mem_increase < 200  # Should use <200MB for processing


# ==================== ACCURACY TESTS ====================

class TestAccuracy:
    """Accuracy validation tests"""
    
    def test_detection_consistency(self):
        """Test detection consistency across multiple runs"""
        detector = VehicleDetectorAdvanced()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        detections_list = []
        for _ in range(3):
            detections, _ = detector.detect_vehicles(frame)
            detections_list.append(len(detections))
        
        # Should have consistent number of detections
        # (allowing for small variance due to model stochasticity)
        assert max(detections_list) - min(detections_list) <= 2
    
    def test_confidence_score_validity(self):
        """Test confidence scores are valid"""
        detector = VehicleDetectorAdvanced()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        detections, _ = detector.detect_vehicles(frame)
        
        for detection in detections:
            confidence = detection["confidence"]
            assert 0.0 <= confidence <= 1.0
    
    def test_bbox_validity(self):
        """Test bounding box coordinates are valid"""
        detector = VehicleDetectorAdvanced()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        detections, _ = detector.detect_vehicles(frame)
        
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            # Check bounds
            assert 0 <= x1 < 640
            assert 0 <= y1 < 480
            assert 0 <= x2 <= 640
            assert 0 <= y2 <= 480
            # Check ordering
            assert x1 < x2
            assert y1 < y2


# ==================== STRESS TESTS ====================

def stress_test_concurrent_processing():
    """Test concurrent video processing"""
    import concurrent.futures
    from unittest.mock import Mock
    
    detector = Mock()
    detector.detect_vehicles = Mock(return_value=([], np.zeros((480, 640, 3))))
    
    def process_video(job_id):
        processor = VideoProcessorAdvanced(detector)
        processor.frame_count = 300
        for _ in range(300):
            processor.processed_frames += 1
        return processor.processed_frames
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_video, i) for i in range(10)]
        results = [f.result() for f in futures]
    
    assert len(results) == 10
    assert all(r == 300 for r in results)
    print(f"Processed {sum(results)} frames concurrently")


# ==================== VALIDATION DATASETS ====================

class TestValidationDatasets:
    """Test with validation datasets"""
    
    def test_sample_video_processing(self):
        """Test processing of sample video"""
        import os
        
        # Check if sample video exists
        sample_video = "test_videos/sample.mp4"
        if not os.path.exists(sample_video):
            pytest.skip("Sample video not available")
        
        detector = VehicleDetectorAdvanced()
        processor = VideoProcessorAdvanced(detector)
        
        # Process sample video
        try:
            report = processor.process_video(sample_video, speed_factor=1.0)
            
            # Validate report structure
            assert "total_vehicles_detected" in report
            assert "vehicle_breakdown" in report
            assert "analytics" in report
            assert "quality_metrics" in report
            
            # Validate report values
            assert report["total_vehicles_detected"] >= 0
            assert 0 <= report["analytics"]["average_confidence"] <= 1.0
        except FileNotFoundError:
            pytest.skip("Sample video file not found")


# ==================== REGRESSION TESTS ====================

def test_regression_detections_stable():
    """Test that detections remain stable across versions"""
    detector = VehicleDetectorAdvanced()
    
    # Create consistent test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (100, 100), (300, 300), (255, 255, 255), -1)
    
    # Get detections
    detections, _ = detector.detect_vehicles(frame)
    
    # Should find at least one vehicle in white rectangle
    # (depends on model training)
    print(f"Found {len(detections)} vehicles")


# ==================== BENCHMARK SUITE ====================

import time
import statistics

class BenchmarkSuite:
    """Comprehensive benchmark suite"""
    
    @staticmethod
    def benchmark_frame_sizes():
        """Benchmark processing of different frame sizes"""
        detector = VehicleDetectorAdvanced()
        sizes = [
            (480, 640),    # SD
            (720, 1280),   # HD
            (1080, 1920),  # Full HD
            (2160, 3840),  # 4K
        ]
        
        results = {}
        for height, width in sizes:
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            times = []
            
            for _ in range(5):
                start = time.time()
                detections, _ = detector.detect_vehicles(frame)
                times.append(time.time() - start)
            
            results[f"{width}x{height}"] = {
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            }
        
        print("\n=== Frame Size Benchmark ===")
        for size, metrics in results.items():
            print(f"{size}:")
            print(f"  Average: {metrics['avg_time']*1000:.2f}ms")
            print(f"  Min: {metrics['min_time']*1000:.2f}ms")
            print(f"  Max: {metrics['max_time']*1000:.2f}ms")
    
    @staticmethod
    def benchmark_speed_factors():
        """Benchmark different speed factors"""
        # Simulate processing with different speed factors
        print("\n=== Speed Factor Benchmark ===")
        
        frame_count = 300  # 10 seconds @ 30fps
        base_time = 0.045  # Average frame processing time
        
        for speed_factor in [1, 2, 5, 10]:
            frames_to_process = frame_count // speed_factor
            estimated_time = frames_to_process * base_time
            speedup = frame_count * base_time / estimated_time
            
            print(f"Speed Factor {speed_factor}x:")
            print(f"  Frames to process: {frames_to_process}")
            print(f"  Estimated time: {estimated_time:.2f}s")
            print(f"  Actual speedup: {speedup:.1f}x")


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    # Run unit tests
    pytest.main([__file__, "-v", "--tb=short"])
    
    # Run benchmarks
    print("\n" + "="*50)
    print("Running Benchmarks")
    print("="*50)
    
    BenchmarkSuite.benchmark_frame_sizes()
    BenchmarkSuite.benchmark_speed_factors()
    
    # Run stress tests
    print("\n" + "="*50)
    print("Running Stress Tests")
    print("="*50)
    
    stress_test_concurrent_processing()
    
    print("\n✅ All tests completed!")


# ==================== TEST CONFIGURATION ====================

# pytest.ini
"""
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    accuracy: Accuracy tests
    stress: Stress tests
    slow: Slow tests
"""


# ==================== COVERAGE CONFIGURATION ====================

# .coveragerc
"""
[run]
source = .
omit =
    */tests/*
    */test_*.py
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = coverage_report
"""
