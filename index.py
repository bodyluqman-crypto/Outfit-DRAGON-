from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import os
import random
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
main_key = "DRAGON-TEAM"
executor = ThreadPoolExecutor(max_workers=10)

# الرابط السري لصور Free Fire (بيشتغل)
INFO_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG"

def fetch_player_info(uid):
    url = f'https://otman-info.vercel.app/player-info?uid={uid}'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def fetch_image(image_url, size=None):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, timeout=10, headers=headers)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return img
    except:
        pass
    return None

def make_circle_with_border(image, size, border_color):
    if image is None:
        return None
    img = image.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)
    circular = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    circular.paste(img, (0, 0), mask)
    border = Image.new('RGBA', (size + 16, size + 16), (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border)
    for i in range(8, 0, -1):
        alpha = 50 - i * 5
        draw_border.ellipse((8 - i, 8 - i, size + 8 + i, size + 8 + i),
                           outline=(border_color[0], border_color[1], border_color[2], alpha), width=2)
    draw_border.ellipse((8, 8, size + 8, size + 8), outline=border_color, width=4)
    draw_border.ellipse((12, 12, size + 4, size + 4), outline=(255, 255, 255, 150), width=1)
    border.paste(circular, (8, 8), circular)
    return border

def create_fancy_background():
    width, height = 1200, 1200
    img = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(40 + ratio * 60)
        g = int(10 + ratio * 80)
        b = int(70 + ratio * 150)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255), width=1)
    colors = [
        (255, 100, 100, 40), (100, 255, 100, 40), (100, 100, 255, 40),
        (255, 255, 100, 40), (255, 100, 255, 40), (100, 255, 255, 40)
    ]
    for i, color in enumerate(colors):
        r = 180 + i * 90
        draw.ellipse((width//2 - r, height//2 - r, width//2 + r, height//2 + r),
                    outline=color, width=3)
    for i in range(0, width, 60):
        draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 15), width=1)
        draw.line([(0, i), (width, i)], fill=(255, 255, 255, 15), width=1)
    for _ in range(150):
        x = random.randint(0, width)
        y = random.randint(0, height)
        intensity = random.randint(80, 255)
        draw.point((x, y), fill=(intensity, intensity, intensity, 255))
    return img

@app.route('/outfit-image', methods=['GET'])
def outfit_image():
    uid = request.args.get('uid')
    key = request.args.get('key')

    if not uid:
        return jsonify({'error': 'Missing uid'}), 400
    if key != main_key:
        return jsonify({'error': 'Invalid key'}), 403

    data = fetch_player_info(uid)
    if not data:
        return jsonify({'error': 'Failed to fetch'}), 500

    clothes_ids = data.get("profileInfo", {}).get("clothes", [])
    equipped_skills = data.get("profileInfo", {}).get("equipedSkills", [])
    pet_id = data.get("petInfo", {}).get("id")
    weapon_id = data.get("basicInfo", {}).get("weaponSkinShows", [None])[0]
    player_name = data.get("basicInfo", {}).get("nickname", "WARRIOR")

    required_codes = ["211", "214", "203", "204", "205", "208"]
    fallback_ids = ["211000000", "214000000", "203000077", "204000345", "205000070", "208000000"]
    used_ids = set()
    futures = []

    def fetch_outfit(idx, code):
        matched = None
        for oid in clothes_ids:
            if str(oid).startswith(code) and oid not in used_ids:
                matched = oid
                used_ids.add(oid)
                break
        if matched is None:
            matched = fallback_ids[idx]
        url = f'{INFO_URL}/{matched}.png'
        return fetch_image(url, size=(130, 130))

    for idx, code in enumerate(required_codes):
        futures.append(executor.submit(fetch_outfit, idx, code))

    background = create_fancy_background()
    W, H = 1200, 1200
    draw = ImageDraw.Draw(background)
    default_font = ImageFont.load_default()

    def draw_text(x, y, text, color):
        draw.text((x, y), text, fill=color, font=default_font)

    # شعار في الأعلى
    draw_text(W//2 - 70, 25, "DRAGONX1M@", (255, 215, 0, 255))
    draw.line([(W//2 - 100, 55), (W//2 + 100, 55)], fill=(255, 215, 0, 200), width=2)
    draw_text(W//2 - 80, 70, "ELITE OUTFIT", (0, 255, 255, 255))

    # الدوائر
    circles = [
        (250, 280, (0, 255, 255), "HELMET"),
        (250, 500, (255, 0, 255), "VISOR"),
        (250, 720, (255, 255, 0), "ARMOR"),
        (950, 280, (0, 255, 0), "LEG"),
        (950, 500, (255, 100, 0), "BOOTS"),
        (950, 720, (255, 0, 255), "PET"),
    ]

    for idx, future in enumerate(futures):
        if idx >= len(circles):
            break
        x, y, color, name = circles[idx]
        img = future.result()
        if img:
            circular = make_circle_with_border(img, 130, color)
            background.paste(circular, (x - 75, y - 75), circular)
        draw_text(x - 30, y + 75, name, color)

    # السلاح
    weapon_x, weapon_y = W//2, 950
    if weapon_id:
        weapon_url = f'{INFO_URL}/weapon_{weapon_id}.png'
        weapon_img = fetch_image(weapon_url, size=(150, 90))
        if not weapon_img:
            weapon_url = f'{INFO_URL}/{weapon_id}.png'
            weapon_img = fetch_image(weapon_url, size=(150, 90))
        if weapon_img:
            background.paste(weapon_img, (weapon_x - 75, weapon_y - 45), weapon_img)
    draw_text(weapon_x - 35, weapon_y + 50, "WEAPON", (255, 50, 100))

    # Avatar
    avatar_id = "406"
    for skill in equipped_skills:
        if str(skill).endswith("06"):
            avatar_id = str(skill)
            break
    avatar_url = f'https://characteriroxmar.vercel.app/chars?id={avatar_id}'
    avatar_img = fetch_image(avatar_url, size=(340, 400))
    if avatar_img:
        ax = (W - avatar_img.width) // 2
        ay = 380
        background.paste(avatar_img, (ax, ay), avatar_img)

    # اسم اللاعب وتذييل
    draw_text(W//2 - len(player_name)*6, H - 80, player_name.upper(), (255, 215, 0, 255))
    draw_text(W - 130, H - 30, "@DRAGONX1M", (255, 255, 255, 150))

    img_io = BytesIO()
    background.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': '✅ ELITE OUTFIT API',
        'creator': 'DRAGONX1M@',
        'endpoint': '/outfit-image?uid=ID&key=DRAGON-TEAM'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
