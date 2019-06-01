import pytest
import os
import subprocess
import sys
import shutil

if sys.platform != 'win32':
    pytestmark = pytest.mark.skip(
        "PyInstaller is currently only tested on Windows")
else:
    try:
        import PyInstaller
    except ImportError:
        pytestmark = pytest.mark.skip("PyInstaller is not available")


@pytest.mark.incremental
class PyinstallerBase(object):

    pinstall_path = ''

    env = None

    @classmethod
    def setup_class(cls):
        cls.env = cls.get_env()

    @classmethod
    def get_env(cls):
        env = os.environ.copy()
        env['__KIVY_PYINSTALLER_DIR'] = cls.pinstall_path

        if 'PYTHONPATH' not in env:
            env['PYTHONPATH'] = cls.pinstall_path
        else:
            env['PYTHONPATH'] = cls.pinstall_path + os.sep + env['PYTHONPATH']
        return env

    @classmethod
    def get_run_env(cls):
        return os.environ.copy()

    def test_project(self):
        try:
            # check that the project works normally before packaging
            subprocess.check_output(
                [sys.executable or 'python',
                 os.path.join(self.pinstall_path, 'main.py')],
                stderr=subprocess.STDOUT, env=self.env)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

    def test_packaging(self):
        dist = os.path.join(self.pinstall_path, 'dist')
        build = os.path.join(self.pinstall_path, 'build')
        try:
            # create pyinstaller package
            subprocess.check_output(
                [sys.executable or 'python', '-m', 'PyInstaller',
                 os.path.join(self.pinstall_path, 'main.spec'),
                 '--distpath', dist, '--workpath', build],
                stderr=subprocess.STDOUT, env=self.env)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

    def test_packaged_project(self):
        try:
            # test package
            subprocess.check_output(
                os.path.join(self.pinstall_path, 'dist', 'main', 'main'),
                stderr=subprocess.STDOUT, env=self.get_run_env())
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf8'))
            raise

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(
            os.path.join(cls.pinstall_path, '__pycache__'),
            ignore_errors=True)
        shutil.rmtree(
            os.path.join(cls.pinstall_path, 'build'), ignore_errors=True)
        shutil.rmtree(
            os.path.join(cls.pinstall_path, 'dist'), ignore_errors=True)
        shutil.rmtree(
            os.path.join(cls.pinstall_path, 'project', '__pycache__'),
            ignore_errors=True)


class TestSimpleWidget(PyinstallerBase):

    pinstall_path = os.path.join(os.path.dirname(__file__), 'simple_widget')


class TestVideoWidget(PyinstallerBase):

    pinstall_path = os.path.join(os.path.dirname(__file__), 'video_widget')

    @classmethod
    def get_env(cls):
        env = super(TestVideoWidget, cls).get_env()
        env['__KIVY_VIDEO_TEST_FNAME'] = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "examples",
            "widgets", "cityCC0.mpg"))
        return env

    @classmethod
    def get_run_env(cls):
        env = super(TestVideoWidget, cls).get_run_env()
        env['__KIVY_VIDEO_TEST_FNAME'] = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "examples",
            "widgets", "cityCC0.mpg"))
        return env
