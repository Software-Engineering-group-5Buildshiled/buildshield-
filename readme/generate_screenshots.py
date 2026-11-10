from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

FONT = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def text_size(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)


def add_text(draw, x, y, text, fill=(0, 0, 0), size=24, bold=False):
    font = ImageFont.truetype(FONT_BOLD if bold else FONT, size)
    draw.text((x, y), text, font=font, fill=fill)


def draw_login_screen():
    img = Image.new("RGB", (1600, 900), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 780, 900), fill=(9, 22, 38))
    draw.rounded_rectangle((90, 80, 350, 168), radius=20, fill=(233, 180, 50))
    draw.text((112, 90), "F", font=ImageFont.truetype(FONT_BOLD, 72), fill=(18, 32, 46))
    add_text(draw, 375, 100, "BuildShield", fill=(255, 255, 255), size=34, bold=True)
    add_text(draw, 116, 172, "SECURE | BUILD | GROW", fill=(175, 210, 240), size=18)

    draw.rounded_rectangle((90, 230, 660, 650), radius=16, fill=(12, 28, 46))
    draw.rounded_rectangle((110, 250, 220, 280), radius=8, fill=(43, 59, 89))
    add_text(draw, 248, 250, "py views.py", fill=(167, 209, 255), size=16)
    add_text(draw, 110, 315, "1  class Finding(models.Model):", fill=(86, 174, 255), size=18)
    add_text(draw, 110, 350, '2      """A single security risk found in the SDLC."""', fill=(255, 255, 255), size=18)
    add_text(draw, 110, 420, "4      def update_status(self, new_status):", fill=(163, 199, 255), size=18)
    add_text(draw, 110, 455, "5          if new_status == 'open':", fill=(163, 199, 255), size=18)

    draw.rounded_rectangle((100, 680, 178, 708), radius=10, fill=(36, 51, 72))
    add_text(draw, 110, 680, "@login_required", fill=(167, 209, 255), size=14)
    draw.rounded_rectangle((190, 680, 290, 708), radius=10, fill=(36, 51, 72))
    add_text(draw, 200, 680, "CSRF protected", fill=(167, 209, 255), size=14)
    draw.rounded_rectangle((300, 680, 390, 708), radius=10, fill=(36, 51, 72))
    add_text(draw, 310, 680, "Django ORM", fill=(167, 209, 255), size=14)

    draw.rounded_rectangle((840, 110, 1460, 760), radius=22, fill=(255, 255, 255))
    add_text(draw, 900, 175, "Welcome to", fill=(44, 51, 64), size=30)
    add_text(draw, 900, 212, "BuildShield", fill=(29, 31, 42), size=44, bold=True)
    add_text(draw, 900, 272, "Login in to continue to your account.", fill=(74, 80, 88), size=25)

    add_text(draw, 900, 350, "Username", fill=(44, 51, 64), size=22)
    draw.rounded_rectangle((900, 385, 1395, 470), radius=14, fill=(246, 247, 250))
    add_text(draw, 970, 405, "Enter your username", fill=(150, 156, 166), size=25)

    add_text(draw, 900, 505, "Password", fill=(44, 51, 64), size=22)
    draw.rounded_rectangle((900, 540, 1395, 625), radius=14, fill=(246, 247, 250))
    add_text(draw, 970, 560, "Enter your password", fill=(150, 156, 166), size=25)

    draw.rounded_rectangle((900, 660, 1395, 740), radius=24, fill=(22, 31, 42))
    add_text(draw, 1150, 670, "Log in", fill=(255, 255, 255), size=28, bold=True)
    add_text(draw, 1000, 785, "Forgot your password or need an account?", fill=(64, 68, 77), size=18)
    add_text(draw, 1085, 815, "Contact your administrator.", fill=(38, 45, 55), size=18)

    img.save(SCREENSHOT_DIR / "login-screen.png")


def draw_dashboard_screen(role: str):
    img = Image.new("RGB", (1600, 900), (244, 244, 244))
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 300, 900), fill=(10, 25, 42))
    draw.rounded_rectangle((18, 18, 272, 78), radius=14, fill=(233, 180, 50))
    draw.text((78, 20), "F", font=ImageFont.truetype(FONT_BOLD, 54), fill=(18, 32, 46))
    add_text(draw, 118, 24, "BuildShield", fill=(255, 255, 255), size=26, bold=True)
    add_text(draw, 40, 94, "SDLC INFRASTRUCTURE", fill=(196, 205, 218), size=12)
    add_text(draw, 40, 110, "SECURITY", fill=(196, 205, 218), size=12)

    nav_items = [
        ("Dashboard", True),
        ("Findings", False),
        ("Report a finding", False),
    ]
    y = 190
    for label, active in nav_items:
        if active:
            draw.rounded_rectangle((18, y, 280, y + 60), radius=12, fill=(255, 182, 35))
            draw.text((50, y + 18), "▣", font=ImageFont.truetype(FONT, 22), fill=(20, 24, 28))
            add_text(draw, 90, y + 16, label, fill=(20, 24, 28), size=20)
        else:
            draw.text((52, y + 18), "◉", font=ImageFont.truetype(FONT, 20), fill=(210, 220, 242))
            add_text(draw, 90, y + 16, label, fill=(220, 226, 235), size=20)
        y += 70

    draw.rounded_rectangle((18, 760, 280, 830), radius=12, fill=(31, 42, 53))
    draw.text((52, 764), "◌", font=ImageFont.truetype(FONT, 22), fill=(230, 236, 246))
    add_text(draw, 90, 768, role if role == "admin1" else "dev1", fill=(245, 246, 247), size=20)
    role_label = "Administrator" if role == "admin1" else "Developer"
    add_text(draw, 86, 798, role_label, fill=(166, 181, 197), size=12)

    draw.rounded_rectangle((18, 840, 280, 880), radius=12, fill=(20, 33, 46))
    add_text(draw, 90, 850, "Log out", fill=(255, 255, 255), size=18)

    draw.rounded_rectangle((330, 40, 1480, 845), radius=18, fill=(242, 242, 242))
    draw.rounded_rectangle((380, 55, 1120, 105), radius=16, fill=(248, 250, 252))
    add_text(draw, 430, 68, "Search findings, projects, pillars...", fill=(112, 127, 144), size=20)

    draw.rounded_rectangle((1220, 55, 1308, 110), radius=18, fill=(28, 36, 49))
    add_text(draw, 1250, 68, "A", fill=(255, 255, 255), size=22)
    add_text(draw, 1318, 66, role if role == "admin1" else "dev1", fill=(38, 45, 55), size=20)
    role_text = "Administrator" if role == "admin1" else "Developer"
    add_text(draw, 1318, 90, role_text, fill=(89, 95, 102), size=12)

    add_text(draw, 340, 160, "All projects", fill=(37, 45, 55), size=42, bold=True)
    add_text(draw, 340, 220, "Security findings across the five SITF pillars of your code factory.", fill=(92, 99, 102), size=22)

    draw.rounded_rectangle((1110, 175, 1430, 228), radius=12, fill=(245, 247, 250))
    add_text(draw, 1160, 186, "22 Sep - 10 Nov 2026", fill=(43, 49, 55), size=18)

    cards = [
        ("Open findings", "24", (202, 229, 250), (120, 160, 220), (350, 280, 670, 470)),
        ("Critical and open", "1", (255, 202, 202), (220, 80, 90), (690, 280, 1010, 470)),
        ("Resolved", "18", (216, 244, 220), (65, 170, 95), (1030, 280, 1360, 470)),
        ("Reported in total", "42", (236, 220, 255), (130, 90, 180), (350, 500, 670, 690)),
    ]

    for title, value, bg, accent, bounds in cards:
        x1, y1, x2, y2 = bounds
        draw.rounded_rectangle((x1, y1, x2, y2), radius=20, fill=(255, 255, 255), outline=(204, 208, 214), width=1)
        add_text(draw, x1 + 25, y1 + 24, title, fill=(42, 49, 56), size=18)
        add_text(draw, x1 + 25, y1 + 70, value, fill=(30, 41, 59), size=42, bold=True)
        draw.line((x1 + 25, y1 + 150, x2 - 25, y1 + 150), fill=(220, 224, 229), width=2)
        pts = []
        for i in range(0, 60):
            x = x1 + 25 + i * 2
            y = y1 + 123 + (10 if i % 8 < 4 else 5) * (1 if "Open" in title or "Critical" in title else -1)
            pts.append((x, y))
        draw.line(pts, fill=accent, width=3)
        add_text(draw, x1 + 25, y1 + 150, "0% than last period", fill=(96, 103, 110), size=15)

    draw.rounded_rectangle((350, 700, 780, 830), radius=18, fill=(255, 255, 255), outline=(205, 209, 213), width=1)
    add_text(draw, 360, 715, "Where the factory is exposed", fill=(42, 49, 56), size=18, bold=True)

    draw.rounded_rectangle((830, 700, 1420, 830), radius=18, fill=(255, 255, 255), outline=(205, 209, 213), width=1)
    add_text(draw, 840, 715, "Findings by severity", fill=(42, 49, 56), size=18, bold=True)

    if role == "admin1":
        img.save(SCREENSHOT_DIR / "admin-dashboard.png")
    else:
        img.save(SCREENSHOT_DIR / "developer-dashboard.png")


draw_login_screen()
draw_dashboard_screen("admin1")
draw_dashboard_screen("dev1")
print("Generated screenshots:")
for item in sorted(SCREENSHOT_DIR.iterdir()):
    print(f"- {item.name}")
