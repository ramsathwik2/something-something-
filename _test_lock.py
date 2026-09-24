import sys, pathlib, shutil, tempfile, os, json

# Self-sandboxing runner: copies src+assets to a temp dir and runs purely
# there, so no real journal/memory/lock data is ever touched on this machine.
_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE
if os.environ.get("TASKBAR_KITTEN_TEST_SANDBOX", "1") not in ("0", "false", "no"):
    import tempfile as _tf
    _tmp = pathlib.Path(_tf.mkdtemp(prefix="kitty_test_lock_"))
    shutil.copytree(ROOT / "src", _tmp / "src")
    shutil.copytree(ROOT / "assets", _tmp / "assets")
    ROOT = _tmp
    print("[sandbox]", ROOT)

sys.path.insert(0, str(ROOT / "src"))
from pet_window import PetWindow
pet = PetWindow(pathlib.Path(ROOT / "assets" / "sprites"))

# clean any existing lock
pet._journal_remove_password()

# 1. set a password
ok = pet._journal_set_password("love123")
print("set_password:", "OK" if ok else "FAIL")

# 2. journal file should be gone, enc present, lock present
jp = pet._journal_path()
print("plaintext gone:", not jp.exists())
print("lock exists:", pet._journal_lock_path().exists())
print("enc exists:", pet._journal_enc_path().exists())
print("encrypted is binary:", not pet._journal_enc_path().read_bytes().startswith(b"{"))

# 3. load is empty without key
pet._journal_key = None
print("load locked empty:", pet._load_journal() == {})

# 4. wrong password fails
pet._journal_key = None
print("wrong pw rejected:", not pet._journal_unlock("wrong"))

# 5. correct password works + data round-trips
pet._journal_key = None
print("right pw accepted:", pet._journal_unlock("love123"))
print("data round-trip:", isinstance(pet._load_journal(), dict))

# 6. save while locked then decrypt again
d = pet._load_journal()
d["2026-09-18"] = {"text": "encrypted entry kept safe", "mood": "", "rating": 0, "tags": [], "photos": [], "ts": "x"}
pet._save_journal(d)
pet._journal_key = None
print("unlock again:", pet._journal_unlock("love123"))
rd = pet._load_journal()
print("encrypted save round-trip:", rd.get("2026-09-18", {}).get("text", "") == "encrypted entry kept safe")

# finally restore plaintext and clean lock so Madhu opens unlocked for the user
pet._journal_remove_password()
pet._save_journal(rd)
print("cleanup done, plaintext:", pet._journal_path().exists())
try: pet.root.destroy()
except Exception: pass