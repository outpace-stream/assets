#!/usr/bin/env python3
"""Build the dark-background SVG from the canonical transparent vector logo."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

source = ROOT / "logo" / "outpace-logo.svg"
parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
root = ET.fromstring(source.read_text(), parser=parser)
_, _, width, height = root.attrib["viewBox"].split()
background = ET.Element(f"{{{NS}}}rect", {
    "id": "background", "width": width, "height": height, "fill": "#0a0a0a",
})
# Keep title/description first, then put the background behind the artwork.
root.insert(2, background)
ET.indent(root, space="  ")
target = ROOT / "logo" / "outpace-logo-dark.svg"
target.write_text(ET.tostring(root, encoding="unicode") + "\n")
print(f"Updated {target.relative_to(ROOT)}")
