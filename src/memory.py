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
            data=json.loads(MEM_PATH.read_text())
            # merge defaults
            for k,v in DEFAULT.items():
                if k not in data:
                    data[k]=v
            return data
        except Exception:
            # recover from backup instead of silently returning {} / overwriting
            try:
                data=json.loads(pathlib.Path(str(MEM_PATH)+".bak").read_text())
                for k,v in DEFAULT.items():
                    if k not in data:
                        data[k]=v
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
        tmp.write_text(json.dumps(data, indent=2))
        if MEM_PATH.exists():
            try:
                pathlib.Path(str(MEM_PATH)+".bak").write_text(MEM_PATH.read_text())
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
