import subprocess
import os
import sys
import time

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(root_dir, "backend", ".venv", "Scripts", "python.exe")
    frontend_dir = os.path.join(root_dir, "frontend")
    pnpm_cmd = r"C:\Users\jayad\AppData\Roaming\npm\pnpm.cmd"

    CREATE_NEW_CONSOLE = 0x00000010
    flags = CREATE_NEW_CONSOLE

    # 1. Kill any stale process on 8000 or 5173
    kill_ps = (
        'Get-NetTCPConnection -LocalPort 8000, 5173 -ErrorAction SilentlyContinue | '
        'ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", kill_ps], capture_output=True)
    time.sleep(1)

    # 2. Launch backend
    backend_cmd = [
        python_exe,
        "-m", "uvicorn",
        "app.main:app",
        "--app-dir", "backend",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    p_backend = subprocess.Popen(
        backend_cmd,
        cwd=root_dir,
        creationflags=flags,
        close_fds=True
    )
    print(f"Backend launched with PID {p_backend.pid}")

    # 3. Launch frontend
    frontend_cmd = [
        pnpm_cmd,
        "dev",
        "--host", "127.0.0.1",
        "--port", "5173"
    ]
    p_frontend = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        creationflags=flags,
        close_fds=True
    )
    print(f"Frontend launched with PID {p_frontend.pid}")

if __name__ == "__main__":
    main()
