import os

# Set API_BASE - use environment variable or default to local
api_base = os.environ.get("API_BASE", "http://localhost:8000")
os.environ["API_BASE"] = api_base

# Run the Streamlit dashboard
exec(open("services/dashboard/app.py").read())
