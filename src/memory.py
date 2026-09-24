import json, pathlib, time, datetime, sys, os
def _mem_base():
    # writable location: AppData for exe, assets for dev
    if getattr(sys, 'frozen', False):
        d = pathlib.Path(os.getenv("APPDATA", str(pathlib.Path.home()))) / "TaskbarKitten"
        d.mkdir(parents=True, exist_ok=True)
        return d / "kitten_memory.json"
    return pathlib.Path(__file__).parent.parent / "assets" / "kitten_memory.json"
MEM_PATH = _mem_base()

DEFAULT = {
    "name": None,
    "birth": None,
    "petCount": 0,
    "walkCount": 0,
    "foodBegs": 0,
    "lastPet": None,
    "lastSeen": None,
    "milestones": [],
    "favorite_spots": [],
    "pos_x": None,
    # master update fields
    "duck_trigger_source": None, # "code" | "architecture"
    "has_seen_duck_explainer": False,
    "luck_message_index": 0,
    "long_absence_hours": 2,
    "has_seen_long_absence": False,
    "is_muted": False,
    "longestApartHours": 0,
    "firstPetDate": None,
}

def load():
    if MEM_PATH.exists():
        try:
            data=json.loads(MEM_PATH.read_text(encoding='utf-8'))
            # merge defaults
            for k,v in DEFAULT.items():
                if k not in data:
                    data[k]=v
            return data
        except Exception:
            # recover from backup instead of silently returning {} / overwriting
            try:
                bak_path=pathlib.Path(str(MEM_PATH)+".bak")
                data=json.loads(bak_path.read_text(encoding='utf-8'))
                for k,v in DEFAULT.items():
                    if k not in data:
                        data[k]=v
                # snapshot the GOOD backup before any write, so a crash between
                # now and the repaired save can never leave us with no copy.
                try:
                    pathlib.Path(str(bak_path)+".recovered."+str(int(time.time()))).write_text(
                        json.dumps(data, indent=2), encoding='utf-8')
                except Exception:
                    pass
                save(data)
                return data
            except Exception:
                _quarantine(MEM_PATH)
    return dict(DEFAULT)

def _quarantine(p):
    try:
        p.rename(pathlib.Path(str(p)+".corrupt."+str(int(time.time()))))
    except Exception:
        pass

def save(data):
    try:
        tmp=pathlib.Path(str(MEM_PATH)+".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        if MEM_PATH.exists():
            try:
                # only rotate .bak when the current main is VALID json; a corrupt
                # main must never overwrite the one good backup (that was the
                # recovery-destroys-only-copy bug).
                prev=MEM_PATH.read_text(encoding='utf-8')
                json.loads(prev)
                pathlib.Path(str(MEM_PATH)+".bak").write_text(prev, encoding='utf-8')
            except Exception:
                pass
        tmp.replace(MEM_PATH)
    except Exception:
        pass

def days_since(last_iso):
    if not last_iso: return 999
    try:
        dt=datetime.datetime.fromisoformat(last_iso)
        return (datetime.datetime.now() - dt).days
    except: return 999

def hours_since(last_iso):
    if not last_iso: return 9999
    try:
        dt=datetime.datetime.fromisoformat(last_iso)
        return (datetime.datetime.now() - dt).total_seconds()/3600
    except: return 9999

def ensure_birth(data):
    if not data.get("birth"):
        data["birth"]=datetime.datetime.now().isoformat()
        save(data)
    return data
