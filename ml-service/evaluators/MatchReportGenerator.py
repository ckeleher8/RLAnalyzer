import os
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from logic.ReplayParser import ReplayParser
from evaluators.ActionValueEvaluator import ActionValueEvaluator

# 1. Define the Contract (Interface)
class IHeuristicAnalyzer(ABC):
    """Contract for any heuristic analysis module."""
    @abstractmethod
    def analyze(self, df: pd.DataFrame, blue_players: list, orange_players: list) -> dict:
        """Returns a dictionary of heuristic stats to be merged into the final report."""
        pass

# 2. Refactored Generator
class MatchReportGenerator:
    """
    Facade pattern: Orchestrates parsing and delegates tasks
    to injected analyzers and ML evaluators.
    """
    def __init__(self, ml_evaluator: ActionValueEvaluator, heuristic_analyzers: list):
        self.ml_evaluator = ml_evaluator
        self.heuristic_analyzers = heuristic_analyzers

    def generate_full_report(self, replay_path: str, blue_players: list = None, orange_players: list = None) -> dict:
        # 1. Parse Replay
        df, hits, detected_blue, detected_orange, metadata, player_meta_map = ReplayParser.parse_match(replay_path)
        
        blue_roster = blue_players if blue_players else detected_blue
        orange_roster = orange_players if orange_players else detected_orange

        # 2. Heuristic Analysis
        heuristics_report = {}
        for analyzer in self.heuristic_analyzers:
            try:
                result = analyzer.analyze(df, blue_roster, orange_roster)
                heuristics_report.update(result)
            except Exception as e:
                print(f"Heuristic Analyzer {analyzer.__class__.__name__} warning: {e}")

        # 3. ML Action Values Evaluation
        ml_report_df = self.ml_evaluator.evaluate_parsed_match(df, hits, blue_roster, orange_roster)
        touches_list = ml_report_df.to_dict(orient="records") if not ml_report_df.empty else []

        # 4. Per-Player Summary Aggregations
        all_players = blue_roster + orange_roster
        player_summaries = []

        for p_name in all_players:
            p_touches = [t for t in touches_list if t.get("Player") == p_name]
            total_av = sum(t.get("Action_Value", 0.0) for t in p_touches)
            avg_av = (total_av / len(p_touches)) if p_touches else 0.0

            meta = player_meta_map.get(p_name, {})
            team = "Blue" if p_name in blue_roster else "Orange"
            
            # Wasted boost from heuristic
            boost_econ = heuristics_report.get(f"{p_name}_Boost_Economy", {})
            if "wasted_boost" in boost_econ:
                total_waste = float(boost_econ["wasted_boost"])
            else:
                waste_items = heuristics_report.get(f"{p_name}_Supersonic_Waste", [])
                total_waste = round(len(waste_items) * 0.33, 1)

            # Pad pickups from heuristic
            pathing_summary = heuristics_report.get(f"{p_name}_Boost_Pathing_Summary", {})
            if "small_pad_pickups" in pathing_summary:
                pad_pickups = int(pathing_summary["small_pad_pickups"])
            else:
                pathing_items = heuristics_report.get(f"{p_name}_Pathing", [])
                pad_pickups = sum(1 for item in pathing_items if item.get("Is_On_Pad", False))

            player_summaries.append({
                "name": p_name,
                "team": team,
                "goals": int(meta.get("goals", sum(1 for t in p_touches if t.get("Is_Goal")))),
                "saves": int(meta.get("saves", sum(1 for t in p_touches if t.get("Is_Save")))),
                "shots": int(meta.get("shots", max(1, len(p_touches) // 4))),
                "total_Action_Value": round(total_av, 3),
                "avg_Action_Value": round(avg_av, 3),
                "total_Wasted_Boost": total_waste,
                "pad_Pickups": pad_pickups
            })

        # 5. Compile Unified Report
        match_id = os.path.basename(replay_path).replace(".replay", "")
        return {
            "Match_ID": match_id,
            "Metadata": metadata,
            "Players": player_summaries,
            "Heuristics": heuristics_report,
            "ML_Action_Values": touches_list
        }