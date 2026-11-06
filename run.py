"""Install missing dependencies and run the local API and frontend."""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
PYTHON_EXE = os.path.join(
    VENV_DIR, "Scripts" if os.name == "nt" else "bin",
    "python.exe" if os.name == "nt" else "python",
)
NPM_EXE = "npm.cmd" if os.name == "nt" else "npm"


def setup():
    if not os.path.exists(PYTHON_EXE):
        print("Creating Python virtual environment...", flush=True)
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

    print("Installing backend dependencies...", flush=True)
    subprocess.run(
        [PYTHON_EXE, "-m", "pip", "install", "-r", os.path.join(BACKEND_DIR, "requirements.txt")],
        cwd=PROJECT_DIR,
        check=True,
    )

    if not os.path.exists(os.path.join(FRONTEND_DIR, "node_modules", "vite", "bin", "vite.js")):
        print("Installing frontend dependencies...", flush=True)
        subprocess.run([NPM_EXE, "ci"], cwd=FRONTEND_DIR, check=True)


def wait_for_api(backend):
    print("Waiting for backend at http://localhost:8000/api/v1/health...", flush=True)
    for _ in range(150):
        if backend.poll() is not None:
            raise RuntimeError(f"Backend exited with code {backend.returncode}")
        try:
            with urllib.request.urlopen("http://localhost:8000/api/v1/health", timeout=2) as response:
                if response.status == 200:
                    print("Backend ready. Frontend: http://localhost:5173", flush=True)
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(2)
    raise TimeoutError("Backend did not become healthy within 5 minutes")


def main():
    setup()
    env = {**os.environ, "PYTHONPATH": BACKEND_DIR}
    backend = subprocess.Popen(
        [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=env,
    )
    try:
        wait_for_api(backend)
        subprocess.run([NPM_EXE, "run", "dev"], cwd=FRONTEND_DIR, check=True)
    finally:
        if backend.poll() is None:
            backend.terminate()
            backend.wait(timeout=10)


if __name__ == "__main__":
    main()
