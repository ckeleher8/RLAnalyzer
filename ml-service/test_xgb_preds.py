import os
import pandas as pd
import numpy as np
from logic.ReplayParser import ReplayParser
from logic.FeatureExtractor import PitchStateExtractor
from engines.xgboost_engine import XGBoostPredictor

predictor = XGBoostPredictor("pitch_evaluator.json")
df, hits, blue, orange, meta, player_meta = ReplayParser.parse_match("raw_replays/3ab6f33e-11e4-42c8-bfce-f8c9485ece35.replay")

for f in [0, 50, 100, 500, 1000, 2000, 5000]:
    feat = PitchStateExtractor.extract_frame_features(df, f, blue, orange)
    pred = predictor.predict(feat)
    print(f"Frame {f} -> Pred: {pred} (ball_y: {feat['pos_y'].iloc[0]})")
    # check model directly
    raw_pred = predictor.model.predict(feat)
    print(f"  raw model predict: {raw_pred}")
