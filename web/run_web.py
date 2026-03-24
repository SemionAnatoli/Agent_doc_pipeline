"""
Запуск веб-интерфейса: поднимает uvicorn и открывает страницу в браузере.
Корень проекта «Агент» определяется автоматически (родитель папки web).
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}/"


def wait_for_server(timeout_sec: float = 30.0, interval_sec: float = 0.15) -> bool:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(URL, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(interval_sec)
    return False


def main() -> None:
    if not (ROOT / "web" / "app.py").is_file():
        print("Не найден web/app.py. Проверьте структуру папок проекта.", file=sys.stderr)
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "web.app:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
        "--reload",
        "--reload-dir",
        str(ROOT),
        "--reload-include",
        "web/reload.trigger",
    ]
    popen_kw: dict = {"cwd": str(ROOT)}
    if sys.platform == "win32":
        popen_kw["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    proc = subprocess.Popen(cmd, **popen_kw)
    try:
        if wait_for_server():
            webbrowser.open(URL)
            if sys.stdout is not None and getattr(sys.stdout, "isatty", lambda: False)():
                print(f"Открыто в браузере: {URL}")
                print("Остановка сервера: Ctrl+C в этом окне.")
        else:
            if sys.stderr is not None:
                print("Сервер не ответил вовремя. Проверьте порт 8000 и логи.", file=sys.stderr)
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if sys.stdout is not None and getattr(sys.stdout, "isatty", lambda: False)():
            print("\nСервер остановлен.")


if __name__ == "__main__":
    main()
