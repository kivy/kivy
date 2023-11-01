import os
from tempfile import TemporaryDirectory

from unittest import mock


def test_garden_import_module():
    with TemporaryDirectory() as tmpdir:
        fake_garden_dir = os.path.join(tmpdir, "garden")

        with mock.patch("kivy.garden.garden_system_dir", fake_garden_dir):
            # Add a fake garden module to the temporary directory
            dummy_flower_dir = os.path.join(
                fake_garden_dir, "garden.dummyflower"
            )
            os.makedirs(dummy_flower_dir, exist_ok=True)

            with open(os.path.join(dummy_flower_dir, "__init__.py"), "w") as f:
                f.write("dummy_var = 1")

            from kivy.garden.dummyflower import dummy_var

            assert dummy_var == 1
