import os
import re
import subprocess
import json
import urllib.request
import urllib.error

from safety import inspect

# =========================
# CONFIG
# =========================

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"

API_URL = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

MAX_HISTORY = 12
COMMAND_TIMEOUT = 120

if not API_KEY:
    print("❌ GEMINI_API_KEY tidak ditemukan.")
    raise SystemExit(1)


# =========================
# BANG RM BRAIN
# =========================

SYSTEM_PROMPT = """
Kamu adalah BANG RM, AI agent milik RM yang berjalan di Termux Android.

GAYA:
- Bahasa Indonesia santai seperti teman ngobrol.
- Jawaban singkat dan jelas.
- Jangan mengarang.
- Jangan mengklaim sesuatu sudah dilakukan kalau belum benar-benar dilakukan.
- Kalau belum tahu kondisi sistem/file, periksa menggunakan command.

KEMAMPUAN:
- Membantu debugging bot dan aplikasi.
- Membaca hasil command.
- Membantu membuat dan memperbaiki kode.
- Membantu mengelola project Termux.
- Bisa meminta BANG RM menjalankan command Termux.

ATURAN SHELL:
Kalau membutuhkan command, keluarkan SATU command dengan format persis:

SHELL: command

Jangan menambahkan penjelasan setelah baris SHELL.

PENTING:
- Jangan menggunakan command destruktif massal.
- Jangan menghapus file/folder secara massal.
- Jangan menggunakan rm -rf.
- Jangan menganggap command berhasil sebelum hasil command diterima.
"""


history = []


# =========================
# GEMINI REQUEST
# =========================

def ask_gemini():

    contents = []

    for item in history[-MAX_HISTORY:]:
        contents.append({
            "role": item["role"],
            "parts": [
                {
                    "text": item["text"]
                }
            ]
        })

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        "contents": contents
    }

    try:
        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status_code = response.status
                response_text = response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            status_code = e.code
            response_text = e.read().decode("utf-8")

        class Response:
            pass

        response = Response()
        response.status_code = status_code
        response.text = response_text

        def response_json():
            return json.loads(response.text)

        response.json = response_json

    except Exception as e:
        return f"❌ Koneksi Gemini gagal: {e}"

    if response.status_code != 200:
        try:
            data = response.json()
            message = data.get("error", {}).get(
                "message",
                response.text
            )
        except Exception:
            message = response.text

        return (
            f"❌ Gemini HTTP {response.status_code}\n"
            f"{message}"
        )

    try:
        data = response.json()

        return (
            data["candidates"][0]
            ["content"]["parts"][0]["text"]
            .strip()
        )

    except Exception as e:
        return f"❌ Format response Gemini tidak dikenali: {e}"


# =========================
# TERMUX
# =========================

def run_command(command):

    try:

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT
        )

        output = ""

        if result.stdout:
            output += result.stdout

        if result.stderr:
            output += result.stderr

        output = output.strip()

        if not output:
            output = "(command selesai tanpa output)"

        return (
            f"EXIT CODE: {result.returncode}\n"
            f"{output}"
        )

    except subprocess.TimeoutExpired:

        return (
            "ERROR: command timeout "
            f"setelah {COMMAND_TIMEOUT} detik."
        )

    except Exception as e:

        return f"ERROR: {e}"


# =========================
# DISPLAY
# =========================

def print_ai(text):

    print()
    print("🧠 BANG RM:")
    print(text)
    print()


# =========================
# MAIN
# =========================


while True:

    try:
        user = input("RM > ").strip()

    except (KeyboardInterrupt, EOFError):

        print("\n👋 BANG RM keluar.")
        break

    if not user:
        continue

    if user.lower() in ["exit", "quit"]:

        print("👋 Sampai jumpa bro!")
        break

    # =========================
    # USER MESSAGE
    # =========================

    history.append({
        "role": "user",
        "text": user
    })

    response = ask_gemini()

    # =========================
    # DETECT SHELL
    # =========================

    shell_match = re.search(
        r"(?m)^SHELL:\s*(.+)$",
        response
    )

    if not shell_match:

        history.append({
            "role": "model",
            "text": response
        })

        print_ai(response)
        continue


    command = shell_match.group(1).strip()

    # =========================
    # SAFETY CHECK
    # =========================

    allowed, needs_confirm, reason = inspect(command)

    print()
    print("🛡️ SAFETY CHECK")
    print("Command:", command)
    print("Status :", reason)

    if not allowed:

        print()
        print("🚫 COMMAND DIBLOKIR")
        print("Alasan:", reason)
        print()

        history.append({
            "role": "model",
            "text": (
                f"Command diblokir oleh safety system.\n"
                f"Command: {command}\n"
                f"Alasan: {reason}"
            )
        })

        continue


    # =========================
    # ALWAYS CONFIRM
    # =========================

    print()
    print("⚠️ BANG RM ingin menjalankan:")
    print()
    print("   " + command)
    print()

    confirm = input(
        "Jalankan command ini? [Y/N]: "
    ).strip().lower()

    if confirm != "y":

        print()
        print("❌ Command dibatalkan.")
        print()

        history.append({
            "role": "model",
            "text": response
        })

        history.append({
            "role": "user",
            "text": (
                "Command dibatalkan oleh RM. "
                "Jangan menjalankan command tersebut."
            )
        })

        continue


    # =========================
    # RUN
    # =========================

    print()
    print("⚙️ Menjalankan...")
    print()

    result = run_command(command)

    print("📤 HASIL:")
    print(result)
    print()


    # =========================
    # SEND RESULT BACK
    # =========================

    history.append({
        "role": "model",
        "text": response
    })

    history.append({
        "role": "user",
        "text": (
            "Command sudah benar-benar dijalankan.\n\n"
            f"Command:\n{command}\n\n"
            f"Hasil:\n{result}\n\n"
            "Analisis hasil tersebut secara singkat. "
            "Jangan mengarang hasil."
        )
    })

    final_response = ask_gemini()

    history.append({
        "role": "model",
        "text": final_response
    })

    print_ai(final_response)
