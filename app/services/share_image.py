"""分享卡片缩略图生成（og:image 用）。

后端用 Pillow 渲染深色品牌卡片：项目名 + 大号分数 + 决策档位。
爬虫（微信等）不执行 JS，所以分享缩略图必须由后端产出真实 PNG。
生成结果按 (id, 分数) 缓存到磁盘，避免每次抓取都重绘。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.scoring import get_decision

# 用系统中文字体，不入库特定字体。按常见路径探测，找不到退回默认字体。
# Linux 服务器建议：sudo apt install -y fonts-noto-cjk
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",   # 文泉驿（部分发行版自带）
    "/System/Library/Fonts/PingFang.ttc",               # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",         # macOS
]
_FONT_PATH = next((p for p in _FONT_CANDIDATES if Path(p).exists()), None)


def _font(size: int) -> ImageFont.FreeTypeFont:
    if _FONT_PATH:
        return ImageFont.truetype(_FONT_PATH, size)
    return ImageFont.load_default(size)  # 无中文字体时退回（仅英文/数字可读）

# 卡片尺寸（正方形，适配微信缩略图）
W = H = 600
PAD = 56

# 决策档位 → 主题色
_TIER_COLORS = {
    "Strong Yes": (52, 211, 153),     # 绿
    "Cautious Yes": (255, 206, 107),  # 琥珀
    "Keep in Touch": (96, 165, 250),  # 蓝
    "Pass": (248, 113, 113),          # 红
}
_DEFAULT_TIER = (255, 206, 107)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_FONT_PATH, size)


def _radial_bg() -> Image.Image:
    """深色径向渐变背景（右上偏亮）。先小图逐像素再放大，省时。"""
    s = 120
    small = Image.new("RGB", (s, s))
    px = small.load()
    cx, cy = s * 0.75, s * 0.15           # 高光中心：右上
    top = (22, 50, 79)                    # #16324f
    mid = (10, 23, 38)                    # #0a1726
    bot = (6, 13, 24)                     # #060d18
    maxd = ((s) ** 2 + (s) ** 2) ** 0.5
    for y in range(s):
        for x in range(s):
            d = (((x - cx) ** 2 + (y - cy) ** 2) ** 0.5) / maxd  # 0..~1
            if d < 0.55:
                t = d / 0.55
                c = tuple(int(top[i] + (mid[i] - top[i]) * t) for i in range(3))
            else:
                t = min(1.0, (d - 0.55) / 0.45)
                c = tuple(int(mid[i] + (bot[i] - mid[i]) * t) for i in range(3))
            px[x, y] = c
    return small.resize((W, H), Image.BILINEAR)


def _wrap(draw, text: str, font, max_w: int, max_lines: int) -> list[str]:
    """按宽度折行（CJK 无空格，逐字测量）；超出 max_lines 末尾省略号。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""
            continue
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if len(lines) == max_lines:
        # 末行可能被截断，确保放得下省略号
        last = lines[-1]
        while last and draw.textlength(last + "…", font=font) > max_w:
            last = last[:-1]
        # 如果原文确实超长，补省略号
        consumed = sum(len(l) for l in lines)
        if consumed < len(text.replace("\n", "")):
            lines[-1] = last + "…"
    return lines


def _render(project_name: str, final_score: float, decision: dict) -> Image.Image:
    img = _radial_bg()
    d = ImageDraw.Draw(img)

    label = decision.get("label", "")
    chinese = decision.get("chinese", "")
    tier = _TIER_COLORS.get(label, _DEFAULT_TIER)

    # 顶部品牌行
    f_brand = _font(22)
    d.text((PAD, PAD), "AI 投资大师 · 评估报告", font=f_brand, fill=(111, 168, 255))

    # 项目名（最多两行）
    f_name = _font(40)
    name = (project_name or "未知项目").strip()
    lines = _wrap(d, name, f_name, W - PAD * 2, 2)
    y = PAD + 52
    for ln in lines:
        d.text((PAD, y), ln, font=f_name, fill=(245, 248, 252))
        y += 52

    # 大号分数（底部偏上）
    f_score = _font(150)
    f_max = _font(40)
    score_txt = str(int(round(final_score)))
    sy = H - PAD - 200
    d.text((PAD, sy), score_txt, font=f_score, fill=(90, 209, 255))
    sw = d.textlength(score_txt, font=f_score)
    d.text((PAD + sw + 14, sy + 96), "/ 100", font=f_max, fill=(107, 128, 153))

    # 决策胶囊
    f_dec = _font(26)
    dec_txt = f"{label} · {chinese}" if chinese else label
    tx0, ty0 = PAD, H - PAD - 56
    tw = d.textlength(dec_txt, font=f_dec)
    pill_w = int(tw + 48)
    pill_h = 52
    r = pill_h // 2
    fill = tuple(list(tier) + [36])  # 低透明度底
    d.rounded_rectangle([tx0, ty0, tx0 + pill_w, ty0 + pill_h], radius=r,
                        fill=tuple(int(c * 0.18 + 12) for c in tier),
                        outline=tier, width=2)
    d.text((tx0 + 24, ty0 + (pill_h - 34) // 2), dec_txt, font=f_dec, fill=tier)

    return img


def _cache_dir() -> Path:
    from app.config import get_settings
    base = Path(get_settings().upload_dir).resolve().parent  # 通常 data/
    p = base / "share_cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_share_image(evaluation_id: int, project_name: str, final_score: float) -> bytes:
    """生成（或读取缓存）分享卡片 PNG，返回二进制。"""
    decision = get_decision(final_score or 0)
    cache = _cache_dir() / f"{evaluation_id}_{int(round(final_score or 0))}.png"
    if cache.exists():
        return cache.read_bytes()
    img = _render(project_name, final_score or 0, decision)
    img.save(cache, "PNG")
    return cache.read_bytes()
