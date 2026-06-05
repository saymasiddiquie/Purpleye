import os
import signal
import subprocess
import sys
import time
from urllib.parse import urlparse


def mask_url(url: str | None) -> str:
    if not url:
        return "NOT SET"

    try:
        parsed = urlparse(url)

        if parsed.password:
            netloc = parsed.netloc.replace(
                f":{parsed.password}@",
                ":******@"
            )
        else:
            netloc = parsed.netloc

        return f"{parsed.scheme}://{netloc}{parsed.path}"
    except Exception:
        return "***"


def terminate_processes(processes):
    print("Stopping child processes...")

    for process in reversed(processes):
        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            pass

    for process in reversed(processes):
        try:
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


def main():
    print("======================================")
    print("Starting Purpleye Unified Stack")
    print("======================================")

    port = os.environ.get("PORT", "10000")

    database_url = os.environ.get("DATABASE_URL")
    redis_url = os.environ.get("REDIS_URL")

    print(f"PORT={port}")
    print(f"DATABASE_URL={mask_url(database_url)}")
    print(f"REDIS_URL={mask_url(redis_url)}")

    # Fail fast if Render env vars are missing
    if not database_url:
        print("ERROR: DATABASE_URL is not set")
        sys.exit(1)

    if not redis_url:
        print("ERROR: REDIS_URL is not set")
        sys.exit(1)

    processes = []

    def shutdown_handler(signum=None, frame=None):
        print("\nShutdown signal received...")
        terminate_processes(processes)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # FastAPI
        print("\n[1/5] Starting FastAPI API...")

        api_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "services.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            env=os.environ.copy(),
        )

        processes.append(api_process)

        # Aggregator
        print("[2/5] Starting Aggregator...")

        agg_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "services.aggregator",
            ],
            env=os.environ.copy(),
        )

        processes.append(agg_process)

        # Ingest
        print("[3/5] Starting Ingest...")

        ingest_env = os.environ.copy()
        ingest_env["INGEST_MODE"] = "synthetic"

        ingest_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "services.ingest",
            ],
            env=ingest_env,
        )

        processes.append(ingest_process)

        # POS
        print("[4/5] Starting POS Publisher...")

        pos_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "services.pos",
            ],
            env=os.environ.copy(),
        )

        processes.append(pos_process)

        print("Waiting for services to initialize...")
        time.sleep(5)

        # Dashboard
        print(f"[5/5] Starting Streamlit Dashboard on port {port}...")

        dashboard_env = os.environ.copy()
        dashboard_env["API_BASE"] = "http://127.0.0.1:8000"

        dashboard_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "services/dashboard/app.py",
                "--server.port",
                str(port),
                "--server.address",
                "0.0.0.0",
                "--server.headless",
                "true",
            ],
            env=dashboard_env,
        )

        processes.append(dashboard_process)

        print("\nPurpleye stack started successfully.")

        while True:
            for process in processes:
                if process.poll() is not None:
                    print(
                        f"Process exited unexpectedly "
                        f"(PID={process.pid}, RC={process.returncode})"
                    )
                    terminate_processes(processes)
                    sys.exit(process.returncode)

            time.sleep(2)

    except KeyboardInterrupt:
        shutdown_handler()

    except Exception as exc:
        print(f"Fatal startup error: {exc}")
        terminate_processes(processes)
        sys.exit(1)


if __name__ == "__main__":
    main()
