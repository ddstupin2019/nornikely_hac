import re
from datetime import datetime

def analyze_pipeline_logs(logfile="pipeline.log"):
    start_time = None
    runs = []
    
    with open(logfile, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
        if not match:
            continue
            
        timestamp_str = match.group(1)
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        
        if "Starting pipeline..." in line:
            start_time = timestamp
        elif "Pipeline finished." in line and start_time:
            elapsed = (timestamp - start_time).total_seconds()
            runs.append(elapsed)
            start_time = None

    if not runs:
        print("No complete pipeline runs found in log.")
        return

    print("Pipeline run times (in seconds):")
    for i, t in enumerate(runs, 1):
        minutes = int(t // 60)
        seconds = int(t % 60)
        print(f"Run {i}: {t:.2f}s ({minutes}m {seconds}s)")
        
    print(f"\nAverage total time: {sum(runs)/len(runs):.2f}s")
    print(f"Min time: {min(runs):.2f}s")
    print(f"Max time: {max(runs):.2f}s")

if __name__ == "__main__":
    analyze_pipeline_logs()
