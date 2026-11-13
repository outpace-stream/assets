import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).with_name('build-android-icons.py')
ROOT = SCRIPT.parents[1]
LOGO = ROOT / 'logo' / 'outpace-logo.svg'
WORD = ROOT / 'wordmark' / 'outpace-wordmark-dark.svg'
ANDROID = '{http://schemas.android.com/apk/res/android}'
spec = importlib.util.spec_from_file_location('android_builder', SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AndroidIconTests(unittest.TestCase):
    def setUp(self):
        self.files = builder.build(LOGO, WORD)

    def parse(self, name):
        return ET.fromstring(self.files[name])

    def test_every_output_is_well_formed_xml(self):
        for name in self.files:
            with self.subTest(name=name):
                self.parse(name)

    def test_launcher_paths_come_from_the_visible_logo_layers(self):
        root = self.parse('drawable/ic_launcher_foreground.xml')
        names = [p.get(ANDROID + 'name') for p in root.iter('path')]
        self.assertEqual(names, ['ring', 'middle-streak', 'amber-sweep'])
        self.assertEqual(root.get(ANDROID + 'viewportWidth'), '108')

    def test_monochrome_and_notification_are_white_silhouettes(self):
        for name in ('drawable/ic_launcher_monochrome.xml', 'drawable/ic_notification.xml'):
            fills = {p.get(ANDROID + 'fillColor') for p in self.parse(name).iter('path')}
            self.assertEqual(fills, {'#FFFFFFFF'}, name)

    def test_background_color_is_owned_by_the_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'logo.svg'
            source.write_text(LOGO.read_text().replace('#0a0a0a', '#12ab34'))
            files = builder.build(source, WORD)
        self.assertIn(b'#FF12AB34', files['values/outpace_brand.xml'])
        self.assertIn(b'#FF12AB34', files['drawable/banner.xml'])

    def test_banner_gradient_only_in_v24(self):
        self.assertNotIn(b'<gradient', self.files['drawable/banner.xml'])
        self.assertIn(b'<gradient', self.files['drawable-v24/banner.xml'])

    def test_check_detects_a_stale_output_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ('tools/' + SCRIPT.name, 'logo/' + LOGO.name, 'wordmark/' + WORD.name):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text((ROOT / rel).read_text())
            script = root / 'tools' / SCRIPT.name
            subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
            stale = root / 'android' / 'res' / 'drawable' / 'ic_notification.xml'
            stale.write_text('stale')
            result = subprocess.run([sys.executable, str(script), '--check'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('ic_notification.xml', result.stdout)
            self.assertEqual(stale.read_text(), 'stale')


if __name__ == '__main__':
    unittest.main()
