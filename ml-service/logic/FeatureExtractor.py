import pandas as pd
from typing import List, Callable, Optional
from dataclasses import dataclass, field

@dataclass
class FeatureConfig:
    """Defines the schema of features to extract."""
    ball_features: List[str] = field(default_factory=lambda: ['pos_x', 'pos_y', 'pos_z', 'vel_x', 'vel_y', 'vel_z'])
    player_features: List[str] = field(default_factory=lambda: ['pos_x', 'pos_y', 'pos_z', 'vel_x', 'vel_y', 'vel_z', 'boost'])
    max_players_per_team: int = 3

class PitchStateExtractor:
    """
    Stateless utility to extract a standardized feature vector for ML models.
    Supports both static invocation and instance-based custom configuration.
    """
    def __init__(self, config: Optional[FeatureConfig] = None, player_sorting_strategy: Optional[Callable] = None):
        self.config = config or FeatureConfig()
        self.player_sorting_strategy = player_sorting_strategy or (lambda df, frame_idx, players: players)

    def extract_features(self, df: pd.DataFrame, frame_idx: int, blue_players: list, orange_players: list) -> pd.DataFrame:
        try:
            row = df.loc[frame_idx]
        except (KeyError, IndexError):
            nearest_idx = df.index.get_indexer([frame_idx], method='nearest')[0]
            row = df.iloc[nearest_idx]

        features = {}

        # 1. Ball Features
        for col in self.config.ball_features:
            val = 0.0
            if ('ball', col) in row:
                val = float(row[('ball', col)])
            features[col] = val

        # 2. Player Sorting
        blue_sorted = self.player_sorting_strategy(df, frame_idx, blue_players)
        orange_sorted = self.player_sorting_strategy(df, frame_idx, orange_players)

        # 3. Blue Team Features (Padded to max_players_per_team)
        for i in range(self.config.max_players_per_team):
            if i < len(blue_sorted):
                p_name = blue_sorted[i]
                for col in self.config.player_features:
                    val = float(row[(p_name, col)]) if (p_name, col) in row else 0.0
                    features[f'blue_p{i}_{col}'] = val
            else:
                for col in self.config.player_features:
                    features[f'blue_p{i}_{col}'] = 0.0

        # 4. Orange Team Features (Padded to max_players_per_team)
        for i in range(self.config.max_players_per_team):
            if i < len(orange_sorted):
                p_name = orange_sorted[i]
                for col in self.config.player_features:
                    val = float(row[(p_name, col)]) if (p_name, col) in row else 0.0
                    features[f'orange_p{i}_{col}'] = val
            else:
                for col in self.config.player_features:
                    features[f'orange_p{i}_{col}'] = 0.0

        return pd.DataFrame([features])

    @classmethod
    def extract_frame_features(cls, df: pd.DataFrame, frame_idx: int, blue_players: list, orange_players: list) -> pd.DataFrame:
        """Static convenience method matching original API contract."""
        extractor = cls()
        return extractor.extract_features(df, frame_idx, blue_players, orange_players)