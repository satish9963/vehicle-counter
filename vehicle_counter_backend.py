"""
Automatic Vehicle Counter - Backend API
FastAPI server for video processing and vehicle detection
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import torch
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import json
import uuid
from datetime import datetime
import threading
from typing import Optional
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Vehicle Counter API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
Path("uploads").mkdir(exist_ok=True)
Path("results").mkdir(exist_ok=True)
Path("models").mkdir(exist_ok=True)

# Load YOLO model
try:
    model = YOLO("yolov8n.pt")  # Nano model for speed
    logger.info("YOLOv8 model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    model = None

# Global state for tracking processing
processing_jobs = {}


class VehicleDetector:
    """Vehicle detection using YOLOv8"""
    
    VEHICLE_CLASSES = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
        8: "boat",
    }
    
    def __init__(self, model):
        self.model = model
        self.conf_threshold = 0.45
    
    def detect_vehicles(self, frame):
        """Detect vehicles in a frame"""
        if self.model is None:
            return [], frame
        
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
                    })
        
        # Draw bounding boxes
        annotated_frame = results[0].plot() if results else frame
        return detections, annotated_frame


class VideoProcessor:
    """Process video files with vehicle detection"""
    
    def __init__(self, detector):
        self.detector = detector
        self.results = []
        self.frame_count = 0
        self.processed_frames = 0
        self.paused = False
    
    def process_video(self, video_path: str, speed_factor: float = 1.0):
        """
        Process video with vehicle detection
        speed_factor: 1.0 = normal, 10.0 = 10x speed
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_skip = int(speed_factor)
        
        frame_idx = 0
        detected_vehicles = {}
        
        while True:
            if self.paused:
                time.sleep(0.1)
                continue
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames based on speed factor
            if frame_idx % frame_skip == 0:
                # Resize for faster processing
                resized_frame = cv2.resize(frame, (640, 480))
                detections, _ = self.detector.detect_vehicles(resized_frame)
                
                timestamp = frame_idx / fps
                detected_vehicles[frame_idx] = {
                    "timestamp": round(timestamp, 2),
                    "detections": detections,
                    "total_count": len(detections),
                }
                
                self.processed_frames += 1
            
            frame_idx += 1
        
        cap.release()
        self.results = detected_vehicles
        return self._generate_report()
    
    def _generate_report(self):
        """Generate summary report"""
        total_detections = sum(d["total_count"] for d in self.results.values())
        vehicle_types = {}
        
        for frame_data in self.results.values():
            for detection in frame_data["detections"]:
                vehicle_type = detection["class"]
                vehicle_types[vehicle_type] = vehicle_types.get(vehicle_type, 0) + 1
        
        return {
            "total_frames": self.frame_count,
            "processed_frames": self.processed_frames,
            "total_vehicles_detected": total_detections,
            "vehicle_breakdown": vehicle_types,
            "detailed_results": self.results,
        }


# Initialize detector
detector = VehicleDetector(model)
processor = VideoProcessor(detector)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file"""
    try:
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise HTTPException(
                status_code=400,
                detail="Only video files (mp4, avi, mov, mkv) are supported"
            )
        
        job_id = str(uuid.uuid4())[:8]
        file_path = f"uploads/{job_id}_{file.filename}"
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get video info
        cap = cv2.VideoCapture(file_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        processing_jobs[job_id] = {
            "status": "uploaded",
            "file_path": file_path,
            "original_filename": file.filename,
            "file_size": len(content),
            "video_info": {
                "frames": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration": frame_count / fps if fps > 0 else 0,
            },
            "created_at": datetime.now().isoformat(),
        }
        
        logger.info(f"Video uploaded: {job_id} - {file.filename}")
        
        return {
            "job_id": job_id,
            "message": "Video uploaded successfully",
            "video_info": processing_jobs[job_id]["video_info"],
        }
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/{job_id}")
async def process_video(job_id: str, speed_factor: float = 1.0, background_tasks: BackgroundTasks = None):
    """Start video processing"""
    try:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = processing_jobs[job_id]
        
        if job["status"] != "uploaded":
            raise HTTPException(status_code=400, detail="Video already processed or invalid state")
        
        job["status"] = "processing"
        job["speed_factor"] = speed_factor
        job["progress"] = 0
        
        # Process in background
        if background_tasks:
            background_tasks.add_task(
                _process_video_task,
                job_id,
                job["file_path"],
                speed_factor
            )
        else:
            # Synchronous processing (for testing)
            result = processor.process_video(job["file_path"], speed_factor)
            job["status"] = "completed"
            job["result"] = result
            job["completed_at"] = datetime.now().isoformat()
        
        return {"job_id": job_id, "status": "processing"}
    
    except Exception as e:
        logger.error(f"Processing error: {e}")
        if job_id in processing_jobs:
            processing_jobs[job_id]["status"] = "failed"
            processing_jobs[job_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


async def _process_video_task(job_id: str, file_path: str, speed_factor: float):
    """Background task for video processing"""
    try:
        logger.info(f"Starting processing: {job_id}")
        result = processor.process_video(file_path, speed_factor)
        processing_jobs[job_id]["result"] = result
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        logger.info(f"Processing completed: {job_id}")
    except Exception as e:
        logger.error(f"Background processing error for {job_id}: {e}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get processing status"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "video_info": job.get("video_info"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at"),
    }


@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """Get processing results"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Processing not completed. Status: {job['status']}"
        )
    
    return {
        "job_id": job_id,
        "result": job.get("result"),
        "completed_at": job.get("completed_at"),
    }


@app.get("/export/{job_id}")
async def export_results(job_id: str, format: str = "csv"):
    """Export results in CSV or JSON format"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed")
    
    result = job.get("result", {})
    filename = f"results/{job_id}_report.{format}"
    
    if format == "csv":
        # Generate CSV report
        with open(filename, "w") as f:
            f.write("Frame,Timestamp,Vehicle_Type,Count,Confidence\n")
            for frame_idx, frame_data in result.get("detailed_results", {}).items():
                timestamp = frame_data.get("timestamp", 0)
                for detection in frame_data.get("detections", []):
                    f.write(
                        f"{frame_idx},{timestamp},{detection['class']},"
                        f"1,{detection['confidence']:.2f}\n"
                    )
    
    elif format == "json":
        # Generate JSON report
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
    
    return FileResponse(filename, media_type="application/octet-stream", filename=f"vehicle_count_report.{format}")


@app.get("/jobs")
async def list_jobs():
    """List all processing jobs"""
    return {
        "total_jobs": len(processing_jobs),
        "jobs": [
            {
                "job_id": job_id,
                "status": job.get("status"),
                "filename": job.get("original_filename"),
                "created_at": job.get("created_at"),
            }
            for job_id, job in processing_jobs.items()
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
