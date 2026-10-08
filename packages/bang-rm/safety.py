import re
import shlex

# Command yang selalu diblokir
BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+[/~*]",
    r"\brm\s+-r[f]?\s+[/~*]",
    r"\brm\s+--no-preserve-root",
    r"\bmkfs\b",
    r"\bdd\s+.*\bof=/dev/",
    r"\bchmod\s+-R\s+777\s+/",
    r"\bchown\s+-R\s+.*\s+/",
    r":\(\)\s*\{\s*:\|:&\s*\};:",
]

# Command yang dianggap berisiko dan wajib konfirmasi
RISKY_COMMANDS = [
    "rm",
    "rmdir",
    "mv",
    "cp",
    "chmod",
    "chown",
    "kill",
    "pkill",
    "killall",
    "pkg",
    "pip",
    "pip3",
    "apt",
    "apt-get",
    "termux-reset",
]

def normalize(command):
    return command.strip().replace("\n", " ")

def command_name(command):
    try:
        parts = shlex.split(command)
        if not parts:
            return ""
        return parts[0].split("/")[-1].lower()
    except Exception:
        return ""

def is_blocked(command):
    cmd = normalize(command).lower()

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd):
            return True, "Command berpotensi menghapus/merusak sistem secara massal."

    # Jangan izinkan wildcard penghapusan seperti:
    # rm *
    # rm -f *
    # rm folder/*
    if re.search(r"\brm\b.*\*", cmd):
        return True, "Penghapusan dengan wildcard (*) diblokir."

    # Jangan izinkan operasi terhadap root filesystem
    if re.search(r"\brm\b.*(^|\s)/(\s|$)", cmd):
        return True, "Target root filesystem (/) diblokir."

    return False, ""

def needs_confirmation(command):
    name = command_name(command)

    if name in RISKY_COMMANDS:
        return True

    # Redirect/overwrite file
    if ">" in command or ">>" in command:
        return True

    # Pipe ke shell
    if re.search(r"\|\s*(sh|bash|zsh)\b", command):
        return True

    return False

def inspect(command):
    """
    Return:
      allowed      : bool
      needs_confirm: bool
      reason       : penjelasan
    """

    command = normalize(command)

    if not command:
        return False, False, "Command kosong."

    blocked, reason = is_blocked(command)

    if blocked:
        return False, False, reason

    if needs_confirmation(command):
        return True, True, "Command memiliki risiko perubahan pada sistem/file."

    return True, False, "Command relatif aman."

if __name__ == "__main__":
    print("🛡️ BANG RM SAFETY TEST")
    print()

    tests = [
        "ls -lah ~/bang_rm",
        "pwd",
        "rm test.txt",
        "rm -rf *",
        "rm -rf ~/bang_rm",
        "rm -rf /",
        "echo hello",
        "pip install requests",
    ]

    for cmd in tests:
        allowed, confirm, reason = inspect(cmd)

        if not allowed:
            status = "🛑 BLOCK"
        elif confirm:
            status = "⚠️ CONFIRM"
        else:
            status = "✅ SAFE"

        print(f"{status}  {cmd}")
        print(f"       {reason}")
        print()
