import importlib.util
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPT = Path(__file__).with_name('build-logo-variants.py')
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
            (root / 'logo' / SOURCE.name).write_text(SOURCE.read_text())
            subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
            stale = root / 'logo' / 'outpace-logo.png'
            stale.write_bytes(b'stale export')
            result = subprocess.run([sys.executable, str(script), '--check'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('outpace-logo.png', result.stdout)
            self.assertEqual(stale.read_bytes(), b'stale export')


if __name__ == '__main__':
    unittest.main()
