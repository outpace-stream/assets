#!/usr/bin/env python3
"""Render every logo export and app-icon variant from logo/outpace-logo.svg. Requires librsvg and Pillow."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image

from logo_geometry import ICON_VARIANTS, Svg, icon_frame

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def build_variants(source: Path) -> dict[str, bytes]:
    svg = source.read_bytes()
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.fromstring(svg, parser=parser)
    for element in root.iter():
        if element.tag is ET.Comment and 'CANONICAL SOURCE' in (element.text or ''):
            element.text = ' GENERATED FILE: edit logo/outpace-logo.svg, then run tools/build-logo-variants.py. '
    background = next(element for element in root.iter() if element.get('id') == 'background')
    # Geometry, palette, dimensions and background all come from the canonical SVG.
    background.attrib.pop('display', None)
    ET.indent(root, space='  ')
    dark_svg = (ET.tostring(root, encoding='unicode') + '\n').encode()

    transparent_png = render_png(svg)
    dark_png = render_png(dark_svg)
    jpeg = BytesIO()
    with Image.open(BytesIO(dark_png)) as image:
        image.convert('RGB').save(jpeg, format='JPEG', quality=95, optimize=True)
    return {
        'outpace-logo-dark.svg': dark_svg,
        'outpace-logo-transparent.png': transparent_png,
        'outpace-logo.png': dark_png,
        'outpace-logo.jpg': jpeg.getvalue(),
    }


def render_png(data: bytes) -> bytes:
    return subprocess.run(['rsvg-convert', '--format', 'png'], input=data, capture_output=True, check=True).stdout


def build_icons(source: Path) -> dict[str, bytes]:
    """Square app-icon/avatar variants, framed for a circular crop (see logo_geometry)."""
    logo = Svg(source)
    size = logo.view_box[2]
    orange, amber = logo.palette()
    scale, tx, ty = icon_frame(logo, size)
    files = {}
    for name, (background, mark) in ICON_VARIANTS.items():
        if background == 'background':
            back = f'<rect width="{size:g}" height="{size:g}" fill="{logo.background()}"/>'
        elif background == 'gradient':
            back = f'<rect width="{size:g}" height="{size:g}" fill="url(#bg)"/>'
        else:
            back = f'<rect width="{size:g}" height="{size:g}" fill="{background}"/>'
        paths = '\n    '.join(
            f'<path id="{pid}" fill="{mark or colors[0]}" d="{d}"/>' for pid, d, colors in logo.paths()
        )
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:g} {size:g}" role="img" aria-labelledby="title">
  <title id="title">Outpace icon ({name})</title>
  <!-- GENERATED FILE: edit logo/outpace-logo.svg, then run tools/build-logo-variants.py. -->
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="{size:g}" y2="{size:g}" gradientUnits="userSpaceOnUse">
      <stop stop-color="{orange}"/>
      <stop offset="1" stop-color="{amber}"/>
    </linearGradient>
  </defs>
  {back}
  <g transform="translate({tx:.3f} {ty:.3f}) scale({scale:.6f})">
    {paths}
  </g>
</svg>
'''.encode()
        files[f'outpace-icon-{name}.svg'] = svg
        files[f'outpace-icon-{name}.png'] = render_png(svg)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if any export is missing or stale; write nothing.')
    args = parser.parse_args()
    source = ROOT / 'logo' / 'outpace-logo.svg'
    # Finish rendering before writing any outputs, so renderer errors cannot leave a partial build.
    files = {f'logo/{name}': data for name, data in build_variants(source).items()}
    files.update({f'icon/{name}': data for name, data in build_icons(source).items()})
    stale = []
    for name, data in files.items():
        target = ROOT / name
        if args.check:
            if not target.exists() or target.read_bytes() != data:
                stale.append(name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            print(f'Updated {name}')
    if args.check:
        for name in stale:
            print(f'Stale export: {name}')
        if not stale:
            print('All logo exports match the canonical SVG.')
    return int(bool(stale))


if __name__ == '__main__':
    raise SystemExit(main())
