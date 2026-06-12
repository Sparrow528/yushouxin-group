#!/usr/bin/env python3
"""
开票二维码生成器 — 可配置版本
读 invoice-qrcode/config.json，生成：
  1. HTML展示页（扫码打开）
  2. 展示页版二维码海报（PNG）
  3. 纯文本版二维码海报（PNG）

用法: python3 generate.py [path/to/config.json]
"""

import json
import os
import sys
from pathlib import Path

# ── 依赖 ──────────────────────────────────────────
try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请先安装依赖: pip install qrcode[pil] pillow")
    sys.exit(1)


# ── 加载配置 ──────────────────────────────────────
def load_config(path=None):
    if path is None:
        path = Path(__file__).parent / "config.json"
    else:
        path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 生成展示页HTML ────────────────────────────────
def generate_html(cfg) -> str:
    c = cfg["company"]
    s = cfg["style"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0, user-scalable=yes">
<title>开票信息 - {c["name"]}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
  background: {s["bg_color"]};
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
}}
.card {{
  background: {s["card_bg"]};
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.06);
  max-width: 440px;
  width: 100%;
  overflow: hidden;
}}
.top-bar {{
  background: linear-gradient(135deg, {s["primary_color"]}, {s["secondary_color"]});
  padding: 28px 20px 20px;
  text-align: center;
}}
.top-bar .icon {{ font-size: 36px; margin-bottom: 8px; }}
.top-bar h1 {{
  color: #fff; font-size: 18px; font-weight: 600; line-height: 1.5;
}}
.top-bar .sub {{
  color: rgba(255,255,255,0.65); font-size: 12px; margin-top: 6px; letter-spacing: 2px;
}}
.content {{ padding: 24px 20px 28px; }}
.row {{
  display: flex; padding: 14px 0; border-bottom: 1px solid #f0f4f8;
}}
.row:last-child {{ border-bottom: none; }}
.label {{
  flex: 0 0 78px; font-size: 13px; color: #8a9bb0; font-weight: 500; line-height: 1.6;
}}
.value {{
  flex: 1; font-size: 14px; color: #1a2a3a; line-height: 1.6; word-break: break-all;
}}
.value.tax {{
  font-size: 16px; font-weight: 700; color: {s["primary_color"]}; letter-spacing: 1.5px;
}}
.value.account {{
  font-size: 15px; letter-spacing: 1px; font-weight: 600; color: {s["primary_color"]};
}}
.hint {{
  margin-top: 18px; text-align: center; font-size: 12px; color: #a0b0c0;
}}
.footer {{
  background: #f7f9fc; padding: 12px 20px; text-align: center;
  font-size: 11px; color: #b5c0cd;
}}
</style>
</head>
<body>
<div class="card">
  <div class="top-bar">
    <div class="icon">🧾</div>
    <h1>{c["name"]}</h1>
    <div class="sub">开 票 信 息</div>
  </div>
  <div class="content">
    <div class="row"><div class="label">单位名称</div><div class="value">{c["name"]}</div></div>
    <div class="row"><div class="label">纳税人识别号</div><div class="value tax">{c["tax_id"]}</div></div>
    <div class="row"><div class="label">地址</div><div class="value">{c["address"]}</div></div>
    <div class="row"><div class="label">开户银行</div><div class="value">{c["bank"]}</div></div>
    <div class="row"><div class="label">银行账号</div><div class="value account">{c["account"]}</div></div>
    <div class="hint">请将以上信息提供给开票方开具发票</div>
  </div>
  <div class="footer">长按识别二维码 · 保存开票信息</div>
</div>
</body>
</html>"""


# ── 生成二维码图片 ────────────────────────────────
def make_qrcode(content: str, cfg, output_path: str, label: str = ""):
    """生成二维码海报"""
    o = cfg["output"]
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    qr_img = qr.make_image(
        fill_color=o["qrcode_fill_color"],
        back_color=o["qrcode_bg_color"],
    ).convert("RGB")

    # 海报尺寸
    qr_size = o["qrcode_size"]
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    c = cfg["company"]
    short = c["short_name"]

    # 字体探测
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            break
    if not font_path:
        font_path = "/usr/share/fonts"

    def get_font(size):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            return ImageFont.load_default()

    def tw(text, font):
        try:
            return font.getlength(text)
        except AttributeError:
            return font.getsize(text)[0]

    def th(font):
        try:
            m = font.getmetrics()
            return m[0] + m[1]
        except AttributeError:
            return font.size + 4

    # --- 常量 ---
    margin = 40
    gap = 10

    # 内容行
    is_webpage = content.startswith("http")
    if is_webpage:
        title_text = f"📄 {c['name']}"
        sub_text = "扫码查看完整开票信息"
        all_info = [
            ["公司名称", c["name"]],
            ["纳税人识别号", c["tax_id"]],
            ["地址", c["address"]],
            ["开户银行", c["bank"]],
            ["银行账号", c["account"]],
        ]
    else:
        title_text = f"📄 {short} - 开票信息"
        sub_text = "扫码查看 | 长按保存"
        all_info = [
            ["纳税人识别号", c["tax_id"]],
            ["开户银行", c["bank"]],
            ["银行账号", c["account"]],
        ]

    ft = get_font(22)
    fs = get_font(13)
    fl = get_font(11)
    fv = get_font(13)

    ht = th(ft)
    hs = th(fs)
    hl = th(fl)
    hv = th(fv)

    # 计算画布尺寸
    info_h = (hv + gap) * len(all_info) + hl * len(all_info) + gap
    canvas_w = qr_size + 80
    canvas_h = margin + ht + 6 + hs + 20 + info_h + 20 + qr_size + 12 + 8 + hs + margin

    img = Image.new("RGB", (canvas_w, canvas_h), "#ffffff")
    draw = ImageDraw.Draw(img)

    y = margin

    # 标题
    draw.text(((canvas_w - tw(title_text, ft)) / 2, y), title_text,
              fill="#1e3a5f", font=ft)
    y += ht + 6

    # 副标题
    draw.text(((canvas_w - tw(sub_text, fs)) / 2, y), sub_text,
              fill="#8a9bb0", font=fs)
    y += hs + 20

    # 信息行
    for label, val in all_info:
        draw.text((margin + 8, y), label, fill="#8a9bb0", font=fl)
        y += hl
        draw.text((margin + 8, y), val, fill="#1a2a3a", font=fv)
        y += hv + gap

    y += 10

    # 二维码居中
    qr_x = (canvas_w - qr_size) // 2
    img.paste(qr_img, (qr_x, y))
    y += qr_size + 12

    # 底部分隔线
    draw.line([(margin, y), (canvas_w - margin, y)], fill="#f0f4f8", width=1)
    y += 8

    # 底部提示
    tip = "长按识别二维码 · 保存开票信息"
    draw.text(((canvas_w - tw(tip, fs)) / 2, y), tip, fill="#b5c0cd", font=fs)

    img.save(output_path, "PNG")
    print(f"✅ 已生成: {output_path}")


# ── 主流程 ────────────────────────────────────────
def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else None
    cfg = load_config(cfg_path)

    c = cfg["company"]
    o_dir = Path(cfg.get("output", {}).get("dir", "output"))
    o_dir.mkdir(parents=True, exist_ok=True)

    short = c["short_name"] or c["name"]

    # 1. HTML展示页
    html = generate_html(cfg)
    html_path = o_dir / f"{short}-开票信息.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 已生成: {html_path}")

    # 2. 纯文本版 — 二维码直接包含文字信息（不用网络也能看）
    text_content = (
        f"{c['name']}\n"
        f"纳税人识别号: {c['tax_id']}\n"
        f"地址: {c['address']}\n"
        f"开户银行: {c['bank']}\n"
        f"银行账号: {c['account']}"
    )
    make_qrcode(text_content, cfg, str(o_dir / f"{short}-开票二维码-纯文本.png"))

    # 3. 展示页版 — 二维码指向GitHub Pages上的HTML展示页
    # 部署后URL格式: https://sparrow528.github.io/yushouxin-group/invoice-qrcode/output/{short}-开票信息.html
    deploy_url = f"https://sparrow528.github.io/yushouxin-group/invoice-qrcode/output/{short}-开票信息.html"
    make_qrcode(deploy_url, cfg, str(o_dir / f"{short}-开票二维码.png"),
                label=f"{c['name']} 开票信息")
    print(f"   📍 展示页URL: {deploy_url}")

    print(f"\n📁 所有文件位于: {o_dir.resolve()}")
    print(f"配置方法: 修改 config.json 中的公司信息，重新运行 python3 generate.py")
    print(f"注意: 展示页版二维码已指向上述URL，请确保HTML已部署到GitHub Pages再使用。")


if __name__ == "__main__":
    main()
