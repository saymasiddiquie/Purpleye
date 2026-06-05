import os
import sys

# Add the project root to python path so services can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.ingest.synth import synth_config_from_env, generate_timeline

def main():
    print("Generating synthetic retail events...")
    cfg = synth_config_from_env()
    # Ensure stable output
    cfg.seed = 42
    cfg.sessions = 30
    cfg.duration_s = 600
    
    events = generate_timeline(cfg)
    print(f"Generated {len(events)} events.")
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "events.jsonl"))
    with open(output_path, "w", encoding="utf-8") as f:
        for ev in events:
            # Serialize the Pydantic model to JSON string and write as a line
            f.write(ev.model_dump_json() + "\n")
            
    print(f"Successfully wrote events to {output_path}")

if __name__ == "__main__":
    main()
