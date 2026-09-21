import os
import sys
import pytest
from starlette.testclient import TestClient

# Ensure root ml-service is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.ReplayParser import ReplayParser
from logic.FeatureExtractor import PitchStateExtractor
from logic.Analyzer import ThirdManAnalyzer, SupersonicWasteAnalyzer, SmallPadPathingAnalyzer
from evaluators.ActionValueEvaluator import ActionValueEvaluator
from evaluators.MatchReportGenerator import MatchReportGenerator
from engines.xgboost_engine import XGBoostPredictor
from api.main_api import app

@pytest.fixture
def sample_replay_path():
    path = os.path.join(os.path.dirname(__file__), "..", "raw_replays", "3ab6f33e-11e4-42c8-bfce-f8c9485ece35.replay")
    assert os.path.exists(path), f"Sample replay not found at {path}"
    return path

def test_replay_parser(sample_replay_path):
    df, hits, blue, orange, meta, player_map = ReplayParser.parse_match(sample_replay_path)
    
    assert not df.empty
    assert len(blue) > 0
    assert len(orange) > 0
    assert len(hits) > 0
    assert "Map_Name" in meta
    assert "Blue_Score" in meta
    assert "Orange_Score" in meta

def test_feature_extractor(sample_replay_path):
    df, _, blue, orange, _, _ = ReplayParser.parse_match(sample_replay_path)
    feature_df = PitchStateExtractor.extract_frame_features(df, 0, blue, orange)
    
    assert not feature_df.empty
    assert 'pos_x' in feature_df.columns
    assert 'blue_p0_pos_x' in feature_df.columns

def test_heuristic_analyzers(sample_replay_path):
    df, _, blue, orange, _, _ = ReplayParser.parse_match(sample_replay_path)
    
    third_man = ThirdManAnalyzer().analyze(df, blue, orange)
    assert isinstance(third_man, dict)
    
    boost_waste = SupersonicWasteAnalyzer().analyze(df, blue, orange)
    assert isinstance(boost_waste, dict)
    
    pad_pathing = SmallPadPathingAnalyzer().analyze(df, blue, orange)
    assert isinstance(pad_pathing, dict)

def test_match_report_generator(sample_replay_path):
    predictor = XGBoostPredictor()
    evaluator = ActionValueEvaluator(predictor)
    analyzers = [ThirdManAnalyzer(), SupersonicWasteAnalyzer(), SmallPadPathingAnalyzer()]
    generator = MatchReportGenerator(evaluator, analyzers)
    
    report = generator.generate_full_report(sample_replay_path)
    
    assert "Match_ID" in report
    assert "Metadata" in report
    assert "Players" in report
    assert len(report["Players"]) > 0
    assert "ML_Action_Values" in report
    assert "Heuristics" in report

def test_api_endpoints(sample_replay_path):
    client = TestClient(app)
    
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    
    # 2. Upload replay
    with open(sample_replay_path, "rb") as f:
        res = client.post("/api/analyze-replay", files={"file": ("test.replay", f, "application/octet-stream")})
    assert res.status_code == 202
    data = res.json()
    assert "job_id" in data
    job_id = data["job_id"]
    
    # 3. Poll job status
    res = client.get(f"/api/jobs/{job_id}")
    assert res.status_code == 200
    assert res.json()["status"] in ("processing", "completed")
