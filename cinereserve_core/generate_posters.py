import os
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
POSTERS_DIR = BASE_DIR / 'media' / 'posters'
BANNERS_DIR = POSTERS_DIR / 'banners'
POSTERS_DIR.mkdir(parents=True, exist_ok=True)
BANNERS_DIR.mkdir(parents=True, exist_ok=True)

# Helper for font loading
def get_font(size=24, bold=True):
    font_paths = [
        'C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibrib.ttf' if bold else 'C:/Windows/Fonts/calibri.ttf',
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_vertical_gradient(draw, width, height, colors):
    """Interpolates between multiple color stops along the Y axis."""
    num_stops = len(colors)
    segment_h = height / (num_stops - 1)
    for y in range(height):
        seg_idx = min(int(y / segment_h), num_stops - 2)
        local_ratio = (y - seg_idx * segment_h) / segment_h
        c1 = colors[seg_idx]
        c2 = colors[seg_idx + 1]
        r = int(c1[0] + (c2[0] - c1[0]) * local_ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * local_ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * local_ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def create_poster(filename, title, subtitle, genres, cert, rating, theme):
    w, h = 600, 900
    img = Image.new('RGB', (w, h), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # 1. Base Gradient
    draw_vertical_gradient(draw, w, h, theme['gradient'])

    # 2. Thematic Artwork / Shapes
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    art_style = theme.get('art_style', 'abstract')
    if art_style == 'quantum':
        # Concentric glowing rings and particle arcs
        center = (w // 2, 340)
        for r in range(40, 220, 25):
            alpha = max(10, 160 - r // 2)
            ov_draw.ellipse(
                [center[0] - r, center[1] - r, center[0] + r, center[1] + r],
                outline=(*theme['accent_color'], alpha),
                width=3
            )
        for i in range(12):
            angle = i * (math.pi / 6)
            x2 = center[0] + int(240 * math.cos(angle))
            y2 = center[1] + int(240 * math.sin(angle))
            ov_draw.line([center, (x2, y2)], fill=(*theme['accent_color'], 40), width=1)

    elif art_style == 'cyberpunk':
        # Cyber grid horizon and neon beams
        horizon_y = 420
        ov_draw.line([(0, horizon_y), (w, horizon_y)], fill=(*theme['accent_color'], 180), width=3)
        for x in range(0, w + 1, 40):
            ov_draw.line([(x, horizon_y), (w // 2 + (x - w // 2) * 3, h)], fill=(*theme['accent_color'], 50), width=1)
        for y in range(horizon_y + 15, h, 25):
            ov_draw.line([(0, y), (w, y)], fill=(*theme['accent_color'], 35), width=1)
        # Giant neon sun behind horizon
        ov_draw.ellipse([w // 2 - 130, horizon_y - 130, w // 2 + 130, horizon_y + 130], outline=(236, 72, 153, 140), width=4)

    elif art_style == 'space':
        # Starfield & giant ringed planet
        random.seed(42)
        for _ in range(140):
            sx = random.randint(20, w - 20)
            sy = random.randint(50, 520)
            s_rad = random.choice([1, 2, 3])
            s_col = random.choice([(255, 255, 255, 200), (*theme['accent_color'], 180), (200, 220, 255, 140)])
            ov_draw.ellipse([sx, sy, sx + s_rad, sy + s_rad], fill=s_col)
        # Planet
        ov_draw.ellipse([w // 2 - 120, 200, w // 2 + 120, 440], fill=(*theme['accent_color'], 190))
        # Planetary ring
        ov_draw.arc([w // 2 - 190, 280, w // 2 + 190, 360], start=0, end=360, fill=(255, 255, 255, 160), width=4)

    elif art_style == 'romance':
        # Soft moon and ambient glowing bokeh circles
        ov_draw.ellipse([w // 2 - 100, 160, w // 2 + 100, 360], fill=(254, 240, 138, 160))
        random.seed(77)
        for _ in range(25):
            bx = random.randint(40, w - 40)
            by = random.randint(100, 500)
            br = random.randint(15, 60)
            ov_draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(251, 113, 133, 40))

    elif art_style == 'horror':
        # Eerie mist gradient triangles and dark moon
        ov_draw.ellipse([w // 2 - 70, 150, w // 2 + 70, 290], fill=(226, 232, 240, 120))
        # Silhouette pine trees
        for tx in range(0, w + 60, 50):
            th = random.randint(140, 220)
            ov_draw.polygon([(tx - 35, 480), (tx, 480 - th), (tx + 35, 480)], fill=(2, 6, 23, 230))

    elif art_style == 'comedy':
        # Tropical sun rays and fun geometric waves
        cx, cy = w // 2, 260
        for i in range(16):
            ang = i * (math.pi / 8)
            rx = cx + int(300 * math.cos(ang))
            ry = cy + int(300 * math.sin(ang))
            ov_draw.polygon([cx, cy, rx - 20, ry, rx + 20, ry], fill=(251, 191, 36, 45))
        ov_draw.ellipse([cx - 85, cy - 85, cx + 85, cy + 85], fill=(245, 158, 11, 210))

    elif art_style == 'action':
        # Venice canals & crosshair motif
        cx, cy = w // 2, 290
        ov_draw.ellipse([cx - 110, cy - 110, cx + 110, cy + 110], outline=(*theme['accent_color'], 200), width=3)
        ov_draw.line([(cx - 150, cy), (cx + 150, cy)], fill=(*theme['accent_color'], 140), width=2)
        ov_draw.line([(cx, cy - 150), (cx, cy + 150)], fill=(*theme['accent_color'], 140), width=2)

    img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))
    draw = ImageDraw.Draw(img)

    # 3. Bottom cinematic vignette for text readability
    vignette = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(480, h):
        ratio = (y - 480) / (h - 480)
        alpha = int(245 * (ratio ** 1.3))
        v_draw.line([(0, y), (w, y)], fill=(5, 8, 16, alpha))
    img.paste(Image.alpha_composite(img.convert('RGBA'), vignette).convert('RGB'))
    draw = ImageDraw.Draw(img)

    # 4. Top Branding Header
    font_brand = get_font(16, bold=True)
    draw.text((w // 2, 35), "CINERESERVE EXCLUSIVE", fill=(241, 245, 249), anchor="mm", font=font_brand)
    draw.line([(w // 2 - 80, 50), (w // 2 + 80, 50)], fill=theme['accent_color'], width=2)

    # 5. Badges (Certification & Format)
    font_badge = get_font(13, bold=True)
    # Cert badge top-left
    draw.rounded_rectangle([35, 75, 95, 102], radius=6, fill=(15, 23, 42), outline=(100, 116, 139), width=1)
    draw.text((65, 88), cert, fill=(241, 245, 249), anchor="mm", font=font_badge)

    # Rating badge top-right
    draw.rounded_rectangle([w - 125, 75, w - 35, 102], radius=6, fill=(234, 179, 8), outline=(202, 138, 4), width=1)
    draw.text((w - 80, 88), f"★ {rating}", fill=(15, 23, 42), anchor="mm", font=font_badge)

    # 6. Movie Title
    font_title = get_font(34, bold=True)
    font_sub = get_font(16, bold=False)
    font_genres = get_font(14, bold=True)

    # Wrap title if long
    words = title.split(' ')
    lines = []
    curr = []
    for wd in words:
        curr.append(wd)
        test_line = ' '.join(curr)
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if bbox[2] - bbox[0] > w - 80:
            if len(curr) > 1:
                curr.pop()
                lines.append(' '.join(curr))
                curr = [wd]
            else:
                lines.append(test_line)
                curr = []
    if curr:
        lines.append(' '.join(curr))

    title_y = 660 - (len(lines) - 1) * 40
    for idx, line in enumerate(lines):
        # Shadow
        draw.text((w // 2 + 2, title_y + idx * 44 + 2), line, fill=(0, 0, 0), anchor="mm", font=font_title)
        # Main text
        draw.text((w // 2, title_y + idx * 44), line, fill=(255, 255, 255), anchor="mm", font=font_title)

    # Subtitle / Director
    draw.text((w // 2, title_y + len(lines) * 44 + 6), subtitle, fill=(148, 163, 184), anchor="mm", font=font_sub)

    # Genres pill row
    genre_text = " • ".join(genres).upper()
    draw.text((w // 2, 800), genre_text, fill=theme['accent_color'], anchor="mm", font=font_genres)

    # Bottom Cinema Tagline
    font_footer = get_font(12, bold=False)
    draw.text((w // 2, 850), "EXPERIENCE IN IMAX & DOLBY ATMOS", fill=(100, 116, 139), anchor="mm", font=font_footer)

    img.save(POSTERS_DIR / filename, format='JPEG', quality=92)
    print(f"[OK] Generated poster: {filename}")

def main():
    posters_data = [
        {
            "filename": "avengers-quantum-odyssey.jpg",
            "title": "Avengers: Quantum Odyssey",
            "subtitle": "Directed by The Russo Brothers",
            "genres": ["Action", "Sci-Fi", "Adventure"],
            "cert": "UA",
            "rating": "8.9",
            "theme": {
                "gradient": [(11, 15, 25), (30, 27, 75), (127, 29, 29), (229, 9, 20)],
                "accent_color": (229, 9, 20),
                "art_style": "quantum"
            }
        },
        {
            "filename": "cyberpunk-neon-horizon.jpg",
            "title": "Cyberpunk: Neon Horizon",
            "subtitle": "Directed by Denis Villeneuve",
            "genres": ["Sci-Fi", "Action", "Thriller"],
            "cert": "A",
            "rating": "8.5",
            "theme": {
                "gradient": [(5, 5, 16), (23, 15, 50), (14, 116, 144), (6, 182, 212)],
                "accent_color": (6, 182, 212),
                "art_style": "cyberpunk"
            }
        },
        {
            "filename": "chronicles-of-starlight.jpg",
            "title": "Chronicles of Starlight",
            "subtitle": "Directed by Pete Docter",
            "genres": ["Animation", "Adventure", "Sci-Fi"],
            "cert": "U",
            "rating": "8.8",
            "theme": {
                "gradient": [(3, 7, 18), (30, 27, 75), (49, 46, 129), (129, 140, 248)],
                "accent_color": (168, 85, 247),
                "art_style": "space"
            }
        },
        {
            "filename": "heartstrings-and-horizons.jpg",
            "title": "Heartstrings & Horizons",
            "subtitle": "Directed by Damien Chazelle",
            "genres": ["Romance", "Drama"],
            "cert": "UA",
            "rating": "8.3",
            "theme": {
                "gradient": [(15, 10, 30), (76, 29, 149), (190, 24, 93), (251, 113, 133)],
                "accent_color": (244, 114, 182),
                "art_style": "romance"
            }
        },
        {
            "filename": "shadows-in-the-mist.jpg",
            "title": "Shadows in the Mist",
            "subtitle": "Directed by James Wan",
            "genres": ["Horror", "Thriller"],
            "cert": "A",
            "rating": "7.4",
            "theme": {
                "gradient": [(2, 6, 23), (15, 23, 42), (51, 65, 85), (100, 116, 139)],
                "accent_color": (239, 68, 68),
                "art_style": "horror"
            }
        },
        {
            "filename": "laughter-therapy-vacation-chaos.jpg",
            "title": "Laughter Therapy: Vacation Chaos",
            "subtitle": "Directed by Taika Waititi",
            "genres": ["Comedy", "Romance"],
            "cert": "U",
            "rating": "7.6",
            "theme": {
                "gradient": [(6, 78, 59), (15, 118, 110), (245, 158, 11), (234, 88, 12)],
                "accent_color": (251, 191, 36),
                "art_style": "comedy"
            }
        },
        {
            "filename": "the-martian-genesis.jpg",
            "title": "The Martian Genesis",
            "subtitle": "Directed by Christopher Nolan",
            "genres": ["Sci-Fi", "Drama"],
            "cert": "UA",
            "rating": "9.2",
            "theme": {
                "gradient": [(24, 9, 7), (69, 10, 10), (153, 27, 27), (249, 115, 22)],
                "accent_color": (249, 115, 22),
                "art_style": "space"
            }
        },
        {
            "filename": "spies-in-venice.jpg",
            "title": "Spies in Venice",
            "subtitle": "Directed by Matthew Vaughn",
            "genres": ["Action", "Comedy", "Thriller"],
            "cert": "UA",
            "rating": "8.0",
            "theme": {
                "gradient": [(9, 30, 43), (15, 61, 76), (30, 41, 59), (217, 119, 6)],
                "accent_color": (234, 179, 8),
                "art_style": "action"
            }
        },
    ]

    for p in posters_data:
        create_poster(
            filename=p["filename"],
            title=p["title"],
            subtitle=p["subtitle"],
            genres=p["genres"],
            cert=p["cert"],
            rating=p["rating"],
            theme=p["theme"]
        )

if __name__ == '__main__':
    main()
