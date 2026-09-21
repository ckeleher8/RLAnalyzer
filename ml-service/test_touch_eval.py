import os
import pandas as pd
from logic.ReplayParser import ReplayParser
from logic.FeatureExtractor import PitchStateExtractor
from evaluators.ActionValueEvaluator import ActionValueEvaluator
from engines.xgboost_engine import XGBoostPredictor

predictor = XGBoostPredictor("pitch_evaluator.json")
evaluator = ActionValueEvaluator(predictor)

df, hits, blue, orange, meta, player_meta = ReplayParser.parse_match("raw_replays/3ab6f33e-11e4-42c8-bfce-f8c9485ece35.replay")
eval_df = evaluator.evaluate_parsed_match(df, hits, blue, orange)

print("Eval df head(10):")
print(eval_df.head(10))

print("\nNon-zero action values count:", len(eval_df[eval_df['Action_Value'] != 0]))
print("Total touches count:", len(eval_df))
print(eval_df[eval_df['Is_Goal']])
