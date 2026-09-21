import requests
import json
import time

url = "http://127.0.0.1:5000/api/replay/upload"
replay_path = "raw_replays/3ab6f33e-11e4-42c8-bfce-f8c9485ece35.replay"

with open(replay_path, "rb") as f:
    files = {"file": ("3ab6f33e.replay", f, "application/octet-stream")}
    res = requests.post(url, files=files)
    print("Upload status:", res.status_code, res.text)
    upload_data = res.json()
    match_id = upload_data.get("id")

# Poll status
for _ in range(15):
    time.sleep(1)
    status_res = requests.get(f"http://127.0.0.1:5000/api/replay/{match_id}/status")
    status_data = status_res.json()
    print("Polling status:", status_data.get("status"))
    if status_data.get("status") in ("Completed", "Failed"):
        break

match_res = requests.get(f"http://127.0.0.1:5000/api/replay/{match_id}")
match = match_res.json()
print("=== FINAL MATCH DATA ===")
print("MapName:", match.get("mapName"))
print("Scores: Blue", match.get("blueScore"), "-", match.get("orangeScore"), "Orange")
print("WinningTeam:", match.get("winningTeam"))
print("DurationSeconds:", match.get("durationSeconds"))
print("Players count:", len(match.get("players", [])))
for p in match.get("players", []):
    print(f"  Player: {p.get('name')} | Team: {p.get('team')} | Goals: {p.get('goals')} | Saves: {p.get('saves')} | Shots: {p.get('shots')} | TotalAV: {p.get('total_Action_Value')} | AvgAV: {p.get('avg_Action_Value')}")
print("Touches count:", len(match.get("touches", [])))
print("First 3 touches:", match.get("touches", [])[:3])
