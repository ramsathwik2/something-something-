# MADHU — Taskbar Kitten · Master Reference & Prompt

> Everything about this project in one file — the single source of truth for
> what Madhu is, who she is for, every feature, and every technical detail.
> If you return to this codebase years from now, or hand this file to an AI,
> it should be enough to get fully oriented and safely edit the code.

## Table of Contents
1. Identity
2. Who it is for
3. Feature list (everything)
4. Architecture & files
5. Menus
6. Memory & persistence
7. The journal
8. Animation system
9. Walking & taskbar placement
10. Sound
11. App glue, tray & threading
12. Activity monitor
13. Cooldowns & behavior timing
14. Testing
15. Build & release pipeline
16. Git & repository hygiene
17. Known limitations
18. Gotchas for future edits
19. The master prompt (paste-ready)

---

## 1. Identity

**Madhu** is a tiny 56x56 pixel cat that lives on the Windows taskbar. She is
two things at once:

1. A **virtual pet** - she walks, sleeps, gets petted, wishes luck,
   celebrates milestones, and reacts to how long you have been away.
2. A **private keepsake journal keeper** - "Gayathree's Journal", a book that
   "Madhu keeps for you", with daily pages, moods, ratings, tags, photos,
   rich-text formatting, statistics, a password lock, and export.

Naming: on first run a dialog asks "what will you call her?" (default
suggestion **"Madhu"**). That name appears everywhere: the root window title,
the right-click menu item `Pet <name> <3`, and the tray. Stored in memory under
`name`.

Personality/voice: affectionate, low-key, playful, reassuring, warm; small
hearts `<3`, short sentences, all text in English.

## 2. Who it is for

- **Gayathree** - the person Madhu was built for. An architecture / studio /
  3D-modeling student, which is why the encouragement ("luck") lines are
  architecture- and model-building-themed (e.g. *"Architecture is patience -
  your lines will find their place"*, *"One more extrude and you will see it"*).
- Single user, personal gift, **Windows-only**: uses Win32 APIs (taskbar rect,
  named mutex, MessageBox, winsound). It will never need to be macOS/Linux.
- Not a product, not public. Treat voice/spelling changes as personal taste,
  not bugs to "normalize".

## 3. Feature list (everything)

### 3.1 Pet behaviors
| Feature | Where / trigger | Notes |
|---|---|---|
| Sits on taskbar | startup | placement `above` (floating) or `overlay` (sits ON the bar) |
| Idle animation | always | `frame_0..7.png` idle frames |
| Sleeping | idle timeout | slow-breathing sleep frames; night (22:00-06:00) sleeps right away |
| Nap easter-egg | during sleep, rare | occasional stretch/blink out of sleep, then back; 90 s cooldown |
| Walking | auto-bored + menu "Walk now (bored)" | clamped inside the taskbar lane; pauses for pet/luck |
| Petting | left-click, menu `Pet <name> <3`, tray | pet animation + counter + optional meow + occasional heart |
| Mood on startup | app start | night = sleeps; gone >= 3 days = big greeting; 1 day = small |
| Long-absence check | every ~30 min | bubble when away longer than threshold (default 2 h) |
| Duck mode (coding) | menu "Duck mode (coding)" + auto via activity | "duck = don't bug me": no walking, sits/sleeps; see 12 |
| Don't sleep 30m | menu "Don't sleep 30m" | blocks sleeping for 30 min; menu label counts down |

### 3.2 Talk & bubbles
- Speech bubble above the kitten. Signature:
  `_show_bubble(text, ms=4000, priority=0)`. Priority `1` preempts/merges
  (see 13).
- Messages currently fired:
  - Name dialog: `Hi, I'm <name>! <3`
  - Fruit/wake/long absence: `Missed you!` variants
  - Milestones (pet counts + anniversaries), see 3.4
  - **11:11 wish**: `11:11 AM/PM -- make a wish` (priority 1, 7 s)
  - **Seasonal**: Christmas (Dec 20-26), Valentine's (Feb 13-15),
    Halloween (Oct 30-31) - 15% chance per check, latched once/year in memory
  - **Journal reminder**: text at configured time (default 21:00), whole-minute
    window, once/day; or "Journal done today - proud of you" if already journaled
- Text lives inline in `pet_window.py` (`LUCK_MESSAGES`, milestone strings,
  greetings).

### 3.3 Luck & encouragement
- **Wish me luck** - menu + tray. Rotates sequentially through `LUCK_MESSAGES`
  (150 architecture/studio lines); index stored in memory (`luck_message_index`,
  wraps modulo). Bubble priority 1; walk pauses during it.

### 3.4 Milestones (persisted once, never repeated)
| Milestone | Trigger |
|---|---|
| `pet1` | first pet ever - "First pet! <name> loves you" |
| `pet10` | 10 pets - "10 pets already? Lucky <name>" |
| `pet100` | 100 pets - "100 pets! <name> is so loved" |
| `pet500` | 500 pets - "500 pets! You're <name>'s favorite human" |
| `week1` | 7 days since birth - "1 week together!" |
| `month1` | 30 days since birth - "1 month with <name>!" |

All newly-fired milestones in one tick merge into ONE bubble (`"; ".join`),
one meow, one size "pop" burst.

### 3.5 The journal (the "book") - internals in 7
Password gate, then a book-styled window (parchment, spine, two pages):
- Daily pages (one entry per date), auto-create, backdate, delete.
- Mood: one of 6 emojis (buttons).  Rating: 1-5 hearts (tap to unset).
- Tags: 6 fixed - love, us, study, thoughts, dreams, today.
- Rich text: bold / italic / underline / color / link / heading / bullet /
  todo checkbox, re-applied on load.
- Photos: attach images, stored under `journal_photos/`, inline thumbnails.
- Word count, debounced auto-save, manual "Save for Madhu".
- Search filters the day list (never steals selection while searching).
- Calendar & insights: streak, top tags, mood/rating trends; click a day to jump.
- Dark mode toggle (per-session via `_journal_dark_cur`).
- Export text (.txt) and PDF (.pdf) - ALL or today-only (multi-page PDF).
- Password lock (Fernet + scrypt, see 7.3) and reminder (3.2).

### 3.6 Journal reminder
Default 21:00; change via the `reminder` button (HH:MM, 24 h). Stored in
memory `journal_hour`/`journal_min`. Fires for the WHOLE target minute, once
per day (latched by date_hour_minute slot).

### 3.7 Our story
Small read-only scrapbook: days together, pet counts, milestones, longest time
apart. Not a separate journal.

### 3.8 Tray (pystray)
Icon = `frame_4.png`. Menu with dynamic labels:
`Placement: Above`, `Placement: Overlay (ON taskbar)`, separator,
`Pet <name> <3`, `Wish me luck`, `Our story`, `Mute/Unmute` (label updates
live via `icon.update_menu()`), `Quit`.

### 3.9 System integration
- Single instance via Win32 mutex; second launch shows a MessageBox
  "Madhu is already running..." and exits.
- Auto-open journal: env `KITTY_OPEN_JOURNAL=1` or arg `--open-journal`.

## 4. Architecture & files

```
D:\KITTY\
|- MASTER.md                  <- this file
|- build_installer.bat        <- PyInstaller build script (see 15)
|- Kitty.spec                 <- PyInstaller spec (gitignored; keep in sync with the .bat)
|- KittySetup.exe             <- Inno Setup output, TRACKED in git (served from GitHub raw)
|- src/
|  |- app.py                  <- entry point: mutex, memory, tray, monitor, mainloop
|  |- pet_window.py           <- PetWindow: ALL UI, behaviors, journal (largest file, ~4700 lines)
|  |- animator.py             <- SpriteAnimator: state machine / frame selection
|  |- taskbar.py              <- Win32 taskbar geometry helpers
|  |- activity.py             <- ActivityMonitor (CPU/process polling, 1 s)
|  |- memory.py               <- persistent memory JSON (the pet's brain)
|- assets/
|  |- sprites/                <- PNG kit (see 8)
|  |- meow.wav                <- the ONLY sound file (bundled)
|  |- journal.json            <- DEV copy of the journal (gitignored)
|  |- journal_photos/         <- attached photos (gitignored)
|  |- kitten_memory.json      <- DEV memory (gitignored) (+ .bak backup)
|- installer/
|  `- kitty.iss               <- Inno Setup script -> KittySetup.exe
|- _test_journal.py           <- journal UI regression suite (16 checks)
|- _test_lock.py              <- journal lock regression suite (11 checks)
|- %TEMP%\opencode\test_walkfix.py, test_dontsleep.py  <- behavioral suites (13 / 23)
```

### 4.1 `PetWindow(SPRITE_DIR)` - the core
Class in `src/pet_window.py`. Constructor takes a sprite dir path. Owns the
Tk root, label/canvas, right-click menu, memory, animator, journal, bubbles,
walks, sounds, milestones. Key instance state (other features read it - do not
rename/drop):
```python
self.root, self.label, self.animator
self.kitten_name            # from memory["name"]
self.pet_w, self.pet_h      # 56, 56
self.is_duck / self.duck_side
self.walk_active / self.bored_since / self.is_petting
self.last_activity
self._modal_open            # True while the name dialog is up
self._startup_greeted
self._ui_queue              # post_ui queue (thread safety)
self._last_sound_ts         # sound throttle
self._journal_read_error    # hard-blocks further journal saves if a load was corrupt
self._unlock_fails          # password throttle counter
```

### 4.2 Threading model (critical)
- Tk runs on the MAIN thread only.
- The activity monitor and pystray run on their own threads. Any UI command
  from those threads MUST be marshaled via `pet.post_ui(callable)`, which
  pushes onto `_ui_queue`; `_drain_ui()` runs every 300 ms inside the Tk main
  loop and executes the queued lambdas. Never call `root.after`/widget methods
  directly from non-Tk threads.

## 5. Menus

### 5.1 Kitten right-click menu (Tk `self.menu`)
Indices are ABSOLUTE and count separators. `entryconfig(4)` renames the pet
item; `entryconfig(9)` is the Mute label (both asserted by tests).

| Index | Label | Command / note |
|---|---|---|
| 0 | Placement: Above (floating) | `set_placement("above")` |
| 1 | Placement: Overlay (on taskbar) | `set_placement("overlay")` |
| 2 | (separator) | |
| 3 | Walk now (bored) | `trigger_walk` |
| 4 | Pet <name> <3 | `trigger_pet` |
| 5 | Gayathree's Journal | `show_journal` |
| 6 | Wish me luck | `trigger_luck` |
| 7 | Our story | `show_scrapbook` |
| 8 | Don't sleep 30m | `toggle_dont_sleep`; label becomes checked + minutes left |
| 9 | Mute / Unmute | `toggle_mute` |
| 10 | Duck mode (coding) | `toggle_duck` |
| 11 | (separator) | |
| 12 | Quit | `quit` |

### 5.2 Tray menu (pystray)
See 3.8. Dynamic labels `Pet <name> <3` and `Mute/Unmute` are CALLABLES
reading `pet.tray_state = {"name", "muted"}`; `toggle_mute` updates the dict
and calls `icon.update_menu()`.

## 6. Memory & persistence

File: `src/memory.py`.
- Path: frozen -> `%APPDATA%\TaskbarKitten\kitten_memory.json`;
  dev -> `D:\KITTY\assets\kitten_memory.json`.
- Persistence strategy (never lose data):
  - `save(data)`: write `x.tmp`, back up existing to `x.bak`, then
    `tmp.replace(x)` (atomic on NTFS).
  - `load()`: parse JSON, merge `DEFAULT` for missing keys. On corrupt JSON:
    try `.bak`; else quarantine as `x.corrupt.<epoch>` and return `DEFAULT`.
- Helpers: `days_since(iso)`, `hours_since(iso)`, `ensure_birth(data)`.

Memory keys (`memory.DEFAULT`; consumed across the app):
```python
name                # kitten name (None until first-run dialog)
birth               # ISO birth timestamp (first run)
petCount            # total pets
walkCount           # total walks
foodBegs            # reserved (no feed feature)
lastPet / lastSeen  # ISO timestamps for absence / greeting math
milestones          # list of fired milestone ids (pet1, pet10, ...)
favorite_spots      # reserved list
pos_x               # last walk x (position survives restarts)
duck_trigger_source # None | "code" | "architecture" (why duck engaged)
has_seen_duck_explainer  # one-time duck explanation bubble
luck_message_index  # rotating pointer into LUCK_MESSAGES
long_absence_hours  # away-threshold for "you were away" (default 2)
has_seen_long_absence    # latch
is_muted            # drives tray label, sound, mute menu item
longestApartHours   # worst absence seen
firstPetDate        # ISO of first pet
# journal reminder
journal_hour / journal_min   # reminder time (default 21:00)
```

## 7. The journal

### 7.1 Where it lives
- Dev: `D:\KITTY\assets\journal.json` + `assets/journal_photos/`
- Frozen: `%APPDATA%\TaskbarKitten\journal.json` + `journal_photos/`
- Migration (runs once, `_migrate_legacy_journal`): folds the dev-tree
  journal/photos into the active path when the active path lacks entries -
  active entries win field-by-field; photos copied if missing. Guarded by
  `self._journal_migrated`.

### 7.2 Entry schema (one key per YYYY-MM-DD)
```json
{
  "text": "the page text",
  "fmt":  [[8,21,"bold"], [30,45,"italic"], [50,70,"heading"], [120,140,"todo"]],
  "mood": "emoji",
  "rating": 4,
  "tags": ["love", "today"],
  "photos": ["153000_719_x.png"],
  "ts": "2026-09-19 14:41"
}
```
- Legacy "seq" format `[text, mood, rating, tags, photos(, ts)]` is still
  auto-converted on load (`_entry_seq`). Keep reading it; never write it.
- Persisted fmt tag names: `bold`, `italic`, `underline`, `heading`, `bullet`,
  `todo`, `color_#hex` (color), `link_...` (link). `todo_done` is derived
  (dim color + overstrike in both themes).
- Canonical getters: `_entry_text/_mood/_rating/_tags/_photos/_seq/_populated`.

### 7.3 Security (lock)
- Minimum password length **6**. Salt is random 16 bytes (`secrets.token_bytes`).
- Key = `scrypt(pw, salt, n=2**14, r=8, p=1, dklen=32)`.
- Files: `journal.enc` = Fernet-encrypted JSON; `journal.lock.json` =
  `{"salt": hex, "check": key-hex}`.
- Locking ORDER (critical): encrypt -> write enc atomically (tmp+replace) ->
  write lock file -> delete plaintext + `.bak`/`.tmp`. Relock ABORTS if the
  existing enc cannot be decrypted with the held key (prevents encrypting {}
  over a real journal).
- Unlock: compare `check` with `hmac.compare_digest`, cache `_journal_key`,
  set `_journal_unlocked`. Throttle: 5 wrong tries -> gate closes.
- Removing the lock writes PLANTEXT DIRECTLY (must bypass `_save_journal`,
  which would re-encrypt while the lock still exists and the data would be
  lost), then deletes enc/lock/temps. `.enc.bak` kept as decrypt fallback.

### 7.4 Export
- Text (`_journal_write_txt`): readable dump; supports today-only.
- PDF (`_journal_write_pdf`): hand-rolled PDF 1.4, MULTI-PAGE (page break at
  46 lines / y < 45), Type1 Helvetica, Latin-1 only. Non-Latin-1 chars are
  transliterated by module-level `_PDF_TRANSLIT` (accents->ASCII, smart
  quotes->ASCII, emoji->* or space). Keep object numbering:
  Catalog=1, Pages=2, page=3+2i, its content=4+2i, font=3+2n.

### 7.5 Rich-text reload (`_apply_fmt`)
Stored fmt offsets are CHARACTER offsets, but embedded images occupy a widget
index yet ZERO text characters, so naive `index("1.0 + N chars")` drifts. The
fix walks `txt.dump("1.0", END)` counting only "text" items to translate the
offset. Never revert to naive char math.

### 7.6 Journal UI correctness rules (audit-derived - keep)
- `load_date(d)`: if d equals date_var AND equals `_journal_applied_date`,
  return WITHOUT wiping editor edits. Otherwise `_flush()` first. Reset
  `_journal_applied_date = None` on each window open.
- `_save` must not insert/jump into the day list while the search box has text.
- new_page / delete / add_photo / photo_delete / backdate all `_flush()` first.
- `quit()` and the window close flush via `self._journal_on_close`.
- Photo names include milliseconds (`%H%M%S_%f_stem.png`) to avoid
  same-second collisions.
- Save path copies the existing entry dict and only overwrites edited fields
  (opening a journal must never destroy stored fields).
- Do NOT re-introduce an unguarded `win.after(...)` scheduled save (the old
  mood button did `win.after(700, save)` and crashed after window close; use
  `_autosave()`).

## 8. Animation system

File: `src/animator.py`, class `SpriteAnimator`.
- State registry maps each state name to `(kind, frames_list)`; kind is one of
  `idle | sleep | walk | pet` (the switch in `next_frame`).
- `set_state(state, big=False, flip=...)` switches the visible pose.
- `set_walk_direction(dir)` only flips when the current state kind is `walk`
  AND the direction actually changed (this is what killed the random U-turn
  bug - keep it).
- Frame stepping is FRAME-LIST based, never an index into a fixed list:
  `next_frame()` picks a list per kind (pet uses pet frames / pet_big), falls
  back to `frames_big`/`frames` when the list is empty, and to `[0, 1]` when
  totally empty. All loops are `lst[seq[idx % len(seq)]]` so non-uniform frame
  counts are safe.
- Renders via Pillow `ImageTk.PhotoImage` onto the label. Headless tests stub
  `ImageTk`; keep `next_frame` importable without a display by isolating the
  Tk-dependent line.

Sprites (`assets/sprites/`): `frame_0..7.png` (idle), `walk_0..3.png`,
`pet_0..2.png`, `sheet.png`, plus `frame_4.png` (tray/app icon).

## 9. Walking & taskbar placement

### 9.1 `src/taskbar.py` (pure Win32)
```python
get_taskbar_rect()  -> (l,t,r,b) of "Shell_TrayWnd" (FindWindowW/GetWindowRect)
get_work_area()     -> SystemParametersInfoW(SPI_GETWORKAREA = 48)
get_screen_size()   -> GetSystemMetrics
get_taskbar_edge()  -> "bottom" | "top" | "left" | "right"
calc_position(pet_w, pet_h, placement="above") -> (x, y)
```
- `above`: sits just above the bar (beside it for left/right bars).
- `overlay`: sits ON the bar (pet bottom = screen bottom - 2).
- Horizontal default: ~60 px from the right edge.

### 9.2 Walking (in `pet_window.py`)
- LANE MODEL: every move is clamped by the SHARED `_lane_bounds`/`_clamp_x`;
  every entry point (trigger_walk, `_walk_step`, `_walk_to_step`,
  `update_position`, startup restore) goes through them. This is the fix for
  "invisible wall" / off-edge spawns - keep it unified.
- `walk_x` + heading persist across restarts via `memory["pos_x"]` and `_pos_file`.
- Spot walks (`_walk_to_spot`) keep the animation flywheel alive
  (`_anim_after` re-armed). Walking pauses for petting/luck/modal.
- `_walk_bob` resets on each new walk (no half-bob reappearances).
- Duck mode has no walking (the duck just doesn't roam).

## 10. Sound

- ONE sound: `assets/meow.wav` (~100 KB).
- `_play_meow(kind="meow")` - kind is now cosmetic; always plays the same wav
  via `winsound.PlaySound(path, SND_FILENAME | SND_ASYNC)`.
- Guards: `is_muted` -> silent; 1 s throttle via `_last_sound_ts`; missing wav
  -> single warning, no crash.
- Path: `self._base_dir() / "assets" / "meow.wav"`. `_base_dir()` resolves to
  `sys._MEIPASS` when frozen (bundled assets) else the repo `assets/` dir.
- pygame / MP3 / hardcoded `F:\` fallbacks were REMOVED. winsound cannot play
  MP3; do not bring them back.

## 11. App glue, tray & threading

`src/app.py main()`:
1. `acquire_single_instance()`: `CreateMutexW(NULL, FALSE,
   "Local\\TaskbarKitten_SingleInstance_Mutex")`. `GetLastError()==183`
   (ERROR_ALREADY_EXISTS) => already running => `MessageBoxW`
   ("Madhu is already running...") => return. `ReleaseMutex` on clean exit.
2. Build `PetWindow(SPRITE_DIR)`.
3. `ActivityMonitor(cpu_thresh=42)` on its own thread; results pushed via
   `pet.post_ui(pet.set_activity_state(...))`.
4. pystray icon (64x64 `frame_4.png`), menu with callable labels over
   `pet.tray_state`, all callbacks via `post_ui`.
5. Optional auto-open journal: `KITTY_OPEN_JOURNAL=1` env or `--open-journal`.
6. `pet.run()` (Tk mainloop), then `mon.stop()` and mutex release.

## 12. Activity monitor

File: `src/activity.py`. Polls CPU (threshold 42) and process count at 1 s.
Used to (a) drive `set_activity_state(active, reason)` (animation/busy state)
and (b) auto-engage Duck mode while the user is clearly coding. Reason strings
include "code" / "architecture" (`duck_trigger_source`). This is also the
origin of `cpu_thresh=42` seen in app.py.

## 13. Cooldowns & behavior timing (the short list)

| What | Timing |
|---|---|
| Sound throttle | 1 s (`_last_sound_ts`) |
| Nap easter-egg | ~90 s cooldown |
| Seasonal message | latched once per year key in memory |
| 11:11 wish | fires when now == 11:11, once per minute green light |
| Journal reminder | whole target minute, once/day (slot latch) |
| 11:11/seasonal/luck bubbles | priority 1 (preempts lower-priority bubbles) |
| `_ui_queue` drain | every 300 ms |
| Don't-sleep window | 30 min, menu label counts down |
| Long-absence check | runs every ~30 min; threshold `long_absence_hours` (2) |
| `_welcome_back` / waiting / notice-beat | internal guards gate state transitions |

General rule: any deferred behavior uses `self.root.after(...)` with a
`_ready_for_transition()` guard so it never fires mid-walk/pet/duck/modal.

## 14. Testing

Run from `D:\KITTY` (set `PYTHONIOENCODING=utf-8` on Windows; the suites build
real widgets, so a desktop session with a display is required):
```
python _test_journal.py            # 16 checks - journal persistence/UI flows
python _test_lock.py               # 11 checks - password lock/encryption round-trips
python %TEMP%\opencode\test_walkfix.py     # 13 checks - walking lane/clamp behavior
python %TEMP%\opencode\test_dontsleep.py   # 23 checks - dont-sleep + duck interplay + menu labels
python -m py_compile src\app.py src\pet_window.py src\animator.py src\memory.py src\activity.py src\taskbar.py
```
The men index facts (4 = Pet, 8 = Don't sleep, 9 = Mute) are asserted by the
suites - run them after any menu change.

## 15. Build & release pipeline

1. `python -m PyInstaller --noconfirm --windowed --onedir --name Kitty
   --add-data "assets\sprites;assets\sprites" --add-data "assets\meow.wav;assets"
   --icon "assets\sprites\frame_4.png" src\app.py`
   -> `dist\Kitty\Kitty.exe` (assets land in `_internal\assets`).
   The same flags live in `build_installer.bat` AND `Kitty.spec` - keep all
   three in sync if assets change.
2. `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\kitty.iss`
   -> `KittySetup.exe` (root of the repo; TRACKED in git).
3. Commit + push; the raw GitHub URL serves the installer:
   `https://raw.githubusercontent.com/ramsathwik2/something-something-/main/KittySetup.exe`
4. Reinstall: download and run the setup. Reinstall = the update mechanism
   (the app has no self-update).

Smoke checklist after every build (frozen app):
- Single instance (second launch -> MessageBox, no second kitten window).
- First run shows the name dialog; `%APPDATA%\TaskbarKitten\` is populated
  (kitten_memory.json + .bak, journal_photos/).
- `dist\Kitty\_internal\assets\meow.wav` exists; `cryptography` and `PIL`
  packages are bundled inside `_internal`.

## 16. Git & repository hygiene

- Repo: `https://github.com/ramsathwik2/something-something-`, branch `main`.
- NEVER `git add -A`. Always stage targeted files. Tracked: `src/*`,
  `build_installer.bat`, `installer/kitty.iss`, `KittySetup.exe`, docs.
- Gitignored (runtime/personal data): `assets/journal.json(.bak)`,
  `assets/journal.enc`, `assets/journal.lock`, `assets/journal_photos/`,
  `assets/kitten_memory.json(.bak)`, `assets/kitten_pos.txt`,
  `build/`, `dist/`, `*.spec`, `__pycache__/`.
- `Kitty.spec` is gitignored but regenerated; keep its `datas` equal to the
  `.bat` add-data flags.
- History note: a plaintext journal was accidentally committed once
  (`847f755`). Removing it from history requires rewriting history; only do
  this with explicit user permission and coordinate re-installs (raw-link
  content changes). Do NOT force-push casually.
- Commit style seen in history: `fix: ...`, `build: ...`, `chore: ...`.

## 17. Known limitations

- The password gate is an in-app lock, NOT OS-grade security. It keeps the
  journal safe from the casual reader; a determined attacker with disk access
  can always get the bytes.
- Dev and frozen builds keep SEPARATE journals (dev `assets/`, frozen
  `%APPDATA%`). The one-time migration merges them only on the machine where
  the old dev file exists in the bundle - in practice the two never truly
  converge. This is accepted.
- During an in-place upgrade, an OLD running instance does not hold the NEW
  mutex, so a few seconds of two instances can occur. Close the old kitten
  before installing.
- `winsound` is Windows-only (fine: the app is Windows-only).
- Resolution/fonts: hardcoded pixels and fixed dialog sizes; they were tuned
  on the author's 1366x768-ish screen and may look off on other DPI.
- The two code copies of the pet window logic (menu label via entryconfig and
  tray callable labels) can drift - tests catch menu drift (see 14).

## 18. Gotchas for future edits

- Menu indices COUNT separators (5.1); `entryconfig(4)`/`entryconfig(9)` are
  load-bearing.
- After any change to non-text/emoji-heavy behavior, run the six-line compile
  check + the four suites.
- `_ready_for_transition()` gates deferred `after()` lambdas; new behaviors
  must use it (walk/pet/duck/modal).
- `_save_journal` is skipped when `_journal_read_error` is True; do not turn
  that off or a corrupt journal gets repeatedly overwritten.
- Removing the journal lock writes plaintext DIRECTLY while the lock file
  still exists (7.3); do not call `_save_journal` there.
- never reference `D:\KITTY`, `F:\`, or `C:\Users\...` in code - use
  `_base_dir()` (freeze-safe). grep for backslash paths before committing.
- Sound: winsound/WAV only. If you add sounds, bundle them via `--add-data`
  and update `.bat`, `Kitty.spec`, AND `PyInstaller` args (3 places).
- `pet.post_ui` is the ONLY legal way to touch Tk from non-main threads.
- `set_duck` appears twice in pet_window.py (a short enable-only copy then the
  parameterized one). The later definition wins; don't "clean up" the first
  without re-running dontsleep tests.
- Old mp3 (`cat-purr-meow.mp3`) may still exist in assets; it is NOT used.

## 19. The master prompt (paste-ready)

Copy EVERYTHING below into an AI tool when you sit down to work on this
project again. It restores full context in one shot.

```
You are working on "Madhu", a personal Windows taskbar kitten + private
journal app written in Python (Tkinter + Pillow + pystray), for the user
"Gayathree". Read D:\KITTY\MASTER.md in FULL first - treat it as the
authoritative spec. The repo is
https://github.com/ramsathwik2/something-something-/ (branch main).
Important context to honor:
- The pet is 56x56 px living on the taskbar. src/app.py is the entry point
  (single-instance Win32 mutex, ActivityMonitor, pystray tray, mainloop).
  src/pet_window.py is the core class PetWindow (UI, behaviors, journal,
  bubbles, sounds, milestones). src/animator.py, taskbar.py, activity.py,
  memory.py support it.
- Runtime data: memory in kitten_memory.json; the journal
  (Gayathree's Journal) in journal.json + journal_photos/, optionally
  encrypted (journal.enc FERNET + scrypt, min 6-char password, 5-try
  throttle, .enc.bak fallback, atomic temp+replace writes + .bak backups).
  Dev stores these in D:\KITTY\assets\; frozen builds use
  %APPDATA%\TaskbarKitten\ (a one-time migration folds dev data in).
- Windows-only, winsound for sound (assets/meow.wav), Pillow sprites under
  assets/sprites/, DPI is hardcoded so accept minor layout quirks.
- Thread rule: Tk is main-thread-only; cross-thread calls MUST use
  pet.post_ui(...) (drained every 300 ms).
- Menu indices count separators (entryconfig(4)=Pet name, entryconfig(9)=Mute,
  index 8=Don't sleep). Tray labels are callables over pet.tray_state.
- NEVER commit things other than what I explicitly stage; never create new
  doc files without asking; never force-push; keep the app's warm, small-
  hearted voice; keep all messaging consistent with the personality in
  MASTER.md.
- Verifications: python -m py_compile on all src files, then
  python _test_journal.py (16 checks), python _test_lock.py (11),
  test_walkfix.py (13), test_dontsleep.py (23). Before any release also do
  the frozen-app smoke checklist in MASTER.md section 15.
- Build/release: update build_installer.bat, Kitty.spec and PyInstaller
  --add-data flags together; ISCC installer\kitty.iss -> KittySetup.exe;
  commit + push; the installer is distributed from the raw GitHub link.
Begin by confirming you have read MASTER.md and list what you understand the
task to be.
```