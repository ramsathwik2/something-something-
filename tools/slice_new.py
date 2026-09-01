from PIL import Image
import pathlib

def slice_sheet(src_path, prefix, target=56):
    src = pathlib.Path(src_path)
    out_dir = pathlib.Path(r"D:\KITTY\assets\sprites")
    im = Image.open(src).convert("RGBA")
    w,h = im.size
    print(f"Slicing {src.name} {w}x{h} -> {prefix}_*.png target {target}")
    col_has=[False]*w
    for y in range(h):
        for x in range(w):
            if im.getpixel((x,y))[3] > 20:
                col_has[x]=True
    segments=[]
    in_seg=False; start=0
    for i,has in enumerate(col_has):
        if has and not in_seg:
            in_seg=True; start=i
        elif not has and in_seg:
            gap=0
            for j in range(i, min(w,i+100)):
                if not col_has[j]:
                    gap+=1
                else: break
            if gap>=12:
                segments.append((start,i)); in_seg=False
    if in_seg:
        segments.append((start,w))
    segments=[s for s in segments if s[1]-s[0]>40]
    print(f"  segments {segments} count {len(segments)}")
    for idx,(x0,x1) in enumerate(segments):
        pad=8; x0=max(0,x0-pad); x1=min(w,x1+pad)
        ymin=h; ymax=0
        for y in range(h):
            for x in range(x0,x1):
                if im.getpixel((x,y))[3]>20:
                    ymin=min(ymin,y); ymax=max(ymax,y); break
        y0=max(0,ymin-8); y1=min(h, ymax+9)
        crop=im.crop((x0,y0,x1,y1))
        cw,ch=crop.size
        scale=min((target-6)/cw, (target-6)/ch) if cw and ch else 1
        nw,nh=int(cw*scale), int(ch*scale)
        resized=crop.resize((nw,nh), Image.NEAREST)
        canvas=Image.new("RGBA",(target,target),(0,0,0,0))
        ox=(target-nw)//2; oy=target-nh-2
        canvas.paste(resized,(ox,oy), resized)
        out=out_dir / f"{prefix}_{idx}.png"
        canvas.save(out)
        print(f"   saved {out.name} {canvas.size} from crop {cw}x{ch} -> {nw}x{nh}")

slice_sheet(r"D:\KITTY\assets\raw_walk.png", "walk", 56)
slice_sheet(r"D:\KITTY\assets\raw_pet.png", "pet", 56)
# also show existing base
