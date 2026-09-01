from PIL import Image
import pathlib

src = pathlib.Path(r"D:\KITTY\assets\raw_sheet.png")
out_dir = pathlib.Path(r"D:\KITTY\assets\sprites")
out_dir.mkdir(parents=True, exist_ok=True)

im = Image.open(src).convert("RGBA")
w,h = im.size
print(f"Loaded {w}x{h}")

# Find columns with alpha >20
alpha = im.split()[3]
# Project: col_has_alpha
col_has = [False]*w
for y in range(h):
    for x in range(w):
        if im.getpixel((x,y))[3] > 20:
            col_has[x]=True

# Find contiguous segments where col_has is True
segments=[]
in_seg=False
start=0
for i, has in enumerate(col_has):
    if has and not in_seg:
        in_seg=True; start=i
    elif not has and in_seg:
        # require gap >= 15 to split
        # look ahead to see if gap is big enough - collect gap length
        gap_len=0
        for j in range(i, min(w, i+80)):
            if not col_has[j]:
                gap_len+=1
            else:
                break
        if gap_len >= 12:
            segments.append((start,i))
            in_seg=False
if in_seg:
    segments.append((start,w))

print(f"Found {len(segments)} segments: {segments}")

# Filter tiny noise segments
segments = [s for s in segments if s[1]-s[0] > 40]
print(f"Filtered segments: {segments}")

# Now for each segment find bbox vertically
TARGET=56
for idx,(x0,x1) in enumerate(segments[:8]):
    # add padding
    pad=8
    x0=max(0,x0-pad); x1=min(w,x1+pad)
    # vertical bounds for this segment
    # find y min/max where alpha in this x range
    ymin=h; ymax=0
    for y in range(h):
        for x in range(x0,x1):
            if im.getpixel((x,y))[3] > 20:
                ymin=min(ymin,y); ymax=max(ymax,y)
                break
    y0=max(0,ymin-8); y1=min(h,ymax+8+1)
    print(f"Frame {idx}: x {x0}-{x1} y {y0}-{y1} -> {x1-x0}x{y1-y0}")
    crop = im.crop((x0,y0,x1,y1))
    # center on TARGET x TARGET transparent canvas, preserve aspect
    cw,ch = crop.size
    scale = min((TARGET-8)/cw, (TARGET-8)/ch) if cw>0 and ch>0 else 1
    new_w, new_h = int(cw*scale), int(ch*scale)
    resized = crop.resize((new_w,new_h), Image.NEAREST)  # keep pixel art crisp
    canvas = Image.new("RGBA",(TARGET,TARGET),(0,0,0,0))
    # bottom-center anchor (like sitting on taskbar)
    ox = (TARGET - new_w)//2
    oy = TARGET - new_h - 2  # 2px bottom margin
    canvas.paste(resized,(ox,oy), resized)
    out_path = out_dir / f"frame_{idx}.png"
    canvas.save(out_path)
    print(f"  saved {out_path} {canvas.size}")

    # also save trimmed original for debug
    #crop.save(out_dir / f"crop_{idx}.png")

# Build combined sheet 448x56 (8*56)
frames = [Image.open(out_dir / f"frame_{i}.png") for i in range(min(8,len(segments)))]
if frames:
    sheet = Image.new("RGBA",(56*len(frames),56),(0,0,0,0))
    for i,f in enumerate(frames):
        sheet.paste(f,(i*56,0),f)
    sheet_path = out_dir / "sheet.png"
    sheet.save(sheet_path)
    print(f"Combined sheet {sheet.size} -> {sheet_path}")
print("Done")
