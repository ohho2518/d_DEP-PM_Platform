"""ปุ่มเปิดระบบ DEP-PM — ดับเบิลคลิกครั้งเดียวแล้วใช้งานได้.

ทำไมต้องมี: การเปิดระบบต้องใช้ 2 เทอร์มินัลกับคำสั่ง 6 บรรทัด (venv · alembic · uvicorn ·
npm) และพลาดง่ายอยู่ 3 จุดที่เคยเกิดจริงบนเครื่องนี้ — สตาร์ต uvicorn ซ้อนกัน 2 ตัวบนพอร์ต
เดียว · ลืม `alembic upgrade head` หลังดึงโค้ดใหม่ · `NEXT_PUBLIC_API_TOKEN` ไม่ตรงกับ
`API_TOKEN` แล้วหน้าเว็บโดน 401 ทั้งหน้าโดยไม่บอกสาเหตุ

สิ่งที่ **ไม่ทำ** โดยตั้งใจ:

* ไม่แตะพอร์ต 8000 (d_CEO) และ 8400 (d_Jarvis) — ของระบบอื่นที่รันค้างตลอด (AGENTS.md §3.1)
* ไม่สร้าง venv / ไม่ลง dependency ของ backend ให้ — เป็นงานติดตั้งครั้งแรกที่ต้องมีคนดู
* ไม่แก้ค่าใน `.env` ที่มีอยู่แล้ว (สร้างให้เฉพาะตอนยังไม่มีไฟล์ โดยลอกจาก `.env.example`)
* ไม่ commit / ไม่ push / ไม่ลบอะไรทั้งสิ้น
"""
from __future__ import annotations

import ctypes
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

#: พอร์ตของระบบนี้ (ทะเบียนกลาง: _CANON\SERVICE_PORTS.md)
BACKEND_PORT = 8500
FRONTEND_PORT = 3000

#: พอร์ตของระบบอื่นในบ้านเดียวกัน — **ห้ามแตะ** แค่รายงานว่าเป็นยังไง
NEIGHBOURS = {8000: "d_CEO", 8400: "d_Jarvis web"}

#: รอ backend ตอบ /health นานสุดกี่วินาที (เครื่องเย็น ๆ import SDK ช้ากว่าปกติ)
BACKEND_TIMEOUT = 60
#: รอ frontend เปิดพอร์ตนานสุดกี่วินาที (`next dev` compile ครั้งแรกนานกว่านั้นมาก แต่พอร์ตเปิดก่อน)
FRONTEND_TIMEOUT = 120


class Abort(RuntimeError):
    """เงื่อนไขที่ไปต่อไม่ได้ พร้อมข้อความที่บอกวิธีแก้ให้คนอ่าน."""


# --- หน้าจอ -------------------------------------------------------------------


def _enable_utf8_console() -> None:
    """บังคับ console เป็น UTF-8 — ไม่งั้นข้อความไทยออกมาเป็นขยะบนเครื่อง Windows ไทย."""
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:  # noqa: BLE001 — แค่ความสวยงาม ห้ามทำให้ตัวเปิดระบบพัง
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def say(message: str = "") -> None:
    print(message, flush=True)


def step(message: str) -> None:
    say(f"  · {message}")


def ok(message: str) -> None:
    say(f"  ✔ {message}")


def warn(message: str) -> None:
    say(f"  ⚠ {message}")


# --- หาที่ตั้งของรีโป ------------------------------------------------------------


def find_repo_root() -> Path:
    """หาโฟลเดอร์รีโปจากตำแหน่งไฟล์นี้ (หรือของ .exe) โดยไล่ขึ้นไปหาหลักฐาน 2 ชิ้น.

    ไม่ใช้ CWD เพราะดับเบิลคลิกจาก Explorer ได้ CWD เป็นอะไรก็ได้
    """
    if getattr(sys, "frozen", False):  # ถูกแพ็กเป็น .exe แล้ว
        start = Path(sys.executable).resolve().parent
    else:
        start = Path(__file__).resolve().parent

    for candidate in (start, *start.parents):
        if (candidate / "backend" / "app" / "main.py").exists() and (
            candidate / "frontend" / "package.json"
        ).exists():
            return candidate
    raise Abort(
        "หาโฟลเดอร์ DEP-PM ไม่เจอ — วางไฟล์นี้ไว้ในโฟลเดอร์รีโป (ที่มี backend\\ และ frontend\\)\n"
        f"    ตอนนี้มองจาก: {start}"
    )


# --- ตรวจของที่ต้องมีก่อน ---------------------------------------------------------


@dataclass
class Paths:
    root: Path

    @property
    def backend(self) -> Path:
        return self.root / "backend"

    @property
    def frontend(self) -> Path:
        return self.root / "frontend"

    @property
    def python(self) -> Path:
        return self.backend / ".venv" / "Scripts" / "python.exe"

    @property
    def db(self) -> Path:
        return self.backend / "dep_pm.db"

    @property
    def logs(self) -> Path:
        return self.root / "logs"


def check_python(paths: Paths) -> None:
    if not paths.python.exists():
        raise Abort(
            "ยังไม่มี virtualenv ของ backend — ติดตั้งครั้งแรกด้วยคำสั่งนี้ (ทำครั้งเดียว):\n"
            f"    cd \"{paths.backend}\"\n"
            "    python -m venv .venv\n"
            "    .venv\\Scripts\\pip install -r requirements.txt"
        )
    ok(f"virtualenv ของ backend: {paths.python.parent.parent}")


def ensure_env_files(paths: Paths) -> None:
    """สร้าง `.env` จากตัวอย่าง **เฉพาะตอนยังไม่มี** — ของที่มีอยู่แล้วห้ามแตะ (มีคีย์จริง)."""
    pairs = [
        (paths.backend / ".env", paths.backend / ".env.example"),
        (paths.frontend / ".env.local", paths.frontend / ".env.local.example"),
    ]
    for target, example in pairs:
        if target.exists():
            continue
        if not example.exists():
            raise Abort(f"ไม่มีทั้ง {target.name} และไฟล์ตัวอย่างของมัน — รีโปไม่ครบ")
        shutil.copyfile(example, target)
        warn(f"สร้าง {target.name} จากตัวอย่างให้แล้ว — ยังไม่มีคีย์ AI จริงในนั้น")
        warn("   เปิดหน้า ⚙ ตั้งค่า AI (/settings) แล้วกรอกคีย์ ระบบถึงจะเรียกโมเดลจริงได้")


def _read_env_value(path: Path, key: str) -> str:
    """อ่านค่าตัวแปรเดียวจากไฟล์ .env — **ห้ามพิมพ์ค่าที่ได้ออกจอ** (เป็นความลับ)."""
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith(f"{key}=") and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    return ""


def check_api_token_match(paths: Paths) -> None:
    """`API_TOKEN` กับ `NEXT_PUBLIC_API_TOKEN` ต้องตรงกัน ไม่งั้นหน้าเว็บโดน 401 ทั้งหน้า.

    อาการเวลาไม่ตรงคือ "โหลดบอร์ดไม่ได้" เฉย ๆ ซึ่งชวนให้ไปไล่หาที่ backend ผิดที่ —
    ตรวจตรงนี้ทีเดียวจบ · เทียบกันเท่านั้น **ไม่พิมพ์ค่าออกจอ**
    """
    backend_token = _read_env_value(paths.backend / ".env", "API_TOKEN")
    frontend_token = _read_env_value(paths.frontend / ".env.local", "NEXT_PUBLIC_API_TOKEN")
    if not backend_token:
        ok("ประตูหน้าบ้าน: ปิดอยู่ (ไม่ได้ตั้ง API_TOKEN — โหมด dev บนเครื่องนี้)")
        return
    if backend_token == frontend_token:
        ok("ประตูหน้าบ้าน: เปิดอยู่ และ token ของหน้าเว็บตรงกับ backend")
        return
    warn("API_TOKEN ของ backend ไม่ตรงกับ NEXT_PUBLIC_API_TOKEN ของหน้าเว็บ")
    warn("   ⇒ หน้าเว็บจะขึ้น 'โหลดบอร์ดไม่ได้' ทั้งที่ backend ปกติดี")
    warn(f"   แก้ที่ {paths.frontend / '.env.local'} ให้ค่าตรงกับ {paths.backend / '.env'}")


# --- ฐานข้อมูล -----------------------------------------------------------------


def _alembic(paths: Paths, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(paths.python), "-m", "alembic", *args],
        cwd=paths.backend,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def upgrade_database_if_needed(paths: Paths) -> None:
    """อัปเกรด schema ให้ตรง head — **สำรองไฟล์ฐานข้อมูลก่อนเสมอ** (WORKING_RULES Rule 3).

    `dep_pm.db` คือข้อมูลจริงของผู้ใช้ · การอัปเกรดอัตโนมัติจึงยอมได้เฉพาะเมื่อมีสำเนาแล้ว
    """
    current = _alembic(paths, "current")
    if current.returncode != 0:
        warn("ตรวจเวอร์ชันฐานข้อมูลไม่ได้ — ข้ามขั้นนี้ไปก่อน (ระบบอาจสตาร์ตไม่ขึ้นถ้า schema เก่า)")
        warn(f"   {current.stderr.strip().splitlines()[-1] if current.stderr.strip() else ''}")
        return

    if "(head)" in current.stdout:
        ok("ฐานข้อมูล: เป็นรุ่นล่าสุดอยู่แล้ว")
        return

    if paths.db.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = paths.root / "BackUp" / f"Launcher_{stamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paths.db, backup_dir / paths.db.name)
        step(f"สำรองฐานข้อมูลไว้ที่ BackUp\\{backup_dir.name}\\ ก่อนอัปเกรด")

    step("อัปเกรดฐานข้อมูลให้ตรงกับโค้ด (alembic upgrade head)…")
    result = _alembic(paths, "upgrade", "head")
    if result.returncode != 0:
        raise Abort(
            "อัปเกรดฐานข้อมูลไม่สำเร็จ — ระบบยังไม่ถูกสตาร์ต ข้อมูลเดิมไม่ถูกแตะ\n"
            f"    {result.stderr.strip()}"
        )
    ok("ฐานข้อมูล: อัปเกรดเรียบร้อย")


# --- พอร์ต / กระบวนการ ----------------------------------------------------------


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def backend_healthy() -> dict | None:
    """ถาม `/health` — คืน None ถ้ายังไม่ตอบ (ยังไม่ขึ้น หรือขึ้นแต่ยังไม่พร้อม)."""
    import json

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{BACKEND_PORT}/health", timeout=3
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError):
        return None


def _spawn(command: list[str], cwd: Path, log_path: Path) -> subprocess.Popen:
    """สตาร์ตกระบวนการเบื้องหลัง เขียน log ลงไฟล์ (ไม่มีหน้าต่างเด้ง)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("a", encoding="utf-8", errors="replace")
    handle.write(f"\n===== เริ่มรอบใหม่ {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
    handle.flush()
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    return subprocess.Popen(
        command, cwd=str(cwd), stdout=handle, stderr=subprocess.STDOUT, creationflags=flags
    )


def _kill_tree(pid: int) -> None:
    """ปิดทั้งต้นไม้ของกระบวนการ — `npm run dev` แตกลูกหลาน ฆ่าแค่ตัวแม่ไม่พอ."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False
        )
    else:
        os.kill(pid, 15)


def _stop_tree(process: subprocess.Popen) -> None:
    if process.poll() is None:
        _kill_tree(process.pid)


def pids_on_port(port: int) -> list[int]:
    """PID ที่ฟังอยู่บนพอร์ตนี้ — ใช้ตอนต้องหยุดระบบที่รอบก่อนสตาร์ตทิ้งไว้.

    อ่านจาก `netstat -ano` แทนการลง psutil เพิ่ม (กติกา §9.6: ไม่เพิ่ม dependency ถ้าไม่จำเป็น)
    """
    if os.name != "nt":
        return []
    result = subprocess.run(
        ["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, check=False
    )
    pids: list[int] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[3] == "LISTENING" and parts[1].endswith(f":{port}"):
            try:
                pid = int(parts[4])
            except ValueError:
                continue
            if pid and pid not in pids:
                pids.append(pid)
    return pids


def _wait_until(condition, timeout: int, label: str) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(1)
    warn(f"{label} ยังไม่ตอบใน {timeout} วินาที — ดู log ในโฟลเดอร์ logs\\")
    return False


# --- ตัวเปิดจริง ---------------------------------------------------------------


@dataclass
class Started:
    """สิ่งที่ **ตัวนี้** สตาร์ตขึ้นมาเอง — ของที่รันอยู่ก่อนแล้วไม่นับ (ห้ามไปปิดของคนอื่น)."""

    backend: subprocess.Popen | None = None
    frontend: subprocess.Popen | None = None

    @property
    def anything(self) -> bool:
        return bool(self.backend or self.frontend)


def start_backend(paths: Paths, started: Started) -> None:
    if port_busy(BACKEND_PORT):
        health = backend_healthy()
        if health is None:
            raise Abort(
                f"พอร์ต {BACKEND_PORT} มีคนใช้อยู่แต่ไม่ใช่ DEP-PM (ไม่ตอบ /health)\n"
                "    ปิดโปรแกรมที่ถือพอร์ตนั้นก่อน แล้วเปิดใหม่"
            )
        ok(f"backend รันอยู่แล้วที่ :{BACKEND_PORT} — ใช้ตัวเดิม ไม่สตาร์ตซ้อน")
        return

    step(f"สตาร์ต backend ที่ :{BACKEND_PORT}…")
    started.backend = _spawn(
        [str(paths.python), "-m", "uvicorn", "app.main:app", "--port", str(BACKEND_PORT)],
        paths.backend,
        paths.logs / "backend.log",
    )
    if _wait_until(lambda: backend_healthy() is not None, BACKEND_TIMEOUT, "backend"):
        ok(f"backend พร้อมที่ http://127.0.0.1:{BACKEND_PORT}")


def start_frontend(paths: Paths, started: Started) -> None:
    if port_busy(FRONTEND_PORT):
        ok(f"หน้าเว็บรันอยู่แล้วที่ :{FRONTEND_PORT} — ใช้ตัวเดิม")
        return

    if not (paths.frontend / "node_modules").exists():
        step("ยังไม่มี node_modules — ลง dependency ของหน้าเว็บ (ครั้งแรกใช้เวลาหลายนาที)…")
        result = subprocess.run(
            ["npm.cmd" if os.name == "nt" else "npm", "install"],
            cwd=str(paths.frontend),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise Abort(f"npm install ไม่สำเร็จ:\n    {result.stderr.strip()[-500:]}")
        ok("ลง dependency ของหน้าเว็บเรียบร้อย")

    step(f"สตาร์ตหน้าเว็บที่ :{FRONTEND_PORT}…")
    started.frontend = _spawn(
        ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"],
        paths.frontend,
        paths.logs / "frontend.log",
    )
    if _wait_until(lambda: port_busy(FRONTEND_PORT), FRONTEND_TIMEOUT, "หน้าเว็บ"):
        ok(f"หน้าเว็บพร้อมที่ http://localhost:{FRONTEND_PORT}")


def report_neighbours() -> None:
    """บอกสถานะระบบข้างเคียง — ดูอย่างเดียว ไม่ยุ่ง (AGENTS.md §3.1)."""
    for port, name in NEIGHBOURS.items():
        state = "รันอยู่" if port_busy(port) else "ไม่ได้รัน"
        say(f"  · {name} (:{port}): {state}")


def report_providers() -> None:
    health = backend_healthy() or {}
    providers = health.get("llm_providers") or []
    if providers:
        ok(f"ผู้ให้บริการ AI ที่ใช้ได้: {', '.join(providers)}")
    else:
        warn("ยังไม่มีคีย์ AI สักเจ้า — ระบบจะทำงานในโหมดตัวอย่าง (ผลงานไม่ใช่ของจริง)")
        warn("   กรอกคีย์ได้ที่หน้า ⚙ ตั้งค่า AI")


def menu(started: Started) -> None:
    """ค้างหน้าจอไว้ให้สั่งงานต่อ — ปิดหน้าต่างเฉย ๆ ระบบยังรันอยู่ (ตั้งใจ)."""
    say()
    say("─" * 62)
    say("  [O] เปิดหน้าเว็บอีกครั้ง   [S] หยุดระบบ   [Q] ออก (ปล่อยให้รันต่อ)")
    say("─" * 62)
    blanks = 0
    while True:
        try:
            choice = input("  เลือก: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if not choice:
            # ถูกเรียกแบบไม่มีคนพิมพ์ (สคริปต์/ไปป์) — อย่าวนถามไม่จบ ปล่อยให้ระบบรันต่อ
            blanks += 1
            if blanks >= 3:
                say("  ไม่มีคนตอบ — ออกแล้ว ระบบยังรันอยู่เบื้องหลัง")
                return
            continue
        blanks = 0
        if choice == "o":
            webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
        elif choice == "s":
            stop_all(started)
            return
        elif choice == "q":
            say("  ออกแล้ว — ระบบยังรันอยู่เบื้องหลัง (เปิดตัวนี้อีกครั้งเพื่อหยุด)")
            return


def cleanup(started: Started) -> None:
    """เก็บกวาดเฉพาะสิ่งที่ **รอบนี้สตาร์ตเอง** — ใช้ตอนเปิดไม่สำเร็จกลางคัน.

    ห้ามใช้ `stop_all` แทน: ถ้าเปิดล้มเหลวเพราะขั้นตอนก่อนหน้า ระบบที่รันอยู่ก่อนแล้ว
    (ซึ่งยังทำงานได้ดี) ต้องไม่ถูกดับไปด้วยความผิดพลาดของตัวเปิด
    """
    for process in (started.frontend, started.backend):
        if process is not None:
            _stop_tree(process)


def stop_all(started: Started) -> None:
    """หยุดระบบ — ทั้งตัวที่รอบนี้สตาร์ตเอง และตัวที่รอบก่อนทิ้งไว้.

    ต้องหยุดของรอบก่อนได้ด้วย ไม่งั้นปิดหน้าต่างไปแล้วเปิดใหม่จะกดหยุดไม่ได้เลย ต้องไปไล่ฆ่า
    process เอง · **ตรวจก่อนฆ่าเสมอ**: :8500 ต้องตอบ `/health` แบบ DEP-PM ก่อน — พอร์ตนี้
    ถ้าบังเอิญเป็นของโปรแกรมอื่น เราจะไม่ไปฆ่ามัน · พอร์ต 8000/8400 ไม่อยู่ในรายการนี้เลย
    """
    cleanup(started)

    stopped: list[str] = []
    if port_busy(BACKEND_PORT):
        if backend_healthy() is None and started.backend is None:
            warn(f"พอร์ต {BACKEND_PORT} เป็นของโปรแกรมอื่น (ไม่ตอบ /health) — ไม่แตะ")
        else:
            for pid in pids_on_port(BACKEND_PORT):
                _kill_tree(pid)
            stopped.append("backend")
    if port_busy(FRONTEND_PORT):
        for pid in pids_on_port(FRONTEND_PORT):
            _kill_tree(pid)
        stopped.append("หน้าเว็บ")

    if stopped:
        say(f"  หยุดแล้ว: {' · '.join(stopped)}  (d_CEO/d_Jarvis ไม่ถูกแตะ)")
    else:
        say("  ไม่มีอะไรให้หยุด — ระบบไม่ได้รันอยู่")


def main() -> int:
    _enable_utf8_console()
    say()
    say("=" * 62)
    say("  DEP-PM Platform — ปุ่มเปิดระบบ")
    say("=" * 62)

    started = Started()
    try:
        paths = Paths(find_repo_root())
        ok(f"โฟลเดอร์ระบบ: {paths.root}")

        say()
        say("[1/4] ตรวจของที่ต้องมี")
        check_python(paths)
        ensure_env_files(paths)
        check_api_token_match(paths)

        say()
        say("[2/4] ฐานข้อมูล")
        upgrade_database_if_needed(paths)

        say()
        say("[3/4] สตาร์ตระบบ")
        start_backend(paths, started)
        start_frontend(paths, started)
        report_providers()

        say()
        say("[4/4] ระบบข้างเคียง (ดูอย่างเดียว ไม่ยุ่ง)")
        report_neighbours()

        say()
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
        ok(f"เปิดเบราว์เซอร์ไปที่ http://localhost:{FRONTEND_PORT} แล้ว")
        menu(started)
        return 0

    except Abort as exc:
        say()
        say("  ✖ เปิดระบบไม่ได้")
        for line in str(exc).splitlines():
            say(f"    {line}")
        cleanup(started)
        input("\n  กด Enter เพื่อปิด…")
        return 1
    except KeyboardInterrupt:
        cleanup(started)
        return 1
    except Exception as exc:  # noqa: BLE001 — ตัวเปิดระบบห้ามตายเงียบ คนใช้ต้องเห็นเหตุ
        say()
        say(f"  ✖ เกิดข้อผิดพลาดที่ไม่ได้คาดไว้: {type(exc).__name__}: {exc}")
        cleanup(started)
        input("\n  กด Enter เพื่อปิด…")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
