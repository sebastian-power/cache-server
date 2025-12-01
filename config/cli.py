import argparse
import json
import os
import signal
from pathlib import Path
import subprocess
import sys

PID_FILE = Path(".run/pids.json")
def clear_cache():
	subprocess.run(["docker", "exec", "-it", "cache-server-redis-1", "redis-cli", "-n", "1", "FLUSHDB"], capture_output=True)

def start(origin, port):
	repo_root = Path(__file__).resolve().parents[1]
	if PID_FILE.exists():
		print("Server already running")
		return
	
	env = os.environ.copy()
	env["UPSTREAM_BASE"] = origin
	env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
	PID_FILE.parent.mkdir(exist_ok=True)
	(PID_FILE.parent / "logs").mkdir(exist_ok=True)
	log_dir = PID_FILE.parent / "logs"

	django_proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
	subprocess.run(["docker", "compose", "up", "-d"])
	celery_proc = subprocess.Popen(
		["celery", "-A", "config", "worker", "--loglevel=info"],
		stdout=open("celery_worker.log", "w"),
		stderr=open("celery_worker.log", "w"),
		text=True
	)
	data = {
        "django": django_proc.pid,
        "celery": celery_proc.pid,
    }
	PID_FILE.write_text(json.dumps(data, indent=2))
	print(f"Server started on port {port}")

def stop():
	if not PID_FILE.exists():
		print("No server processes detected")
		return
	
	data = json.loads(PID_FILE.read_text())
	subprocess.run(["docker", "compose", "down"])
	print("Stopped docker")

	for name, pid in data.items():
		try:
			if os.name == "nt":
				subprocess.call(["taskkill", "/PID", str(pid), "/F"])
			else:
				os.kill(pid, signal.SIGTERM)
			print(f"Stopped {name}")
		except Exception as e:
			print(f"Could not stop {name}: {e}")
	
	PID_FILE.unlink(missing_ok=True)
	print("Server shutdown complete")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--clear-cache", action="store_true")
	sub = parser.add_subparsers(dest="command")
	start_parser = sub.add_parser("start")
	start_parser.add_argument("origin", help="Origin to forward requests to")
	start_parser.add_argument("-p", "--port", default=8000)
	sub.add_parser("stop")
	args = parser.parse_args()

	if args.clear_cache:
		clear_cache()
		print("Cache cleared")
		return
	if args.command == "start":
		start(args.origin, args.port)
	elif args.command == "stop":
		stop()
	else:
		parser.print_help()


if __name__ == "__main__":
    main()
