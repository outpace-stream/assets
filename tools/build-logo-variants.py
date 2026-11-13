#!/usr/bin/env python3
"""Render every logo export from logo/outpace-logo.svg. Requires librsvg and Pillow."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image

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

    def render(data: bytes) -> bytes:
        return subprocess.run(
            ['rsvg-convert', '--format', 'png'], input=data,
            capture_output=True, check=True,
        ).stdout

    transparent_png = render(svg)
    dark_png = render(dark_svg)
    jpeg = BytesIO()
    with Image.open(BytesIO(dark_png)) as image:
        image.convert('RGB').save(jpeg, format='JPEG', quality=95, optimize=True)
    return {
        'outpace-logo-dark.svg': dark_svg,
        'outpace-logo-transparent.png': transparent_png,
        'outpace-logo.png': dark_png,
        'outpace-logo.jpg': jpeg.getvalue(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if any export is missing or stale; write nothing.')
    args = parser.parse_args()
    directory = ROOT / 'logo'
    # Finish rendering before writing any outputs, so renderer errors cannot leave a partial build.
    files = build_variants(directory / 'outpace-logo.svg')
    stale = []
    for name, data in files.items():
        target = directory / name
        if args.check:
            if not target.exists() or target.read_bytes() != data:
                stale.append(name)
        else:
            target.write_bytes(data)
            print(f'Updated logo/{name}')
    if args.check:
        for name in stale:
            print(f'Stale export: logo/{name}')
        if not stale:
            print('All logo exports match the canonical SVG.')
    return int(bool(stale))


if __name__ == '__main__':
    raise SystemExit(main())
