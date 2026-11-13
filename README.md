# Outpace assets

Shared brand assets for the [Outpace organization](https://github.com/outpace-stream).

![Outpace logo](logo/outpace-logo.png)

## Editable vector logo

- [Transparent SVG](logo/outpace-logo.svg): canonical editable source.
- [Dark-background SVG](logo/outpace-logo-dark.svg): generated from the same source.

![Editable vector recreation](logo/outpace-logo-dark.svg)

This is a hand-built vector recreation of the original mark, with smooth Bézier curves
and editable orange/amber gradients. It contains no embedded bitmap or font dependencies.
The original PNG/JPEG files remain unchanged; the organization avatar uses the original
filled logo on its dark background.

To edit the logo, open `logo/outpace-logo.svg` in Inkscape, Illustrator, Figma, or a text editor:

- Change the `orange` and `amber` gradient stops to adjust colors.
- Edit the `ring`, `middle-streak`, and `amber-sweep` paths to adjust the shape.
- Keep the `viewBox` and its padding for a consistent avatar crop.
- Run `python3 tools/build-logo-variants.py` to update the dark-background version.
  Its background color is defined in that script.

For a PNG export, use an SVG editor or librsvg, for example:

```bash
rsvg-convert -w 1024 -h 1024 -o outpace-logo-export.png logo/outpace-logo.svg
```

## Raster logo variants

- [Transparent PNG](logo/outpace-logo-transparent.png): filled orange-and-amber mark with an alpha-transparent background and play-arrow opening.
- [Original PNG](logo/outpace-logo.png): 1254 × 1254 pixels.
- [JPEG avatar copy](logo/outpace-logo.jpg): the smaller upload copy used for the organization avatar.
- [Generation prompt](logo/generation-prompt.txt): the prompt used with the built-in image generation tool.
- [Transparent variant prompt](logo/transparent-generation-prompt.txt): the background-removal edit instructions.

The logo combines an orange-and-amber motion mark with a play arrow on a charcoal background.
