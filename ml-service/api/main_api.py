import os
import sys
import uuid
import shutil
import asyncio
import time
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Ensure root ml-service is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.xgboost_engine import XGBoostPredictor
from evaluators.ActionValueEvaluator import ActionValueEvaluator
from evaluators.MatchReportGenerator import MatchReportGenerator
from logic.Analyzer import ThirdManAnalyzer, SupersonicWasteAnalyzer, SmallPadPathingAnalyzer

# Global in-memory job store
JOB_STORE: Dict[str, Dict[str, Any]] = {}
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp_replays"))
os.makedirs(TEMP_DIR, exist_ok=True)

# 1. Lifecycle Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Booting Rocket League ML Engine...")
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pitch_evaluator.json"))
    app.state.predictor = XGBoostPredictor(model_path)
    os.makedirs(TEMP_DIR, exist_ok=True)
    yield
    print("Shutting down ML Engine...")
    if hasattr(app.state, 'predictor'):
        del app.state.predictor

app = FastAPI(title="RL Replay ML Analysis Engine", lifespan=lifespan)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Dependency Injection
def get_report_generator(request: Request) -> MatchReportGenerator:
    predictor = getattr(request.app.state, 'predictor', None)
    if predictor is None:
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pitch_evaluator.json"))
        predictor = XGBoostPredictor(model_path)
    evaluator = ActionValueEvaluator(predictor)
    analyzers = [ThirdManAnalyzer(), SupersonicWasteAnalyzer(), SmallPadPathingAnalyzer()]
    return MatchReportGenerator(evaluator, analyzers)

# 3. Background Task Worker
async def process_match_background(
    job_id: str, 
    filepath: str, 
    blue_players: Optional[list], 
    orange_players: Optional[list], 
    generator: MatchReportGenerator
):
    try:
        print(f"Executing ML Analysis for Job {job_id} on {filepath}...")
        report = await asyncio.to_thread(
            generator.generate_full_report,
            filepath,
            blue_players,
            orange_players
        )
        
        JOB_STORE[job_id] = {
            "status": "completed",
            "report": report,
            "message": "Analysis finished successfully.",
            "completed_at": time.time()
        }
        print(f"Job {job_id} Completed Successfully!")
        
    except Exception as e:
        print(f"Job {job_id} Failed: {e}")
        JOB_STORE[job_id] = {
            "status": "failed",
            "report": None,
            "message": str(e),
            "completed_at": time.time()
        }
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

# 4. Endpoints
@app.post("/api/analyze-replay", status_code=202)
async def analyze_replay(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    blue_players: Optional[str] = Form(default=None),
    orange_players: Optional[str] = Form(default=None),
    generator: MatchReportGenerator = Depends(get_report_generator)
):
    """
    Receives the .replay file and queues asynchronous ML analysis.
    """
    job_id = str(uuid.uuid4())
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_filename = os.path.join(TEMP_DIR, f"{job_id}.replay")

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        blue_list = [p.strip() for p in blue_players.split(",")] if blue_players else None
        orange_list = [p.strip() for p in orange_players.split(",")] if orange_players else None

        JOB_STORE[job_id] = {
            "status": "processing",
            "report": None,
            "message": "Replay processing initiated.",
            "started_at": time.time()
        }

        background_tasks.add_task(
            process_match_background,
            job_id,
            temp_filename,
            blue_list,
            orange_list,
            generator
        )

        return {
            "status": "processing",
            "job_id": job_id,
            "message": "Replay accepted for analysis."
        }

    except Exception as e:
        if os.path.exists(temp_filename):
            try: os.remove(temp_filename)
            except: pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Returns the processing status and results for a submitted replay job.
    """
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    job = JOB_STORE[job_id]
    return {
        "status": job.get("status", "processing"),
        "job_id": job_id,
        "message": job.get("message"),
        "report": job.get("report")
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "RL ML Engine",
        "active_jobs": len(JOB_STORE)
    }