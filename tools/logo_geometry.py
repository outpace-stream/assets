"""Shared reading and framing of the canonical logo SVG, for the export and Android scripts."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SVG = '{http://www.w3.org/2000/svg}'

# App icons and avatars are cropped to a circle. The mark takes this share of the circle's width,
# and is shifted so the ring, not the whole silhouette with its motion streaks, sits near the
# centre: OPTICAL_WEIGHT of the way from the bounding-box centre to the ring's centre.
ICON_FIT = 0.62
OPTICAL_WEIGHT = 0.6

# Square icon variants: (background, mark color or None for the logo's own colors).
# "brand" fills the background with the logo's orange-to-amber and draws the mark in white.
ICON_VARIANTS = {
    'dark': ('background', None),
    'light': ('#ffffff', None),
    'brand': ('gradient', '#ffffff'),
}


class Svg:
    def __init__(self, path: Path):
        self.root = ET.parse(path).getroot()
        self.view_box = [float(v) for v in self.root.get('viewBox').split()]
        self.gradients = {
            g.get('id'): [s.get('stop-color') for s in g.iter(SVG + 'stop')]
            for g in self.root.iter(SVG + 'linearGradient')
        }

    def paths(self):
        """Visible paths in drawing order, as (id, d, colors). Hidden layers are skipped."""
        out = []

        def walk(element, hidden):
            hidden = hidden or element.get('display') == 'none'
            for child in element:
                if child.tag == SVG + 'path' and not hidden:
                    fill = child.get('fill')
                    ref = re.fullmatch(r'url\(#(.+)\)', fill or '')
                    colors = self.gradients[ref.group(1)] if ref else [fill]
                    out.append((child.get('id'), ' '.join(child.get('d').split()), colors))
                elif child.tag == SVG + 'g':
                    walk(child, hidden)

        walk(self.root, False)
        return out

    def background(self) -> str:
        layer = next(e for e in self.root.iter() if e.get('id') == 'background')
        return next(layer.iter(SVG + 'rect')).get('fill')

    def palette(self):
        """The first stop of each gradient, in document order (orange, then amber)."""
        return [stops[0] for stops in self.gradients.values()]


def bounds(d: str):
    """Bounding box of a path's points (curve control points included, so slightly generous)."""
    xs, ys, x, y = [], [], 0.0, 0.0
    for cmd, args in re.findall(r'([MLHVCQZmlhvcqz])([^MLHVCQZmlhvcqz]*)', d):
        nums = [float(n) for n in re.findall(r'-?\d*\.?\d+(?:e-?\d+)?', args)]
        if cmd == 'H':
            for x in nums:
                xs.append(x); ys.append(y)
        elif cmd == 'V':
            for y in nums:
                xs.append(x); ys.append(y)
        elif cmd in 'MLCQ':
            for i in range(0, len(nums) - 1, 2):
                x, y = nums[i], nums[i + 1]
                xs.append(x); ys.append(y)
        elif cmd not in 'Zz':
            raise ValueError(f'relative path command {cmd} is not supported')
    return min(xs), min(ys), max(xs), max(ys)


def union(boxes):
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)


def mark_box(logo: Svg):
    return union([bounds(d) for _, d, _ in logo.paths()])


def icon_frame(logo: Svg, canvas: float, circle: float = None):
    """Scale and translation that place the mark in a square `canvas`, framed for a circular crop of
    diameter `circle` (the whole canvas by default), as (scale, tx, ty)."""
    x0, y0, x1, y1 = mark_box(logo)
    ring = next(bounds(d) for pid, d, _ in logo.paths() if pid == 'ring')
    # The ring's outer arc spans its full height, so its centre is one radius in from the right.
    ring_cx = ring[2] - (ring[3] - ring[1]) / 2
    cx = (x0 + x1) / 2 + OPTICAL_WEIGHT * (ring_cx - (x0 + x1) / 2)
    cy = (y0 + y1) / 2
    s = (circle or canvas) * ICON_FIT / (x1 - x0)
    return s, canvas / 2 - s * cx, canvas / 2 - s * cy
