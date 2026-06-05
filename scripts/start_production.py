import os
import subprocess
import sys
import time
import signal

def main():
    print("Starting Purpleye Unified Production Stack...")
    
    # Get port from environment (Render sets PORT for the web service)
    port = os.environ.get("PORT", "8501")
    
    processes = []
    
    def cleanup_processes(*args):
        print("\nShutting down all processes...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                pass
        sys.exit(0)
        
    # Register termination signals
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)
    
    # 1. Start FastAPI API on port 8000
    print("Starting FastAPI API on port 8000...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "services.api.main:app", 
        "--host", "127.0.0.1", "--port", "8000"
    ])
    processes.append(api_process)
    
    # 2. Start Aggregator
    print("Starting Aggregator...")
    agg_process = subprocess.Popen([
        sys.executable, "-m", "services.aggregator"
    ])
    processes.append(agg_process)
    
    # 3. Start Ingest (synthetic)
    print("Starting Ingest (synthetic mode)...")
    ingest_env = {**os.environ, "INGEST_MODE": "synthetic"}
    ingest_process = subprocess.Popen([
        sys.executable, "-m", "services.ingest"
    ], env=ingest_env)
    processes.append(ingest_process)
    
    # 4. Start POS Publisher
    print("Starting POS Publisher...")
    pos_process = subprocess.Popen([
        sys.executable, "-m", "services.pos"
    ])
    processes.append(pos_process)
    
    # Wait a few seconds for services to initialize
    time.sleep(5)
    
    # 5. Start Streamlit Dashboard in the foreground (Render routes incoming traffic to $PORT)
    print(f"Starting Streamlit Dashboard on port {port}...")
    dashboard_env = {**os.environ, "API_BASE": "http://127.0.0.1:8000"}
    dashboard_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "services/dashboard/app.py",
        "--server.port", port, "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ], env=dashboard_env)
    processes.append(dashboard_process)
    
    try:
        # Wait for the dashboard to finish or keep running
        dashboard_process.wait()
    except KeyboardInterrupt:
        cleanup_processes()
    except Exception as e:
        print(f"Error in dashboard execution: {e}")
        cleanup_processes()

if __name__ == "__main__":
    main()
