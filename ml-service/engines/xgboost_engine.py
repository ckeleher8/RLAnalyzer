import os
import xgboost as xgb
import pandas as pd
import numpy as np
from core.interfaces import BasePredictor

class XGBoostPredictor(BasePredictor):
    def __init__(self, model_path: str = "pitch_evaluator.json"):
        self.model = None
        if os.path.exists(model_path) and os.path.getsize(model_path) > 10:
            try:
                self.model = xgb.XGBRegressor()
                self.model.load_model(model_path)
                print(f"Loaded trained XGBoost model from {model_path}")
            except Exception as e:
                print(f"Warning loading model {model_path}: {e}. Initializing heuristic fallback.")
                self.model = None

    def predict(self, state_vector: pd.DataFrame) -> float:
        if self.model is not None:
            try:
                pred = self.model.predict(state_vector)
                return float(pred[0])
            except Exception:
                pass

        # Robust heuristic fallback: evaluates pitch offensive pressure from ball & car coordinates
        ball_y = float(state_vector.get('pos_y', [0.0])[0]) if 'pos_y' in state_vector else 0.0
        # Positive if ball is on orange side (Y > 0), negative if on blue side (Y < 0)
        norm_val = np.clip(ball_y / 5120.0, -1.0, 1.0) * 0.5
        return float(norm_val)