#python poster.py --inputs frames/*.png --out poster.png
#python poster.py --inputs frames/*.png --out poster.png --captions "1:Идея" "2:Обдумать" "3:План" "4:Spec. Driven Dev." "5:Vision.md" "6:Дока" "7:изучаю" "9:Результат :)" "12:Success!" 

# (Python) poster_maker_4x3_strict.py
# Usage:
#   python poster_maker_4x3_strict.py --inputs frames/*.png --out poster.png
#   python poster_maker_4x3_strict.py --inputs frames/*.jpg frames/*.png --out poster.png --gutter 40 --margin 60
#   python poster_maker_4x3_strict.py --inputs frames/*.png --out poster.png --captions "11:TESTING.." "12:ЗАРАБОТАЛО!"

import argparse, glob, os, re, sys
from PIL import Image, ImageDraw, ImageFont

def parse_whx(s: str):
    m = re.match(r'^(\d+)x(\d+)$', s.strip().lower())
    if not m: raise argparse.ArgumentTypeError("Expected WxH, e.g. 1200x900")
    return int(m.group(1)), int(m.group(2))

def load_font(size: int):
    for name in ["arial.ttf", "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try: return ImageFont.truetype(name, size)
        except Exception: pass
    return ImageFont.load_default()

def fit_into_box(im: Image.Image, box_w: int, box_h: int):
    w, h = im.size
    scale = min(box_w / w, box_h / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    im2 = im.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (box_w, box_h), (245, 247, 250))
    ox = (box_w - new_w) // 2
    oy = (box_h - new_h) // 2
    canvas.paste(im2, (ox, oy))
    return canvas

def parse_caption_args(items):
    mapping = {}
    for it in items or []:
        if ':' not in it:
            raise argparse.ArgumentTypeError('Caption must be like "11:TEXT"')
        idx_str, text = it.split(':', 1)
        idx = int(idx_str)
        mapping[idx] = text
    return mapping

def draw_caption(img: Image.Image, text: str, top=True, pad=16, font_size=56, color=(20,20,20)):
    draw = ImageDraw.Draw(img); font = load_font(font_size)
    x0, y0, x1, y1 = draw.textbbox((0,0), text, font=font)
    tw, th = x1 - x0, y1 - y0
    W, H = img.size
    x = (W - tw) // 2
    y = pad if top else H - th - pad
    shadow = (0,0,0)
    for dx, dy in [(1,1),(2,2),(0,2),(2,0)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=color)

def extract_frame_index(path: str) -> int:
    """
    Берём ПОСЛЕДНЕЕ число в имени файла как индекс кадра.
    examples:
      char1.png -> 1
      frame_07-final.jpg -> 7
      story-10.png -> 10
    """
    name = os.path.basename(path)
    nums = re.findall(r'(\d+)', name)
    if not nums:
        raise ValueError(f'No digits found in filename: {name}')
    return int(nums[-1])

def main():
    ap = argparse.ArgumentParser(description="Lay out EXACTLY 12 images into a 4x3 poster (strict frame mapping).")
    ap.add_argument("--inputs", nargs="+", required=True, help="Glob(s) for input images")
    ap.add_argument("--out", required=True, help="Output poster file, e.g., poster.png")
    ap.add_argument("--cell", type=parse_whx, default="1200x900", help="Cell size WxH (default 1200x900)")
    ap.add_argument("--gutter", type=int, default=40, help="Gap between cells in px (default 40)")
    ap.add_argument("--margin", type=int, default=60, help="Outer margin in px (default 60)")
    ap.add_argument("--bg", default="#ffffff", help="Background color (default #ffffff)")
    ap.add_argument("--captions", nargs="*", help='Optional captions like 11:TESTING.. 12:ЗАРАБОТАЛО!')
    ap.add_argument("--caption-top", action="store_true", help="Place captions at top (default).")
    ap.add_argument("--caption-bottom", action="store_true", help="Place captions at bottom.")
    ap.add_argument("--caption-size", type=int, default=56, help="Caption font size (default 56)")
    ap.add_argument("--no-pad-cell", action="store_true", help="Crop to fill cell (no letterboxing).")
    args = ap.parse_args()

    cols, rows = 4, 3  # жёстко: 4×3 = 12
    need = cols * rows  # 12

    # Собираем все файлы из глобав
    files = []
    for patt in args.inputs:
        files.extend(glob.glob(patt))
    if len(files) < need:
        print(f"Found {len(files)} images, need {need}.", file=sys.stderr)
        sys.exit(1)

    # Карта индекс->путь: берём последние цифры в имени
    by_idx = {}
    for f in files:
        try:
            idx = extract_frame_index(f)
            if 1 <= idx <= need and idx not in by_idx:
                by_idx[idx] = f
        except Exception:
            # пропускаем файлы без номера
            continue

    # Проверяем, что есть все 1..12
    missing = [i for i in range(1, need+1) if i not in by_idx]
    if missing:
        print("Missing frames (by number in filenames):", missing, file=sys.stderr)
        print("Tip: make sure files are named like char1.png ... char12.png (any prefix/suffix OK).", file=sys.stderr)
        sys.exit(1)

    # Формируем массив файлов строго по порядку 1..12
    ordered_files = [by_idx[i] for i in range(1, need+1)]

    cell_w, cell_h = args.cell
    gutter = args.gutter
    margin = args.margin

    poster_w = margin*2 + cols*cell_w + (cols-1)*gutter
    poster_h = margin*2 + rows*cell_h + (rows-1)*gutter
    poster = Image.new("RGB", (poster_w, poster_h), args.bg)

    # Загружаем кадры и приводим к cell
    frames = []
    for f in ordered_files:
        im = Image.open(f).convert("RGB")
        if args.no_pad_cell:
            w, h = im.size
            scale = max(cell_w / w, cell_h / h)
            new_w, new_h = int(w*scale), int(h*scale)
            im2 = im.resize((new_w, new_h), Image.LANCZOS)
            x0 = max(0, (new_w - cell_w)//2)
            y0 = max(0, (new_h - cell_h)//2)
            im2 = im2.crop((x0, y0, x0+cell_w, y0+cell_h))
        else:
            im2 = fit_into_box(im, cell_w, cell_h)
        frames.append(im2)

    captions = parse_caption_args(args.captions)
    caption_top = True if args.caption_top or not args.caption_bottom else False

    # Укладка 4×3 слева-направо, сверху-вниз
    idx = 0
    for r in range(rows):
        for c in range(cols):
            x = margin + c*(cell_w + gutter)
            y = margin + r*(cell_h + gutter)
            img = frames[idx]
            frame_no = idx + 1  # 1..12
            if frame_no in captions:
                tmp = img.copy()
                draw_caption(tmp, captions[frame_no], top=caption_top, pad=16, font_size=args.caption_size)
                img = tmp
            poster.paste(img, (x, y))
            idx += 1

    poster.save(args.out)
    print(f"Saved: {args.out}  ({poster_w}x{poster_h}px)  | frames: 1..12 mapped by filename digits")

if __name__ == "__main__":
    main()
