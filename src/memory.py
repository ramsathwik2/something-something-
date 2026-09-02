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
        except: pass
    return dict(DEFAULT)

def save(data):
    try:
        MEM_PATH.write_text(json.dumps(data, indent=2))
    except: pass

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
