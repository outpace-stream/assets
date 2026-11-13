#!/usr/bin/env python3
"""Render the Android launcher icon, themed icon, notification icon, in-app mark and TV banner as
VectorDrawable XML from logo/outpace-logo.svg and wordmark/outpace-wordmark-dark.svg.

The output under android/res mirrors an Android res/ tree, so an app copies it as is. VectorDrawable
gradients need API 24, so the base files use solid fills (the logo's gradients are nearly flat) and
drawable-v24 adds the banner with the wordmark's real gradient.
"""
import argparse
from pathlib import Path

from logo_geometry import ICON_VARIANTS, Svg, bounds, icon_frame, union

ROOT = Path(__file__).resolve().parents[1]
ANDROID = 'xmlns:android="http://schemas.android.com/apk/res/android"'
AAPT = 'xmlns:aapt="http://schemas.android.com/aapt"'
HEADER = '<!-- GENERATED FILE: edit {sources}, then run tools/build-android-icons.py. -->'

# The launcher icon variant, from logo_geometry.ICON_VARIANTS: "light" (white disc), "dark" or "brand".
ANDROID_ICON = 'light'
# Launchers show a 72dp circle (or other mask) of the 108dp adaptive canvas; frame the mark for it.
LAUNCHER_CANVAS, LAUNCHER_VISIBLE = 108, 72
NOTIFICATION_FIT = 0.96
BANNER = (320, 180)
BANNER_MARK_HEIGHT = 86
BANNER_WORD_HEIGHT = 38.6
BANNER_GAP = 14


def argb(color: str) -> str:
    return '#FF' + color.lstrip('#').upper()


def compact(d: str) -> str:
    return ' '.join(d.split())


def vector(width, height, view_w, view_h, body, sources, aapt=False):
    ns = f'{ANDROID} {AAPT}' if aapt else ANDROID
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + HEADER.format(sources=sources) + '\n'
        + f'<vector {ns}\n    android:width="{width}dp" android:height="{height}dp"'
        + f' android:viewportWidth="{view_w:g}" android:viewportHeight="{view_h:g}">\n'
        + body + '\n</vector>\n'
    )


def group(scale, tx, ty, paths_xml):
    inner = '\n'.join('    ' + line for line in paths_xml.splitlines())
    return (
        f'    <group android:scaleX="{scale:.6f}" android:scaleY="{scale:.6f}"'
        f' android:translateX="{tx:.4f}" android:translateY="{ty:.4f}">\n{inner}\n    </group>'
    )


def solid_paths(paths, mono=None):
    return '\n'.join(
        f'    <path android:name="{pid}" android:fillColor="{mono or argb(colors[0])}" android:pathData="{d}" />'
        for pid, d, colors in paths
    )


def gradient_path(pid, d, colors, x1, x2):
    return (
        f'    <path android:name="{pid}" android:pathData="{d}">\n'
        '        <aapt:attr name="android:fillColor">\n'
        f'            <gradient android:type="linear" android:startX="{x1:g}" android:startY="0"'
        f' android:endX="{x2:g}" android:endY="0"'
        f' android:startColor="{argb(colors[0])}" android:endColor="{argb(colors[-1])}" />\n'
        '        </aapt:attr>\n'
        '    </path>'
    )


def build(logo_path: Path, word_path: Path) -> dict[str, bytes]:
    logo = Svg(logo_path)
    word = Svg(word_path)
    mark = logo.paths()
    x0, y0, x1, y1 = union([bounds(d) for _, d, _ in mark])
    mw, mh, cx, cy = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2
    logo_src = 'logo/outpace-logo.svg'
    files = {}

    def centred(canvas, fit, mono=None):
        s = canvas * fit / mw
        return group(s, canvas / 2 - s * cx, canvas / 2 - s * cy, solid_paths(mark, mono))

    background_kind, mark_color = ICON_VARIANTS[ANDROID_ICON]
    ls, ltx, lty = icon_frame(logo, LAUNCHER_CANVAS, LAUNCHER_VISIBLE)
    launcher_mark = argb(mark_color) if mark_color else None
    files['drawable/ic_launcher_foreground.xml'] = vector(
        108, 108, 108, 108, group(ls, ltx, lty, solid_paths(mark, launcher_mark)), logo_src)
    files['drawable/ic_launcher_monochrome.xml'] = vector(
        108, 108, 108, 108, group(ls, ltx, lty, solid_paths(mark, '#FFFFFFFF')), logo_src)
    if background_kind == 'gradient':
        orange, amber = logo.palette()
        fill = (f'<gradient android:type="linear" android:angle="315"'
                f' android:startColor="{argb(orange)}" android:endColor="{argb(amber)}" />')
    else:
        color = logo.background() if background_kind == 'background' else background_kind
        fill = f'<solid android:color="{argb(color)}" />'
    # A shape, not a vector, so the brand gradient works on every API level.
    files['drawable/ic_launcher_background.xml'] = (
        '<?xml version="1.0" encoding="utf-8"?>\n' + HEADER.format(sources=logo_src) + '\n'
        f'<shape {ANDROID} android:shape="rectangle">\n    {fill}\n</shape>\n'
    )
    files['drawable/ic_notification.xml'] = vector(24, 24, 24, 24, centred(24, NOTIFICATION_FIT, '#FFFFFFFF'), logo_src)
    files['drawable/logo_mark.xml'] = vector(40, 40, 40, 40, centred(40, 1.0), logo_src)

    background = argb(logo.background())
    files['values/outpace_brand.xml'] = (
        '<?xml version="1.0" encoding="utf-8"?>\n' + HEADER.format(sources=logo_src) + '\n<resources>\n'
        f'    <color name="logo_bg">{background}</color>\n</resources>\n'
    )
    files['mipmap-anydpi-v26/ic_launcher.xml'] = (
        HEADER.format(sources=logo_src) + '\n'
        f'<adaptive-icon {ANDROID}>\n'
        '    <background android:drawable="@drawable/ic_launcher_background" />\n'
        '    <foreground android:drawable="@drawable/ic_launcher_foreground" />\n'
        '    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />\n'
        '</adaptive-icon>\n'
    )
    files['mipmap/ic_launcher.xml'] = (
        HEADER.format(sources=logo_src) + '\n'
        f'<layer-list {ANDROID}>\n'
        '    <item><shape android:shape="oval">' + fill + '</shape></item>\n'
        '    <item android:drawable="@drawable/ic_launcher_foreground" />\n'
        '</layer-list>\n'
    )

    # TV banner: mark and wordmark side by side on the logo background.
    wx, wy, ww, wh = word.view_box
    bw, bh = BANNER
    ms = BANNER_MARK_HEIGHT / mh
    ws = BANNER_WORD_HEIGHT / wh
    left = (bw - (mw * ms + BANNER_GAP + ww * ws)) / 2
    mark_xml = group(ms, left - ms * x0, bh / 2 - ms * cy, solid_paths(mark))
    word_left = left + mw * ms + BANNER_GAP
    word_tx, word_ty = word_left - ws * wx, bh / 2 - ws * (wy + wh / 2)
    backdrop = f'    <path android:name="background" android:fillColor="{background}" android:pathData="M0,0h{bw}v{bh}h-{bw}z" />'
    word_paths = word.paths()
    banner_src = f'{logo_src} or wordmark/outpace-wordmark-dark.svg'
    solid_word = solid_paths([(pid, d, colors) for pid, d, colors in word_paths])
    files['drawable/banner.xml'] = vector(bw, bh, bw, bh, '\n'.join([backdrop, mark_xml, group(ws, word_tx, word_ty, solid_word)]), banner_src)
    gx0, _, gx1, _ = union([bounds(d) for pid, d, c in word_paths if len(c) > 1])
    gradient_word = '\n'.join(
        gradient_path(pid, d, colors, gx0, gx1) if len(colors) > 1 else solid_paths([(pid, d, colors)])
        for pid, d, colors in word_paths
    )
    files['drawable-v24/banner.xml'] = vector(
        bw, bh, bw, bh, '\n'.join([backdrop, mark_xml, group(ws, word_tx, word_ty, gradient_word)]), banner_src, aapt=True,
    )
    return {name: text.encode() for name, text in files.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='Fail if any output is missing or stale; write nothing.')
    args = parser.parse_args()
    files = build(ROOT / 'logo' / 'outpace-logo.svg', ROOT / 'wordmark' / 'outpace-wordmark-dark.svg')
    out = ROOT / 'android' / 'res'
    stale = []
    for name, data in files.items():
        target = out / name
        if args.check:
            if not target.exists() or target.read_bytes() != data:
                stale.append(name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            print(f'Updated android/res/{name}')
    if args.check:
        for name in stale:
            print(f'Stale output: android/res/{name}')
        if not stale:
            print('All Android drawables match the canonical SVGs.')
    return int(bool(stale))


if __name__ == '__main__':
    raise SystemExit(main())
