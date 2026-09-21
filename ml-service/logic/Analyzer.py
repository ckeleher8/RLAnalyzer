import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any

# Import the interface contract
from evaluators.MatchReportGenerator import IHeuristicAnalyzer

@dataclass
class AnalyzerConfig:
    """Holds all heuristic thresholds."""
    creep_threshold: float = 2500.0
    sag_threshold: float = 6000.0
    supersonic_velocity: float = 22000.0
    pad_radius_sq: float = 220.0**2
    big_pad_radius_sq: float = 450.0**2
    
    # 33 Standard Rocket League field small boost pads
    small_pads: np.ndarray = field(default_factory=lambda: np.array([
        # Center & central spine
        (0, 0), (1024, 0), (-1024, 0), (0, -1024), (0, 1024),
        (0, -2816), (0, 2816), (0, -4240), (0, 4240),
        # Midfield horseshoe arcs
        (1792, -1024), (-1792, -1024), (1792, 1024), (-1792, 1024),
        (940, -3308), (-940, -3308), (940, 3308), (-940, 3308),
        # Goal line defensive arcs & posts
        (1024, -4240), (-1024, -4240), (1024, 4240), (-1024, 4240),
        (2048, -4120), (-2048, -4120), (2048, 4120), (-2048, 4120),
        (1792, -2816), (-1792, -2816), (1792, 2816), (-1792, 2816),
        # Outer side connectors
        (3072, -1974), (-3072, -1974), (3072, 1974), (-3072, 1974)
    ]))

    # 6 Standard Big Boost Pads (4 corners + 2 sides)
    big_pads: np.ndarray = field(default_factory=lambda: np.array([
        (-3072, -4096), (3072, -4096),   # Blue Corners
        (-3072, 4096),  (3072, 4096),    # Orange Corners
        (-3584, 0),     (3584, 0)        # Midfield Sides
    ]))


class LastManAnalyzer(IHeuristicAnalyzer):
    """
    Analyzes rotational positioning, creeping, and sagging for the deepest defender.
    Dynamically differentiates between 2v2 (2nd Man / Last Man) and 3v3 (3rd Man / Last Defender).
    """
    def __init__(self, config: AnalyzerConfig = None):
        self.config = config or AnalyzerConfig()

    def analyze(self, df: pd.DataFrame, blue_players: list, orange_players: list) -> dict:
        results = {}
        teams = {"Blue": blue_players, "Orange": orange_players}

        for team_color, roster in teams.items():
            valid_roster = [p for p in roster if (p, 'pos_x') in df.columns]
            if len(valid_roster) < 1:
                continue

            team_size = len(valid_roster)
            is_2v2 = team_size == 2
            is_3v3 = team_size >= 3
            
            role_name = "2nd Man (Last Man)" if is_2v2 else "3rd Man (Last Defender)" if is_3v3 else "Solo Defender"
            game_mode = "2v2" if is_2v2 else "3v3" if is_3v3 else "1v1"
            optimal_presence_min = 40 if is_2v2 else 28
            optimal_presence_max = 60 if is_2v2 else 38

            dist_df = pd.DataFrame(index=df.index)
            ball_x = df[('ball', 'pos_x')] if ('ball', 'pos_x') in df.columns else 0
            ball_y = df[('ball', 'pos_y')] if ('ball', 'pos_y') in df.columns else 0
            ball_z = df[('ball', 'pos_z')] if ('ball', 'pos_z') in df.columns else 0

            for player in valid_roster:
                dx = df[(player, 'pos_x')] - ball_x
                dy = df[(player, 'pos_y')] - ball_y
                dz = df[(player, 'pos_z')] - ball_z
                dist_df[player] = np.sqrt(dx**2 + dy**2 + dz**2)

            dist_df['Last_Man_Name'] = dist_df[valid_roster].idxmax(axis=1)
            dist_df['Last_Man_Distance'] = dist_df[valid_roster].max(axis=1)

            dist_df['Flag_Creeping'] = dist_df['Last_Man_Distance'] < self.config.creep_threshold
            dist_df['Flag_Sagging'] = dist_df['Last_Man_Distance'] > self.config.sag_threshold

            # Calculate per-player last-man statistics
            player_stats = {}
            total_match_frames = len(df)
            
            for player in valid_roster:
                p_mask = dist_df['Last_Man_Name'] == player
                p_frames = int(np.sum(p_mask))
                p_creeping_frames = int(np.sum(p_mask & dist_df['Flag_Creeping']))
                p_sagging_frames = int(np.sum(p_mask & dist_df['Flag_Sagging']))
                
                presence_pct = round((p_frames / total_match_frames * 100), 1) if total_match_frames > 0 else 0
                creeping_time_sec = round(p_creeping_frames / 30.0, 1)
                sagging_time_sec = round(p_sagging_frames / 30.0, 1)
                
                # Evaluation relative to benchmarks:
                # Creeping Benchmark: Optimal: < 30 frames (< 1.0s), Acceptable: 30-90 frames, Danger: > 90 frames
                if p_creeping_frames <= 30:
                    creep_rating = "Optimal"
                    creep_badge = "Optimal (< 1.0s)"
                elif p_creeping_frames <= 90:
                    creep_rating = "Acceptable"
                    creep_badge = "Acceptable (1.0s - 3.0s)"
                else:
                    creep_rating = "Critical Danger"
                    creep_badge = "Critical Overcommit (> 3.0s)"

                # Sagging Benchmark: Optimal: < 60 frames (< 2.0s), Acceptable: 60-150 frames, Danger: > 150 frames
                if p_sagging_frames <= 60:
                    sag_rating = "Optimal"
                    sag_badge = "Optimal (< 2.0s)"
                elif p_sagging_frames <= 150:
                    sag_rating = "Acceptable"
                    sag_badge = "Acceptable (2.0s - 5.0s)"
                else:
                    sag_rating = "Excessive Passive"
                    sag_badge = "Too Passive (> 5.0s)"

                player_stats[player] = {
                    "player_name": player,
                    "team": team_color,
                    "role_name": role_name,
                    "game_mode": game_mode,
                    "total_last_man_frames": p_frames,
                    "presence_pct": presence_pct,
                    "optimal_presence_range": f"{optimal_presence_min}% - {optimal_presence_max}%",
                    "creeping_frames": p_creeping_frames,
                    "creeping_seconds": creeping_time_sec,
                    "creep_rating": creep_rating,
                    "creep_badge": creep_badge,
                    "sagging_frames": p_sagging_frames,
                    "sagging_seconds": sagging_time_sec,
                    "sag_rating": sag_rating,
                    "sag_badge": sag_badge
                }

            # Sample every 10 frames for payload
            sample_df = dist_df.iloc[::10]
            records = sample_df[['Last_Man_Name', 'Last_Man_Distance', 'Flag_Creeping', 'Flag_Sagging']].rename(
                columns={'Last_Man_Name': 'Third_Man_Name', 'Last_Man_Distance': 'Third_Man_Distance'}
            ).to_dict(orient="records")

            # Store results under both names for backwards compatibility and clarity
            results[f"{team_color}_Third_Man"] = records
            results[f"{team_color}_Last_Man_Meta"] = {
                "team": team_color,
                "team_size": team_size,
                "game_mode": game_mode,
                "role_name": role_name,
                "benchmarks": {
                    "creeping": {
                        "optimal": "< 30 frames (< 1.0s)",
                        "acceptable": "30 - 90 frames (1.0s - 3.0s)",
                        "danger": "> 90 frames (> 3.0s)",
                        "description": "Frames positioning < 2500 uu to ball as deepest defender (vulnerable to overhead clears)"
                    },
                    "sagging": {
                        "optimal": "< 60 frames (< 2.0s)",
                        "acceptable": "60 - 150 frames (2.0s - 5.0s)",
                        "danger": "> 150 frames (> 5.0s)",
                        "description": "Frames positioning > 6000 uu from ball while team attacks (cannot sustain pressure)"
                    },
                    "presence": {
                        "optimal_range": f"{optimal_presence_min}% - {optimal_presence_max}%",
                        "description": f"Ideal defensive share per player in {game_mode}"
                    }
                },
                "player_summaries": player_stats
            }

        return results

# Keep ThirdManAnalyzer alias for backwards compatibility
ThirdManAnalyzer = LastManAnalyzer


class SupersonicWasteAnalyzer(IHeuristicAnalyzer):
    """Detects players boosting while already at supersonic speed."""
    def __init__(self, config: AnalyzerConfig = None):
        self.config = config or AnalyzerConfig()

    def analyze(self, df: pd.DataFrame, blue_players: list, orange_players: list) -> dict:
        results = {}
        all_players = blue_players + orange_players

        for player_name in all_players:
            if (player_name, 'vel_x') not in df.columns:
                continue

            player_df = df[player_name]
            vel_x = player_df['vel_x']
            vel_y = player_df['vel_y']
            vel_z = player_df['vel_z']
            boost = player_df['boost']

            velocity_mag = np.sqrt(vel_x**2 + vel_y**2 + vel_z**2)
            boost_diff = boost.diff().fillna(0)

            is_supersonic = velocity_mag >= self.config.supersonic_velocity
            is_boosting = boost_diff < -0.1

            supersonic_waste_mask = is_supersonic & is_boosting

            waste_df = pd.DataFrame({
                'Frame': df.index,
                'Velocity': np.round(velocity_mag, 1),
                'Boost_Change': np.round(boost_diff, 2),
                'Is_Wasting': supersonic_waste_mask
            })

            wasting_instances = waste_df[waste_df['Is_Wasting']]
            total_waste_amount = round(len(wasting_instances) * 0.33, 1)

            if total_waste_amount <= 15:
                waste_grade = "A+ (Optimal Conservation)"
            elif total_waste_amount <= 35:
                waste_grade = "B (Acceptable)"
            else:
                waste_grade = "C (High Waste - Release Boost at Supersonic)"

            results[f"{player_name}_Supersonic_Waste"] = wasting_instances.head(50).to_dict(orient="records")
            results[f"{player_name}_Boost_Economy"] = {
                "player_name": player_name,
                "wasted_frames": len(wasting_instances),
                "wasted_boost": total_waste_amount,
                "grade": waste_grade,
                "benchmarks": {
                    "optimal": "< 15 boost wasted",
                    "acceptable": "15 - 35 boost wasted",
                    "poor": "> 35 boost wasted"
                }
            }

        return results


class SmallPadPathingAnalyzer(IHeuristicAnalyzer):
    """
    Evaluates player micro-pathing over small boost pads vs reliance on 100-orbs.
    Provides complete transparency into Corner Dependency vs Balanced Midfield calculations.
    """
    def __init__(self, config: AnalyzerConfig = None):
        self.config = config or AnalyzerConfig()

    def analyze(self, df: pd.DataFrame, blue_players: list, orange_players: list) -> dict:
        results = {}
        all_players = blue_players + orange_players

        for player_name in all_players:
            if (player_name, 'pos_x') not in df.columns:
                continue

            px = df[(player_name, 'pos_x')].values
            py = df[(player_name, 'pos_y')].values
            positions = np.column_stack((px, py))
            total_frames = len(px)

            # 1. Distance to Small Boost Pads
            diff_small = positions[:, np.newaxis, :] - self.config.small_pads[np.newaxis, :, :]
            dist_sq_small = np.sum(diff_small**2, axis=-1)
            min_dist_small = np.sqrt(np.min(dist_sq_small, axis=1))
            is_on_small_pad = min_dist_small <= np.sqrt(self.config.pad_radius_sq)
            
            # Count discrete small pad pickups (entering radius)
            small_pad_pickups = int(np.sum(np.diff(is_on_small_pad.astype(int)) == 1))
            small_pad_pickups = max(small_pad_pickups, int(np.sum(is_on_small_pad) // 8))

            # 2. Distance to Big Boost Pads (Corners vs Side)
            diff_big = positions[:, np.newaxis, :] - self.config.big_pads[np.newaxis, :, :]
            dist_sq_big = np.sum(diff_big**2, axis=-1)
            min_dist_big = np.sqrt(np.min(dist_sq_big, axis=1))
            nearest_big_idx = np.argmin(dist_sq_big, axis=1)
            is_on_big_pad = min_dist_big <= np.sqrt(self.config.big_pad_radius_sq)

            # Big boost pickups (indices 0..3 are corners, 4..5 are mid-sides)
            big_pickups = np.diff(is_on_big_pad.astype(int)) == 1
            corner_big_pickups = int(np.sum(big_pickups & (nearest_big_idx[1:] < 4)))
            side_big_pickups = int(np.sum(big_pickups & (nearest_big_idx[1:] >= 4)))

            # 3. Spatial Occupancy (Deep Corners vs Central Midfield Spine)
            corner_mask = (np.abs(px) > 1500) & (np.abs(py) > 2800)
            midfield_mask = (np.abs(px) <= 1500) & (np.abs(py) <= 2500)

            corner_time_pct = round(float(np.mean(corner_mask) * 100), 1) if total_frames > 0 else 0
            midfield_time_pct = round(float(np.mean(midfield_mask) * 100), 1) if total_frames > 0 else 0

            # 4. Total Boost Ingestion Metrics
            total_intake_events = small_pad_pickups + corner_big_pickups + side_big_pickups
            if total_intake_events == 0:
                total_intake_events = max(1, small_pad_pickups)

            small_pad_ratio_pct = round((small_pad_pickups / total_intake_events) * 100, 1)
            corner_boost_ratio_pct = round((corner_big_pickups / total_intake_events) * 100, 1)
            side_boost_ratio_pct = round((side_big_pickups / total_intake_events) * 100, 1)

            # 5. Deterministic Classification & Transparent Criteria
            # Benchmark criteria:
            # - Optimal: Small Pad Ratio >= 70% AND Corner Time <= 20%
            # - Balanced Midfield: Small Pad Ratio 55% - 70% AND Corner Time <= 25%
            # - Moderate Corner Bias: Corner Boost Ratio 35% - 50% OR Corner Time 25% - 35%
            # - Heavy Corner Dependency: Corner Boost Ratio >= 50% OR (Corner Time > 35% AND Small Pads < 15)
            if corner_boost_ratio_pct >= 50 or (corner_time_pct > 35 and small_pad_pickups < 15):
                classification = "Heavy Corner Dependency"
                status_color = "rose"
                badge = "Heavy Corner Dependency"
                criteria_reason = (
                    f"High corner reliance ({corner_boost_ratio_pct}% of boost collections from corner 100-orbs, "
                    f"{corner_time_pct}% time in deep corners). You are regularly driving away from the play for boost."
                )
                actionable_advice = (
                    "Avoid turning wide to your defensive corner 100-orbs when rotating back. "
                    "Rotate down the central goal-line spine ('the horseshoe' pad arc) while keeping vision of the ball. "
                    "Collecting 3 small pads (+36 boost) provides more than enough boost for any fast aerial save or recovery."
                )
            elif corner_boost_ratio_pct >= 35 or corner_time_pct > 25:
                classification = "Moderate Corner Bias"
                status_color = "yellow"
                badge = "Moderate Corner Bias"
                criteria_reason = (
                    f"Moderate corner bias ({corner_boost_ratio_pct}% corner orbs, {corner_time_pct}% corner time). "
                    f"You occasionally abandon rotational pressure to grab a 100-boost when small pads were available."
                )
                actionable_advice = (
                    "When your teammate challenges, stay anchored on midfield small pads instead of retreating to corner orbs. "
                    "This keeps you positioned to capitalize immediately on 50/50 spills and loose balls."
                )
            elif small_pad_ratio_pct >= 70 and small_pad_pickups >= 15:
                classification = "Optimal Small-Pad Master"
                status_color = "green"
                badge = "Optimal Small-Pad Master"
                criteria_reason = (
                    f"Elite pad routing ({small_pad_ratio_pct}% small pad ratio, {small_pad_pickups} pickups, {midfield_time_pct}% midfield control). "
                    f"You maintain offensive pressure without running out of boost."
                )
                actionable_advice = (
                    "Maintain this excellent habit. Feather boost through rotation lanes to keep momentum at supersonic without burning tank capacity."
                )
            else:
                classification = "Balanced Midfield"
                status_color = "cyan"
                badge = "Balanced Midfield"
                criteria_reason = (
                    f"Solid midfield presence ({midfield_time_pct}% midfield time, {small_pad_pickups} small pads). "
                    f"Balanced collection between opportunistic 100-orbs and rotational pads."
                )
                actionable_advice = (
                    "Focus on picking up 1-2 extra pads during recovery turns to consistently maintain 40+ boost at all times."
                )

            # Sample pathing records
            pathing_df = pd.DataFrame({
                'Near_Pad_Index': np.argmin(dist_sq_small, axis=1),
                'Distance_To_Pad': np.round(min_dist_small, 1),
                'Is_On_Pad': is_on_small_pad
            }, index=df.index)

            results[f"{player_name}_Pathing"] = pathing_df.iloc[::15].to_dict(orient="records")
            results[f"{player_name}_Boost_Pathing_Summary"] = {
                "player_name": player_name,
                "small_pad_pickups": small_pad_pickups,
                "corner_big_pickups": corner_big_pickups,
                "side_big_pickups": side_big_pickups,
                "corner_time_pct": corner_time_pct,
                "midfield_time_pct": midfield_time_pct,
                "small_pad_ratio_pct": small_pad_ratio_pct,
                "corner_boost_ratio_pct": corner_boost_ratio_pct,
                "classification": classification,
                "status_color": status_color,
                "badge": badge,
                "criteria_reason": criteria_reason,
                "actionable_advice": actionable_advice,
                "benchmarks": {
                    "optimal_pad_ratio": "> 70% small pad ratio",
                    "optimal_midfield_time": "> 35% midfield control",
                    "danger_corner_time": "> 25% deep corner time",
                    "danger_corner_boost": "> 40% corner boost reliance"
                }
            }

        return results