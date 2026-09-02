# Taskbar Kitten — Madhu — Full Feature Spec

**Stack:** `Python 3.12 + Tkinter 8.6 + Pillow 12.3 + psutil 7.2 + pystray` · `56x56` pixel-art · `96x96` duck · `D:\KITTY\src\pet_window.py:12` · `animator.py:66` · `taskbar.py:42`

## 1. Core Life
- **Chill loop** `28–42s` random (`avg 35s`, `12–18s` in Don't Sleep) `pet_window.py:244` → weighted `_cat_idle_choice` `pet_window.py:281`:
  - `15%` stretch/yawn `[2,3,3,2] 280ms` → groom → sleep/play
  - `13%` loaf `[4,7,4] 1400ms` → watch birds
  - `16%` groom `[pet 2,2,0,0] 420ms` + `lick lick ✨`
  - `14%` knead `[0,1,0,1] 300ms` + `knead knead ♡`
  - `14%` play pounce `[3,2,1,0] 110ms`
  - `28%` walk (`45%` in Don't Sleep) → `walk_to_spot`/`trigger_walk` roaming
- **Breathing:** `sleeping [0,1] 2200ms` held `78%` on `0` (`1900–3200ms`) + `900–1500ms` watch, randomized, not hyper.
- **Persistence:** `assets/kitten_memory.json` `memory.py:5` birth/petCount/fav spots/pos_x, `assets/kitten_pos.txt` `56x56` pos.

## 2. Taskbar Anchoring
- `Shell_TrayWnd` rect via `ctypes` `taskbar.py:9` `GetWindowRect`, `get_taskbar_edge()` top/bottom/left/right, `calc_position(pet_w,pet_h,placement)` `taskbar.py:42` `above` `t-56-2` vs `overlay` `sh-56-2`, fullscreen tuck `+6px` `pet_window.py:155`, multi-monitor via `MonitorFromWindow`, DPI via `GetDpiForWindow`, poll `5000ms` no flicker.

## 3. Sleep / Wake
- `sleeping 0` deep, `waking 2,3 180ms` yawn tail-up, `watching 6,4,5 1100ms`, `blink 7,4 900ms`, loaf `4,7,4`. Night `22–6h` sleepier `pet_window.py:892`.

## 4. Walk — Full Taskbar Roam
- `56x56` `walk_0..3.png` `140ms` + flipped `walk_flipped` when `dir<0` `animator.py:59` `set_walk_direction` no idx reset.
- `trigger_walk`/`_walk_to_spot` `pet_window.py:331` picks `_choose_sleep_spot` `pet_window.py:253` `55%` random `40..sw-120` vs `45%` home `Counter(favorite_spots)`. `walk_to_spot` `4px/32ms` with `1–2px` weight bob, `trigger_walk` `4px/35ms` until `2 bounces` or `320–520 steps` (full bar edge-to-edge, not `80–140` wall). `walk_x` persists `kitten_pos.txt`. Drag `on_drag:445` uses `e.x_root` + favorite record.

## 5. Pet / Hearts
- Left-click / tray `Pet Madhu <3` → `pet [0,1,2,1,0] 220ms` `pet_window.py:408` `pet_0..2 56x56` hearts, `1.18x` bounce `160ms`, `purr`/`meow` `meow.wav` `pet_window.py:1120` via `winsound.PlaySound`, mute toggle. Auto back `sleeping` `2200ms`. `petCount` + `lastPet` → milestones.

## 6. Food — Always Hungry Easter Egg
- `FOOD_WORDS` 116 (`biryani/biriyani/briyani` + Western) `pet_window.py:643` + `FOOD_SINGLE` fuzzy `lev≤1` (`lev≤2` for `≥7` + prefix) `pet_window.py:663` catches `biriyani` typos.
- Any title `*food*` in foreground `GetForegroundWindow` `GetWindowTextW` triggers `pet_window.py:647` (no google gate). `food_check 1200ms` `22s` debounce + `last_word` guard, `900ms` bubble clamped `bw/bh` `max(8, sw-bw-8)` `pet_window.py:702,711`, walk to food `180ms`.

## 7. Dual Rubber-Duck (Code vs Architecture)
- `CODING_PROCS {code.exe,pycharm64,idea,devenv,sublime,atom,cursor,opencode.exe}` `ARCH {acad,revit,rhino,sketchup,archicad,lumion,twinmotion,vray,enscape}` `pet_window.py:379` `detect_duck_source()` foreground-only `GetWindowThreadProcessId` + title fallback `visual studio code/pycharm/autocad…`.
- `set_duck(enable,source)` `pet_window.py:514` `56→96` dock `sw-96-12, sh/2-48` with `blink` notice beat `280ms`, `duck_trigger_source` persisted. Render `lumion/twinmotion/vray` stays while `cpu>20` `psutil cpu_percent 0.1` `pet_window.py:418`, else tucks *immediate* `pet_window.py:549` (was `14s`).

## 8. Wish Me Luck — 150
- `LUCK_MESSAGES 150` `pet_window.py:508` rotating via `luck_message_index` `pet_window.py:975` `trigger_luck` notice beat + bubble `5000ms` + `1.22x` bounce + chirp, tray + menu `Wish me luck 🍀` `pet_window.py:502`.

## 9. Sound
- `_play_meow(kind)` `pet_window.py:1125` `winsound.PlaySound assets/meow.wav` `SND_ASYNC` for `meow/purr/chirp` (downloaded CC0 1.14s 98KB), fallback `Beep` tremolo `72→60Hz`. Mute `is_muted` `memory.py:20` toggle `Mute 🔇/Unmute 🔊` `pet_window.py:69` + tray `app.py:54`, persists.

## 10. Curious + Glance + Missing You + Welcome Back
- `curious_check 2200ms` `pet_window.py:506` `GetLastInputInfo` idle `>14s` then `idle<1.2s` + `35%` → `watching`/`walk to center`.
- `glance_check 1700ms` `pet_window.py:1007` cursor `<320px` `45%` → `watching` flip by `dx`.
- `long_absence` `2h` via `hours_since` `memory.py:45` `pet_window.py:1013` blink `missed you…` + `_welcome_back` `pet_window.py:1035` hop `1.25x` double bounce + `pet`.
- `waiting_check 45s` idle `>180s` `pet_window.py:933` drifts to favorite `Counter` or `x=14` `waiting for you…`.

## 11. Gift Touches
- **Name:** `ask_name_if_needed` `pet_window.py:818` parchment `360x410` rounded `Canvas` shadow `#E6D5B8` white `#FFDAB9` `frame_4.png 72x72`, `Meet your kitten ✨` `Segoe UI 13 bold #8B4513`, entry `#FFDAB9`, pink `🐾 That's my name ♡` `#FF8FA3`, fade-in, drag, `menu.entryconfig 4` + `root.title`. `name: null` reset so she gets prompt.
- **11:11** `wish_11_check 20s` `pet_window.py:1135` hour `11/23` minute `11` → `11:11 AM/PM — make a wish ✨` 7s + chirp once per slot.
- **Seasonal:** `seasonal_check 1h` `pet_window.py:929` Dec 20–26 🎄, Feb 13–15 💘, Oct 30–31 🎃 `15%`.
- **Milestones:** `1/10/100/500` pets + `week 7` + `month 30` heart-burst `1.28x` + meow `pet_window.py:859`.

## 12. Don't Sleep 30m
- Menu `Don't sleep 30m ☕` `pet_window.py:508` `toggle_dont_sleep` `pet_window.py:1141` sets `_dont_sleep_until +30m`, label `✓ (Xm)` tick `60s` (`_dont_sleep_tick_after`), auto `30*60*1000` expire. `animate` redirects `sleeping→play/groom/watching/knead` `pet_window.py:182`, `bored_check` walk `45%` `12–18s`, `_maybe_sleep` picks lively.

## 13. Scrapbook — Our Story
- `show_scrapbook()` `pet_window.py:1072` `360x320` `FFF8DC` `Our story with Madhu 📖` days since `birth`, `petCount`, `longestApartHours`, fav `avg px`, `milestones`, quote.

## 14. Build / Installer
- `requirements.txt` Pillow psutil pystray + `build_installer.bat` `PyInstaller --windowed --onedir --name Kitty --add-data assets/sprites --add-data assets/meow.wav --icon frame_4.png src/app.py` → `dist\Kitty\Kitty.exe` `5.4MB` `installer/kitty.iss` Wizard modern, `AppName Madhu`, `wizard.bmp 164x314` + `wizard_small.bmp 55x55` from sprite. `Kitty.spec` excluded via `.gitignore`. Run via `run.bat` or `dist\Kitty\Kitty.exe`. GitHub `ramsathwik2/something-something-` `main` `7aa7b67`.

## 15. Privacy
- Only `GetForegroundWindow` title + `GetLastInputInfo` idle, no history scrape. Food titles stay local.

