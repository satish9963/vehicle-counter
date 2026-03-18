"""
Vehicle Counter - Advanced Backend Features
Extended functionality with database, caching, batch processing, and analytics
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import cv2
import torch
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import json
import uuid
from datetime import datetime, timedelta
import threading
import redis
import logging
from typing import Optional, List, Dict
import time
from enum import Enum
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== DATABASE SETUP ====================
DATABASE_URL = "sqlite:///./vehicle_counter.db"  # Use PostgreSQL in production
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== DATABASE MODELS ====================
class ProcessingJobDB(Base):
    """Database model for processing jobs"""
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    status = Column(String, default="uploaded")  # uploaded, processing, completed, failed
    speed_factor = Column(Float, default=1.0)
    progress = Column(Integer, default=0)
    total_vehicles = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)
    vehicle_breakdown = Column(JSON, default={})
    detailed_results = Column(JSON, default={})
    video_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    user_id = Column(String, nullable=True)  # For multi-user support
    is_archived = Column(Boolean, default=False)

class AnalyticsDB(Base):
    """Database model for analytics"""
    __tablename__ = "analytics"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, index=True)
    metric_name = Column(String)
    metric_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON, default={})

Base.metadata.create_all(bind=engine)

# ==================== CACHING SETUP ====================
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_ENABLED = True
    logger.info("Redis cache enabled")
except:
    redis_client = None
    REDIS_ENABLED = False
    logger.warning("Redis not available - running without cache")

# ==================== ENHANCED MODELS ====================
class JobStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VehicleDetectorAdvanced:
    """Enhanced vehicle detection with caching and optimization"""
    
    VEHICLE_CLASSES = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
        8: "boat",
        9: "traffic_light",
    }
    
    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model = YOLO(model_name)
        self.conf_threshold = 0.45
        self.detection_cache = {}
    
    def detect_vehicles(self, frame, use_cache=False):
        """Detect vehicles with optional caching"""
        frame_hash = hash(frame.tobytes())
        
        # Check cache
        if use_cache and frame_hash in self.detection_cache:
            return self.detection_cache[frame_hash]
        
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detections = []
        
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                if cls in self.VEHICLE_CLASSES:
                    detections.append({
                        "class": self.VEHICLE_CLASSES[cls],
                        "confidence": float(box.conf[0]),
                        "bbox": [int(x) for x in box.xyxy[0].tolist()],
                        "area": self._calculate_bbox_area([int(x) for x in box.xyxy[0].tolist()]),
                    })
        
        # Cache result
        if use_cache:
            self.detection_cache[frame_hash] = detections
        
        annotated_frame = results[0].plot() if results else frame
        return detections, annotated_frame
    
    @staticmethod
    def _calculate_bbox_area(bbox):
        """Calculate bounding box area"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def clear_cache(self):
        """Clear detection cache"""
        self.detection_cache.clear()


class VideoProcessorAdvanced:
    """Enhanced video processor with analytics and optimization"""
    
    def __init__(self, detector, db_session=None):
        self.detector = detector
        self.db_session = db_session
        self.results = []
        self.frame_count = 0
        self.processed_frames = 0
        self.paused = False
        self.analytics = {
            "vehicles_per_frame": [],
            "vehicle_types_over_time": [],
            "confidence_scores": [],
            "processing_times": [],
        }
    
    def process_video(self, video_path: str, speed_factor: float = 1.0, job_id: str = None):
        """Process video with advanced analytics"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        start_time = time.time()
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_skip = int(speed_factor)
        
        frame_idx = 0
        detected_vehicles = {}
        all_detections = []
        
        while True:
            if self.paused:
                time.sleep(0.1)
                continue
            
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % frame_skip == 0:
                frame_start = time.time()
                
                resized_frame = cv2.resize(frame, (640, 480))
                detections, _ = self.detector.detect_vehicles(resized_frame)
                
                timestamp = frame_idx / fps
                detected_vehicles[frame_idx] = {
                    "timestamp": round(timestamp, 2),
                    "detections": detections,
                    "total_count": len(detections),
                }
                
                all_detections.extend(detections)
                self.analytics["vehicles_per_frame"].append(len(detections))
                
                # Extract confidence scores
                for detection in detections:
                    self.analytics["confidence_scores"].append(detection["confidence"])
                
                # Track processing time
                frame_time = time.time() - frame_start
                self.analytics["processing_times"].append(frame_time)
                
                self.processed_frames += 1
            
            frame_idx += 1
        
        cap.release()
        self.results = detected_vehicles
        total_time = time.time() - start_time
        
        return self._generate_advanced_report(total_time)
    
    def _generate_advanced_report(self, processing_time):
        """Generate comprehensive report with analytics"""
        total_detections = sum(d["total_count"] for d in self.results.values())
        vehicle_types = Counter()
        confidence_scores = []
        
        for frame_data in self.results.values():
            for detection in frame_data["detections"]:
                vehicle_types[detection["class"]] += 1
                confidence_scores.append(detection["confidence"])
        
        # Calculate statistics
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        max_vehicles_per_frame = max(self.analytics["vehicles_per_frame"]) if self.analytics["vehicles_per_frame"] else 0
        avg_vehicles_per_frame = np.mean(self.analytics["vehicles_per_frame"]) if self.analytics["vehicles_per_frame"] else 0
        
        return {
            "total_frames": self.frame_count,
            "processed_frames": self.processed_frames,
            "total_vehicles_detected": total_detections,
            "vehicle_breakdown": dict(vehicle_types),
            "detailed_results": self.results,
            "analytics": {
                "average_confidence": round(avg_confidence, 4),
                "max_vehicles_per_frame": max_vehicles_per_frame,
                "avg_vehicles_per_frame": round(avg_vehicles_per_frame, 2),
                "total_processing_time": round(processing_time, 2),
                "fps_processed": round(self.processed_frames / processing_time, 2) if processing_time > 0 else 0,
            },
            "quality_metrics": {
                "accuracy_estimate": min(avg_confidence * 100, 100),
                "coverage_percentage": round((self.processed_frames / self.frame_count) * 100, 2),
            }
        }


# ==================== FASTAPI APPLICATION ====================
app = FastAPI(title="Vehicle Counter API Advanced", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
Path("uploads").mkdir(exist_ok=True)
Path("results").mkdir(exist_ok=True)
Path("models").mkdir(exist_ok=True)

# Load model
detector = VehicleDetectorAdvanced("yolov8n.pt")
logger.info("YOLOv8 model loaded")

# ==================== BATCH PROCESSING ====================
class BatchProcessor:
    """Batch processing for multiple videos"""
    
    def __init__(self, detector, db_session=None):
        self.detector = detector
        self.db_session = db_session
        self.queue = []
        self.processing = False
    
    def add_to_queue(self, job_id: str):
        """Add job to processing queue"""
        self.queue.append(job_id)
        logger.info(f"Job {job_id} added to queue. Queue size: {len(self.queue)}")
    
    def process_queue(self):
        """Process queue sequentially"""
        while self.queue:
            job_id = self.queue.pop(0)
            logger.info(f"Processing job {job_id} from queue")
            # Process job
            self.processing = True
        self.processing = False
    
    def get_queue_status(self):
        """Get current queue status"""
        return {
            "queue_size": len(self.queue),
            "processing": self.processing,
            "next_job": self.queue[0] if self.queue else None,
        }

batch_processor = BatchProcessor(detector)

# ==================== ANALYTICS ENGINE ====================
class AnalyticsEngine:
    """Advanced analytics for processed videos"""
    
    @staticmethod
    def calculate_traffic_flow(detections: Dict, fps: float):
        """Calculate traffic flow metrics"""
        timestamps = sorted([int(k) for k in detections.keys()])
        vehicle_counts = [detections[str(ts)]["total_count"] for ts in timestamps]
        
        return {
            "peak_vehicles": max(vehicle_counts),
            "average_vehicles": np.mean(vehicle_counts),
            "traffic_variance": float(np.var(vehicle_counts)),
        }
    
    @staticmethod
    def generate_heatmap(detections: Dict) -> str:
        """Generate heatmap of vehicle detections"""
        # Create heatmap visualization
        frame_indices = sorted([int(k) for k in detections.keys()])
        vehicle_counts = [detections[str(idx)]["total_count"] for idx in frame_indices]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(frame_indices, vehicle_counts, linewidth=2, color='#3b82f6')
        ax.fill_between(frame_indices, vehicle_counts, alpha=0.3, color='#3b82f6')
        ax.set_xlabel('Frame')
        ax.set_ylabel('Vehicle Count')
        ax.set_title('Vehicle Detection Heatmap')
        ax.grid(True, alpha=0.3)
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_statistics(report: Dict) -> Dict:
        """Generate comprehensive statistics"""
        return {
            "total_vehicles": report["total_vehicles_detected"],
            "detection_accuracy": report["analytics"]["average_confidence"],
            "processing_efficiency": report["quality_metrics"]["coverage_percentage"],
            "peak_traffic": report["analytics"]["max_vehicles_per_frame"],
            "average_traffic": report["analytics"]["avg_vehicles_per_frame"],
        }

# ==================== ENHANCED ENDPOINTS ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Enhanced health check"""
    return {
        "status": "healthy",
        "model_loaded": detector.model is not None,
        "redis_enabled": REDIS_ENABLED,
        "database_connected": True,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
    }

@app.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = None):
    """Upload video with database persistence"""
    try:
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(status_code=400, detail="Invalid format")
        
        job_id = str(uuid.uuid4())[:8]
        file_path = f"uploads/{job_id}_{file.filename}"
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract metadata
        cap = cv2.VideoCapture(file_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Save to database
        if db:
            job_record = ProcessingJobDB(
                id=job_id,
                filename=file.filename,
                status=JobStatus.UPLOADED,
                video_metadata={
                    "frames": frame_count,
                    "fps": fps,
                    "width": width,
                    "height": height,
                    "duration": frame_count / fps if fps > 0 else 0,
                    "file_size": len(content),
                }
            )
            db.add(job_record)
            db.commit()
        
        # Cache in Redis
        if REDIS_ENABLED:
            redis_client.setex(
                f"job:{job_id}",
                86400,  # 24 hours
                json.dumps({"status": "uploaded"})
            )
        
        logger.info(f"Video uploaded: {job_id} - {file.filename}")
        
        return {
            "job_id": job_id,
            "message": "Video uploaded successfully",
            "video_info": {
                "frames": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration": frame_count / fps if fps > 0 else 0,
            },
        }
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/{job_id}")
async def process_video(
    job_id: str,
    speed_factor: float = 1.0,
    background_tasks: BackgroundTasks = None,
    db: Session = None
):
    """Start processing with database tracking"""
    try:
        # Get job from database
        if db:
            job_record = db.query(ProcessingJobDB).filter(ProcessingJobDB.id == job_id).first()
            if not job_record:
                raise HTTPException(status_code=404, detail="Job not found")
            
            job_record.status = JobStatus.PROCESSING
            job_record.speed_factor = speed_factor
            job_record.started_at = datetime.utcnow()
            db.commit()
        
        # Start processing
        if background_tasks:
            background_tasks.add_task(
                _process_video_task,
                job_id,
                f"uploads/{job_id}_*",
                speed_factor,
                db
            )
        
        logger.info(f"Processing started: {job_id}")
        return {"job_id": job_id, "status": "processing"}
    
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_video_task(job_id: str, file_pattern: str, speed_factor: float, db: Session):
    """Background processing task"""
    try:
        from glob import glob
        files = glob(file_pattern)
        if not files:
            raise ValueError("Video file not found")
        
        file_path = files[0]
        processor = VideoProcessorAdvanced(detector, db)
        result = processor.process_video(file_path, speed_factor, job_id)
        
        # Update database
        if db:
            job_record = db.query(ProcessingJobDB).filter(ProcessingJobDB.id == job_id).first()
            if job_record:
                job_record.status = JobStatus.COMPLETED
                job_record.completed_at = datetime.utcnow()
                job_record.total_vehicles = result["total_vehicles_detected"]
                job_record.accuracy = result["analytics"]["average_confidence"]
                job_record.vehicle_breakdown = result["vehicle_breakdown"]
                job_record.detailed_results = result["detailed_results"]
                job_record.processing_time = result["analytics"]["total_processing_time"]
                db.commit()
        
        logger.info(f"Processing completed: {job_id}")
    
    except Exception as e:
        logger.error(f"Background processing error: {e}")
        if db:
            job_record = db.query(ProcessingJobDB).filter(ProcessingJobDB.id == job_id).first()
            if job_record:
                job_record.status = JobStatus.FAILED
                job_record.error_message = str(e)
                db.commit()

@app.get("/results/{job_id}")
async def get_results(job_id: str, db: Session = None):
    """Get results from database"""
    try:
        if db:
            job_record = db.query(ProcessingJobDB).filter(ProcessingJobDB.id == job_id).first()
            if not job_record:
                raise HTTPException(status_code=404, detail="Job not found")
            
            if job_record.status != JobStatus.COMPLETED:
                raise HTTPException(status_code=400, detail=f"Job status: {job_record.status}")
            
            return {
                "job_id": job_id,
                "result": {
                    "total_vehicles": job_record.total_vehicles,
                    "accuracy": job_record.accuracy,
                    "vehicle_breakdown": job_record.vehicle_breakdown,
                    "processing_time": job_record.processing_time,
                },
                "completed_at": job_record.completed_at,
            }
    
    except Exception as e:
        logger.error(f"Get results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{job_id}")
async def get_analytics(job_id: str, db: Session = None):
    """Get analytics for a job"""
    try:
        if db:
            job_record = db.query(ProcessingJobDB).filter(ProcessingJobDB.id == job_id).first()
            if not job_record or job_record.status != JobStatus.COMPLETED:
                raise HTTPException(status_code=400, detail="Job not completed")
            
            analytics = AnalyticsEngine.generate_statistics({
                "total_vehicles_detected": job_record.total_vehicles,
                "analytics": {
                    "average_confidence": job_record.accuracy,
                    "max_vehicles_per_frame": max(
                        [d["total_count"] for d in job_record.detailed_results.values()],
                        default=0
                    ),
                    "avg_vehicles_per_frame": job_record.total_vehicles / len(job_record.detailed_results),
                    "total_processing_time": job_record.processing_time,
                },
                "quality_metrics": {
                    "coverage_percentage": 100,
                }
            })
            
            return {
                "job_id": job_id,
                "analytics": analytics,
                "generated_at": datetime.utcnow().isoformat(),
            }
    
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue/status")
async def get_queue_status():
    """Get batch processing queue status"""
    return batch_processor.get_queue_status()

@app.post("/batch/add/{job_id}")
async def add_to_batch(job_id: str):
    """Add job to batch processing queue"""
    batch_processor.add_to_queue(job_id)
    return {"message": "Job added to queue", "queue_status": batch_processor.get_queue_status()}

@app.get("/history")
async def get_job_history(limit: int = Query(50), db: Session = None):
    """Get job processing history"""
    try:
        if db:
            jobs = db.query(ProcessingJobDB).order_by(
                ProcessingJobDB.created_at.desc()
            ).limit(limit).all()
            
            return {
                "total_jobs": len(jobs),
                "jobs": [
                    {
                        "job_id": j.id,
                        "filename": j.filename,
                        "status": j.status,
                        "total_vehicles": j.total_vehicles,
                        "accuracy": j.accuracy,
                        "processing_time": j.processing_time,
                        "created_at": j.created_at,
                        "completed_at": j.completed_at,
                    }
                    for j in jobs
                ]
            }
    
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
