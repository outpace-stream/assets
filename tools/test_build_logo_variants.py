import importlib.util
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPT = Path(__file__).with_name('build-logo-variants.py')
GEOMETRY = Path(__file__).with_name('logo_geometry.py')
sys.path.insert(0, str(SCRIPT.parent))
SOURCE = SCRIPT.parents[1] / 'logo' / 'outpace-logo.svg'
spec = importlib.util.spec_from_file_location('logo_builder', SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class LogoBuildTests(unittest.TestCase):
    def test_renders_transparent_and_dark_variants_from_the_source(self):
        files = builder.build_variants(SOURCE)
        transparent = Image.open(BytesIO(files['outpace-logo-transparent.png'])).convert('RGBA')
        dark = Image.open(BytesIO(files['outpace-logo.png'])).convert('RGBA')
        jpeg = Image.open(BytesIO(files['outpace-logo.jpg']))
        self.assertEqual(transparent.size, (1254, 1254))
        self.assertEqual(transparent.getpixel((0, 0))[3], 0)
        self.assertEqual(transparent.getpixel((627, 627))[3], 0)
        self.assertEqual(transparent.getpixel((627, 300))[3], 255)
        self.assertEqual(dark.getchannel('A').getextrema(), (255, 255))
        self.assertEqual(jpeg.size, dark.size)
        self.assertEqual(jpeg.mode, 'RGB')

    def test_background_color_is_owned_by_the_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.svg'
            source.write_text(SOURCE.read_text().replace('#0a0a0a', '#12ab34'))
            files = builder.build_variants(source)
        dark = Image.open(BytesIO(files['outpace-logo.png'])).convert('RGB')
        jpeg = Image.open(BytesIO(files['outpace-logo.jpg'])).convert('RGB')
        self.assertEqual(dark.getpixel((0, 0)), (18, 171, 52))
        self.assertTrue(all(abs(a - b) <= 3 for a, b in zip(jpeg.getpixel((0, 0)), (18, 171, 52))))

    def test_check_detects_a_stale_export_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'tools').mkdir()
            (root / 'logo').mkdir()
            script = root / 'tools' / SCRIPT.name
            script.write_text(SCRIPT.read_text())
            (root / 'tools' / GEOMETRY.name).write_text(GEOMETRY.read_text())
            (root / 'logo' / SOURCE.name).write_text(SOURCE.read_text())
            subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
            stale = root / 'logo' / 'outpace-logo.png'
            stale.write_bytes(b'stale export')
            result = subprocess.run([sys.executable, str(script), '--check'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('outpace-logo.png', result.stdout)
            self.assertEqual(stale.read_bytes(), b'stale export')


    def test_icon_variants_share_framing_and_differ_in_background(self):
        files = builder.build_icons(SOURCE)
        icons = {name: Image.open(BytesIO(files[f'outpace-icon-{name}.png'])).convert('RGB') for name in ('dark', 'light', 'brand')}
        for image in icons.values():
            self.assertEqual(image.size, (1254, 1254))
        self.assertEqual(icons['dark'].getpixel((10, 10)), (10, 10, 10))
        self.assertEqual(icons['light'].getpixel((10, 10)), (255, 255, 255))
        corner = icons['brand'].getpixel((10, 10))
        self.assertGreater(corner[0], 240)
        self.assertLess(corner[2], 80)
        # The ring is drawn at the same place in every variant: white in "brand", orange elsewhere.
        import logo_geometry
        scale, tx, ty = logo_geometry.icon_frame(logo_geometry.Svg(SOURCE), 1254)
        ring = (round(tx + scale * 800), round(ty + scale * 330))  # inside the ring's orange upper arc
        self.assertEqual(icons['brand'].getpixel(ring), (255, 255, 255))
        self.assertGreater(icons['light'].getpixel(ring)[0], 240)
        self.assertLess(icons['light'].getpixel(ring)[2], 80)

    def test_icon_mark_fits_inside_the_circular_crop(self):
        light = Image.open(BytesIO(builder.build_icons(SOURCE)['outpace-icon-light.png'])).convert('RGB')
        r = 627
        for x in range(0, 1254, 6):
            for y in range(0, 1254, 6):
                if (x - r) ** 2 + (y - r) ** 2 > (0.97 * r) ** 2:
                    self.assertEqual(light.getpixel((x, y)), (255, 255, 255), (x, y))


if __name__ == '__main__':
    unittest.main()
