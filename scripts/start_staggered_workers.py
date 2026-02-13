"""
Start workers with staggered delays to avoid Chrome conflicts
"""
import subprocess
import time
import sys

workers = [
    (34, 66, "Worker 2"),
    (67, 99, "Worker 3"),
    (100, 133, "Worker 4")
]

print("Starting workers with 60-second delays between each...")
print("Worker 1 (Pages 1-33) is already running\n")

for start, end, name in workers:
    print(f"[{time.strftime('%H:%M:%S')}] Starting {name} (Pages {start}-{end})...")

    log_file = f"batch_{start}_{end}.log"

    # Start the process in background
    subprocess.Popen(
        [sys.executable, "batch_scraper.py", str(start), str(end)],
        stdout=open(log_file, 'w'),
        stderr=subprocess.STDOUT,
        cwd=r"D:\workspace\banpu"
    )

    print(f"[{time.strftime('%H:%M:%S')}] {name} started, waiting 60 seconds before next...\n")
    time.sleep(60)

print(f"[{time.strftime('%H:%M:%S')}] All workers started!")
print("\nMonitor progress with:")
print("  tail -f batch_*.log")
