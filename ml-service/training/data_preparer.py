import os
import sys
import pandas as pd
import numpy as np

# Ensure root ml-service is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.ReplayParser import ReplayParser
from logic.FeatureExtractor import PitchStateExtractor

class RewardShaper:
    """Responsibility: Handles the math for time-decaying action values."""
    @staticmethod
    def calculate_time_decayed_rewards(df_length: int, hits: list, blue_players: list, discount_factor=0.99, max_frames_back=300) -> np.ndarray:
        target_values = np.zeros(df_length)
        goals = [h for h in hits if getattr(h, 'goal', False) or getattr(h, 'is_goal', False)]
        
        for goal in goals:
            player_name = getattr(goal, 'player_name', '')
            is_blue_goal = player_name in blue_players
            multiplier = 1.0 if is_blue_goal else -1.0
            
            goal_frame = getattr(goal, 'frame_number', 0)
            start_frame = max(0, goal_frame - max_frames_back)
            
            for f in range(start_frame, min(df_length, goal_frame + 1)):
                frames_away = goal_frame - f
                value = multiplier * (discount_factor ** frames_away)
                
                if abs(value) > abs(target_values[f]):
                    target_values[f] = value
                    
        return target_values


class ActionValueDataPreparer:
    """Orchestrates reading replays and preparing training feature CSVs."""
    def __init__(self, raw_dir="./raw_replays", output_dir="./training_data", frame_skip=15):
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.frame_skip = frame_skip
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _process_single_match(self, df: pd.DataFrame, hits: list, blue_players: list, orange_players: list) -> pd.DataFrame:
        target_values = RewardShaper.calculate_time_decayed_rewards(
            len(df), hits, blue_players
        )
        
        dataset_rows = []
        for frame_idx in range(0, len(df), self.frame_skip):
            feature_df = PitchStateExtractor.extract_frame_features(df, frame_idx, blue_players, orange_players)
            feature_df['Target_Goal_Value'] = target_values[frame_idx]
            dataset_rows.append(feature_df)
            
        return pd.concat(dataset_rows, ignore_index=True)

    def prepare_dataset(self):
        raw_files = [f for f in os.listdir(self.raw_dir) if f.endswith('.replay')]
        
        for file in raw_files:
            replay_path = os.path.join(self.raw_dir, file)
            out_path = os.path.join(self.output_dir, file.replace('.replay', '.csv'))
            
            print(f"Processing raw replay for training: {file}...")
            try:
                df, hits, blue_players, orange_players, _, _ = ReplayParser.parse_match(replay_path)
                match_dataset = self._process_single_match(df, hits, blue_players, orange_players)
                match_dataset.to_csv(out_path, index=False)
                print(f"Successfully saved {len(match_dataset)} frames to {out_path}")
            except Exception as e:
                print(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    preparer = ActionValueDataPreparer()
    preparer.prepare_dataset()