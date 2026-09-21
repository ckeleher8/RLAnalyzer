import requests
import os

# --- Configuration ---
API_KEY = "WBxphxSbHAXSz8RAszhWjCKaXqDFv4l0ykHsZLiZ"  # Replace with your actual API key
BASE_URL = "https://ballchasing.com/api"
DOWNLOAD_DIR = "./raw_replays"

# Ensure the download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Headers required for authentication
HEADERS = {
    "Authorization": API_KEY
}

def fetch_replay_metadata(playlist="ranked-doubles", min_rank="supersonic-legend", count=5):
    """
    Searches for replays matching specific criteria and returns their metadata.
    """
    print(f"Searching for {count} {playlist} replays (Min Rank: {min_rank})...")
    
    endpoint = f"{BASE_URL}/replays"
    params = {
        "playlist": playlist,
        "min-rank": min_rank,
        "count": count,
        "sort-by": "replay-date",
        "sort-dir": "desc"
    }

    response = requests.get(endpoint, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("list", [])
    else:
        print(f"Failed to fetch metadata. Status Code: {response.status_code}")
        print(response.text)
        return []

def download_replay_file(replay_id, filename):
    """
    Downloads the physical .replay file using its ID.
    """
    endpoint = f"{BASE_URL}/replays/{replay_id}/file"
    file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.replay")

    # Skip if we already downloaded this replay
    if os.path.exists(file_path):
        print(f"Replay {filename} already exists. Skipping.")
        return

    print(f"Downloading: {filename}.replay...")
    response = requests.get(endpoint, headers=HEADERS, stream=True)

    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print("Download complete.")
    elif response.status_code == 429:
        print("Rate limit exceeded. Consider adding a time.sleep() delay.")
    else:
        print(f"Failed to download replay. Status Code: {response.status_code}")

# --- Main Execution ---
if __name__ == "__main__":
    # Fetch a list of high-level 2v2 replay IDs
    # playlist="ranked-doubles" targets 2v2
    # min_rank="supersonic-legend" targets SSL players
    replays = fetch_replay_metadata(playlist="ranked-doubles", min_rank="supersonic-legend", count=5)
    
    if not replays:
        print("No replays found or API key is invalid.")
    
    # Loop through the list and download each .replay file
    for replay in replays:
        replay_id = replay["id"]
        # Creating a readable filename using the match title or ID
        replay_name = replay.get("title", replay_id).replace(" ", "_").replace("/", "-")
        
        download_replay_file(replay_id, replay_name)
        
    print("\nData acquisition complete. Replays are saved in:", DOWNLOAD_DIR)