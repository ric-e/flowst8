import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def start_process(command: list[str], cwd: Path) -> subprocess.Popen:
    return subprocess.Popen(command, cwd=str(cwd), start_new_session=True)


def terminate_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def main() -> int:
    backend_host = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port = os.getenv("BACKEND_PORT", "8000")
    frontend_host = os.getenv("FRONTEND_HOST", "127.0.0.1")
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
        "--reload",
        "--reload-dir",
        "backend/app",
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
        while True:
            statuses = [process.poll() for process in processes]
            finished_codes = [code for code in statuses if code is not None]
            if finished_codes:
                exit_code = next((code for code in finished_codes if code != 0), 0)
                break
            time.sleep(0.25)
    finally:
        terminate_processes(processes)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
