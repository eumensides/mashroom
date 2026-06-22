#!/usr/bin/env python3
"""
蘑菇档案图片批量转 WebP 脚本
=============================
用法：把这个文件放到你的 mashroom 仓库根目录，
然后在终端执行：

    python convert_to_webp.py

脚本会：
1. 扫描当前目录（及子目录）所有 .png 文件
2. 转换为 WebP（quality=82，与原图质量接近但体积约减少 80%）
3. 同时生成一份 320px 缩略图（供卡片封面用）
4. 原 PNG 原样保留，不删除（浏览器不支持 WebP 时可做降级）

依赖：pip install Pillow
"""

from pathlib import Path
from PIL import Image
import sys

# ── 配置区（按需调整） ─────────────────────────────────────────────
QUALITY     = 82        # WebP 质量 1-100，82 视觉上几乎无损，体积节省 ~80%
THUMB_WIDTH = 640       # 卡片封面宽度（像素），原图宽度小于此值则跳过缩放
LOSSLESS    = False     # True = 无损 WebP（体积更大），False = 有损（推荐）
SKIP_DIRS   = {'.git', 'node_modules', '__pycache__'}
# ────────────────────────────────────────────────────────────────────


def convert(png_path: Path) -> dict:
    img = Image.open(png_path).convert("RGB")
    orig_w, orig_h = img.size
    orig_kb = png_path.stat().st_size / 1024

    results = {}

    # 1. 全尺寸 WebP（与 PNG 同名，扩展名换成 .webp）
    webp_path = png_path.with_suffix('.webp')
    img.save(webp_path, format='WEBP', quality=QUALITY, lossless=LOSSLESS,
             method=6)   # method=6 最慢但最小体积
    webp_kb = webp_path.stat().st_size / 1024
    results['full'] = (webp_path, orig_kb, webp_kb)

    # 2. 缩略图（仅当原图宽度 > THUMB_WIDTH 才缩放）
    if orig_w > THUMB_WIDTH:
        ratio    = THUMB_WIDTH / orig_w
        new_size = (THUMB_WIDTH, int(orig_h * ratio))
        thumb    = img.resize(new_size, Image.LANCZOS)
        thumb_path = png_path.parent / (png_path.stem + '_thumb.webp')
        thumb.save(thumb_path, format='WEBP', quality=QUALITY, lossless=LOSSLESS,
                   method=6)
        thumb_kb = thumb_path.stat().st_size / 1024
        results['thumb'] = (thumb_path, orig_kb, thumb_kb)

    return results


def main():
    root = Path('.')
    pngs = sorted([
        p for p in root.rglob('*.png')
        if not any(part in SKIP_DIRS for part in p.parts)
    ])

    if not pngs:
        print("当前目录下没有找到 PNG 文件。请确认脚本和图片在同一目录。")
        sys.exit(0)

    print(f"找到 {len(pngs)} 张 PNG，开始转换...\n")
    total_orig = total_webp = 0

    for i, png in enumerate(pngs, 1):
        try:
            res = convert(png)
            full_path, orig_kb, webp_kb = res['full']
            saved = (1 - webp_kb / orig_kb) * 100
            total_orig += orig_kb
            total_webp += webp_kb
            thumb_note = ""
            if 'thumb' in res:
                tp, _, tkb = res['thumb']
                thumb_note = f"  + 缩略图 {tp.name} ({tkb:.0f} KB)"
            print(f"[{i:>3}/{len(pngs)}] {png.name}")
            print(f"       {orig_kb:>7.0f} KB → {webp_kb:>6.0f} KB  "
                  f"(节省 {saved:.0f}%){thumb_note}")
        except Exception as e:
            print(f"[{i:>3}/{len(pngs)}] ✗ {png.name}  错误: {e}")

    saved_total = (1 - total_webp / total_orig) * 100
    print(f"\n完成！共节省 {total_orig - total_webp:.0f} KB"
          f"  ({total_orig:.0f} KB → {total_webp:.0f} KB，减少 {saved_total:.0f}%)")
    print("\n下一步：")
    print("  1. git add *.webp *_thumb.webp")
    print("  2. git commit -m 'add WebP versions for faster loading'")
    print("  3. git push")
    print("  4. 替换 HTML 里的图片引用：把 xxx.png 改成 xxx.webp（见下方说明）")


if __name__ == '__main__':
    main()
