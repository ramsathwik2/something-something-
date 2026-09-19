# Madhu — Architecture

A deep, public-safe dive into how Madhu works. For the exhaustive internal
reference (entry schemas, video-timing tables, gotchas), see `MASTER.md`.

## 1. Program flow

`src/app.py main()`

1. **Single instance** — `CreateMutexW` on `Local\TaskbarKitten_SingleInstance_Mutex`.
   If a second copy starts, a MessageBox says *"Madhu is already running..."* and it exits.
2. **PetWindow** (Tk root, 56×56 sprite label, right-click menu, memory, animator,
   journal, bubbles, walks, sounds, milestones).
3. **ActivityMonitor** (`cpu_thresh=42`) on its own thread; results marshalled to the
   UI thread with `pet.post_ui(...)`.
4. **Tray** — pystray icon (`frame_4.png`) with dynamic menu labels driven by a
   `pet.tray_state` dict (`icon.update_menu()` after changes).
5. **Auto-open journal** if `KITTY_OPEN_JOURNAL=1` or `--open-journal`.
6. `pet.run()` → Tk mainloop; then monitor stop + mutex release.

## 2. Threading model

- Tk is **main-thread-only**. The activity monitor and pystray run on their own threads.
- Any widget call from a background thread MUST go through `pet.post_ui(fn)`, which
  enqueues `fn` and executes it from `_drain_ui()` every 300 ms inside the Tk loop.
- Never call `root.after(...)` or widget methods directly from a non-Tk thread.

## 3. The pet

- **Sprites**: 56×56 PNGs in `assets/sprites/` (`frame_0..7` idle, `walk_0..3`,
  `pet_0..2`, `sheet.png`); 96×96 duck variants are scaled with NEAREST.
- **Animator**: `SpriteAnimator` is a state machine (`idle | sleep | walk | pet`).
  `next_frame()` is frame-list based — it never indexes a fixed array, and falls back
  gracefully (including to `[0,1]`) when a frame list is empty.
- **Walking**: moves are clamped to a shared taskbar lane (`_lane_bounds`/`_clamp_x`)
  from every entry point; the walk pauses for petting, luck and modals; position
  persists across restarts.

## 4. Taskbar geometry (`src/taskbar.py`)

Pure Win32 via ctypes:

- `get_taskbar_rect()` — `FindWindowW("Shell_TrayWnd")` / `GetWindowRect`
- `get_work_area()` — `SystemParametersInfoW(SPI_GETWORKAREA=48)`
- `get_taskbar_edge()` — bottom | top | left | right
- `calc_position(pet_w, pet_h, placement)` — `above` (floating off the bar) or
  `overlay` (standing on the bar)

## 5. Memory (`src/memory.py`)

- Path: dev → `assets/kitten_memory.json`; frozen → `%APPDATA%\TaskbarKitten\`.
- Writes are atomic: `*.tmp` → backup `*.bak` → `tmp.replace(...)`.
- Load falls back to `.bak`, and quarantines corrupt files as `*.corrupt.<epoch>`
  so the pet's history is never silently lost.
- Stores: name, birth, pet/walk counts, milestones, favorite spots, position,
  luck message index, mute, absence threshold, seasonal latches, journal reminder.

## 6. The journal

- **Storage**: `journal.json` (or `journal.enc` + `journal.lock` when a password is set),
  photos under `journal_photos/`. Dev uses `assets/`; frozen builds use `%APPDATA%`.
- **Entry schema**: `{ text, fmt, mood, rating, tags, photos, ts }` keyed by date.
- **Lock** (Fernet + scrypt, min 6 chars, random 16-byte salt, n=2^14 r=8 p=1:
  set = encrypt → temp+replace → lock file → delete plaintext; 5-try throttle;
  `.enc.bak` fallback). Removing the lock writes plaintext directly while the
  lock file still exists (never re-encrypt there).
- **Migration**: a one-time step folds local/dev journal entries into the active
  store with per-field merge when the active store lacks them.
- **Export**: TXT and a hand-rolled multi-page PDF (Latin-1 with a transliteration
  table; page break at 46 lines).
- **Rich text**: fmt offsets are character-based, but embedded images occupy widget
  indices yet zero text characters — reload walks `txt.dump(...)` counting text items.

## 7. Menus & tray

- Kitten right-click menu indices **count separators** — `entryconfig(4)` = Pet name,
  `entryconfig(9)` = Mute, index 8 = Don't sleep (asserted by the test suites).
- Tray labels are **callables** reading `pet.tray_state` so "Pet <name> <3" and
  Mute/Unmute stay live.

## 8. Build & release

1. `build_installer.bat` → PyInstaller (`--windowed --onedir --name Kitty`, sprites
   and `meow.wav` via `--add-data`) → `dist\Kitty\Kitty.exe`.
2. `iscc installer\kitty.iss` → `KittySetup.exe` (tracked in git).
3. Commit + push — the installer is served from the repo's raw GitHub URL.
4. Reinstall = update. After changing assets, keep the PyInstaller flags, the `.bat`
   and `Kitty.spec` in sync (three places).

## 9. Privacy

No telemetry, no network. It reads only taskbar geometry, the foreground window
title (to detect code/design tools), and keyboard idle time — all local.