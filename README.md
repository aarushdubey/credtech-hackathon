# credtech-hackathon
CredTech: Real-Time Explainable Credit Intelligence 📈
A submission for the CredTech Hackathon, organized by The Programming Club, IITK.

CredTech is a full-stack web application designed to solve the core problem of traditional credit ratings: they are slow, opaque, and often lag behind real-world events. Our platform ingests live financial and news data to generate a dynamic, explainable creditworthiness score for publicly traded companies.

✨ Key Features
🧠 Real-Time Scoring: Fuses live stock data, financial ratios, and news sentiment into a single, easy-to-understand score.

🔍 Drill-Down Explanations: Every score is fully explained, breaking down the impact of price movement, news, financials, and macroeconomic factors. No black boxes.

📊 Interactive Charts: Visualize historical price trends and switch between different timeframes (1M, 3M, 6M, 1Y) to analyze performance.

🤝 Peer Comparison: Instantly compare a company's credit score against its key competitors.

📰 Clickable Headlines: All news headlines are linked directly to the source article for verification and further reading.

❤️ Personalized Watchlist: Save companies to a persistent watchlist for easy access and monitoring.

🔄 Auto-Refresh: The dashboard simulates a live environment by auto-refreshing the score every 60 seconds.

🛠️ Tech Stack & System Architecture
Our platform is built with a modern, efficient, and scalable tech stack.

Backend: Python with the Flask web framework, using Gunicorn as the production WSGI server.

Frontend: Vanilla HTML5, CSS3, and JavaScript (ES6+).

Data Sources: yfinance for financial data and the NewsAPI for unstructured news headlines.

Charting: Chart.js for interactive data visualization.

Deployment: Hosted as a Web Service on Render, deployed directly from GitHub.

System Flow
The architecture is a simple, robust client-server model:
[User's Browser] <--> [Flask/Gunicorn on Render] <--> [yfinance & NewsAPI]

🏆 Meeting the Hackathon Challenge
We designed our project to directly address the key evaluation criteria.

🎯 Model Accuracy & Explainability (30%)
Our model is 100% transparent. The "Score Breakdown" feature provides a clear, feature-level explanation for every score, showing the user exactly how stock performance, news sentiment, and financial health contributed to the final number.

🔧 Data Engineering & Pipeline (20%)
The backend gracefully handles potential API failures. If the NewsAPI fails (due to rate limits or an invalid key), the application continues to function, providing a score based on the available financial data instead of crashing. We also implemented a simple caching mechanism to reduce redundant API calls.

📰 Dealing with Unstructured Data (12.5%)
We go beyond simple headlines by performing a keyword-based sentiment analysis. This analysis meaningfully impacts both the final credit score and the plain-language explanation, directly integrating subjective news data with objective financial data.

🖥️ User Experience & Dashboard (15%)
The dashboard is designed for analysts. Features like the personalized watchlist, clickable headlines, peer comparisons, and dynamic chart timeframes provide an intuitive and insightful user experience.

🚀 Deployment & Real-Time Updates (10%)
The entire application is deployed on Render with a public URL. The "Auto-Refresh" feature updates the score every 60 seconds, simulating the real-time nature required by the problem statement.

✨ Innovation (12.5%)
Our key innovations are the fusion of multiple data types (price, financials, news, macro) into a single score and the analyst-centric features like peer comparison and a persistent watchlist, which are not typically found in basic financial dashboards.

🤔 Key Trade-offs & Decisions
Rule-Based Model vs. ML: We chose a rule-based scoring engine over a complex ML model to ensure 100% explainability and transparency, directly addressing the "no black box" challenge.

Client-Side Watchlist: We used the browser's localStorage for the watchlist. This allowed us to deliver a personalized feature quickly without the complexity of a database and user authentication, which was ideal for a hackathon timeline.

API Limitations: The free NewsAPI plan is restricted on production servers. To meet the challenge, we designed the app to work perfectly locally (for the video demo) while handling the API failure gracefully on the live site.

🏃 How to Run Locally
Clone the repository:

Bash

git clone https://github.com/aarushdubey/credtech-hackathon.git
cd credtech-hackathon
Create and activate the virtual environment:

Bash

python -m venv venv
source venv/bin/activate
Install dependencies:

Bash

pip install -r requirements.txt
Create a .env file in the main project folder and add your NewsAPI key:

NEWS_API_KEY="your_api_key_here"
Run the application:

Bash

venv/bin/python app.py
Open your browser and go to http://127.0.0.1:5000.
