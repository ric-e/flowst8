import os
import signal
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def start_process(command: list[str], cwd: Path) -> subprocess.Popen:
    return subprocess.Popen(command, cwd=str(cwd))


def terminate_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        if process.poll() is None:
            process.wait(timeout=10)


def main() -> int:
    backend_host = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port = os.getenv("BACKEND_PORT", "8000")
    frontend_host = os.getenv("FRONTEND_HOST", "0.0.0.0")
    frontend_port = os.getenv("FRONTEND_PORT", "3000")

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        backend_host,
        "--port",
        backend_port,
    ]
    frontend_cmd = [
        "npm",
        "--prefix",
        "frontend",
        "run",
        "dev",
        "--",
        "--hostname",
        frontend_host,
        "--port",
        frontend_port,
    ]

    processes = [
        start_process(backend_cmd, ROOT),
        start_process(frontend_cmd, ROOT),
    ]

    def shutdown_handler(signum, frame):
        del signum, frame
        terminate_processes(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    exit_code = 0
    try:
        for process in processes:
            code = process.wait()
            if code != 0:
                exit_code = code
                break
    finally:
        terminate_processes(processes)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
