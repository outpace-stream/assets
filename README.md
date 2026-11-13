# Outpace assets

Shared brand assets for the [Outpace organization](https://github.com/outpace-stream).

![Outpace logo](logo/outpace-logo.png)

## Single source of truth

**Edit only [logo/outpace-logo.svg](logo/outpace-logo.svg).** It owns the geometry, gradients,
canvas, padding and background color. It contains editable vector paths, with no embedded
bitmap or font dependencies. The hidden `background` layer is enabled for dark exports.

The recreation preserves the original logo's silhouette, layout and orange-and-amber colors.
The raster concept's incidental texture is replaced by clean vector fills.

| Variant | SVG | PNG | JPEG |
| --- | --- | --- | --- |
| Transparent | [Source SVG](logo/outpace-logo.svg) | [PNG](logo/outpace-logo-transparent.png) | Not supported by JPEG |
| Original dark background | [Generated SVG](logo/outpace-logo-dark.svg) | [PNG](logo/outpace-logo.png) | [JPEG](logo/outpace-logo.jpg) |

The PNG and JPEG exports are 1254 × 1254 pixels, matching the source SVG canvas. Transparent
exports keep the colored mark fully filled and the background/play-arrow opening transparent.
The organization avatar uses the dark-background JPEG.

## Edit and regenerate

Open the source SVG in Inkscape, Illustrator, Figma, or a text editor:

- Change the `orange` and `amber` gradient stops to adjust colors.
- Edit the `ring`, `middle-streak`, and `amber-sweep` paths to adjust the shape.
- Edit the `background` layer's fill to change the dark background.
- Keep the `viewBox` and its padding for a consistent avatar crop.

Install Python 3, Pillow and librsvg (`rsvg-convert`). On Debian/Ubuntu:

```bash
sudo apt-get install librsvg2-bin python3-pil
```

Then regenerate **all** exports and check them:

```bash
python3 tools/build-logo-variants.py
python3 tools/build-logo-variants.py --check
python3 -m unittest discover -s tools -p 'test_*.py'
```

`--check` reports missing/stale exports without modifying files. It renders the SVG again and
compares the results with the committed files. After changing a renderer/encoder version,
regenerate and commit the exports together. Do not hand-edit generated SVG, PNG or JPEG files.

The historical [concept prompt](logo/generation-prompt.txt) and
[background-removal prompt](logo/transparent-generation-prompt.txt) document the initial design
process. They are not inputs to the current export pipeline.
