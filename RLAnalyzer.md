

Here is the architectural flow:

1. **Data Acquisition & Parsing:**
The first hurdle is getting usable data out of the proprietary `.replay` files.

* **Acquisition:** You can pull replays automatically using the Ballchasing.com API, which provides a massive dataset of high-level games to build a training set.
* **Parsing:** Raw replay files are binary. Use an existing parser like `Rattletrap` (or Python wrappers like `carball` or `boxcars`) to convert the binary data into JSON or structured Python Pandas DataFrames. This gives you frame-by-frame data on car positions, boost levels, velocities, and ball physics.


2. **Feature Engineering & AI Models:** Python.
Raw frame data isn't enough; the AI needs engineered features to understand the context of the game.

* **Feature Extraction:** Calculate higher-level metrics from the raw frames. Focus on mechanics relevant to Champion-level play and above, such as directional air roll efficiency, boost management during sustained pressure, recovery times, and rotation spacing.
* **Model Training:** Use `scikit-learn` or `TensorFlow` to train your models. You might build:
* **A Classification Model:** To evaluate decision-making (e.g., predicting whether a challenge will result in a goal or a counter-attack based on positioning).
* **An Anomaly Detection Model:** To flag mechanical inefficiencies, like poor aerial paths or suboptimal recoveries.


* The output should be actionable insights (e.g., "You are flipping too early on back-post rotations").


3. **Backend API & Data Persistence:** C# .NET & SQL Server.
Once the Python pipeline generates insights, they need to be stored and served securely.

* **Database:** Design a schema in SQL Server to handle the hierarchical data: Users -> Series -> Matches -> Player Stats & AI Insights.
* **API Layer:** Build a C# .NET backend with RESTful endpoints. The API will receive the processed JSON reports from the Python pipeline, map them to DTOs, and persist them in the SQL database. It will act as the bridge between your analysis engine and the user interface.


4. **Frontend Dashboard:** React.
The final layer is visualizing the insights so players can actually use them to improve.

* **State Management:** Use React to build a fast, responsive dashboard that pulls data from your C# API.
* **Visualizations:** Integrate charting libraries to show performance trends over time, heatmaps of positioning, or boost usage footprints.
* **Feedback Delivery:** Present the AI's findings clearly. Instead of just showing numbers, translate the model outputs into specific training recommendations or highlight critical moments on a timeline.