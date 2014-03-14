from __future__ import print_function
import os
import sys
import shutil
import zipfile
import shlex
from zipfile import ZipFile
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve
from subprocess import Popen, PIPE
from distutils.cmd import Command
from os.path import join, dirname, abspath, exists

PY2 = sys.version_info[0] == 2
PYVER = '2.7' if PY2 else '3.3'


def zip_directory(dir, zip_file):
    zip = ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(abspath(dir))
    for root, dirs, files in os.walk(dir):
        archive_root = abspath(root)[root_len:]
        for f in files:
            fullpath = join(root, f)
            archive_name = join(archive_root, f)
            zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    zip.close()


class WindowsPortableBuild(Command):
    description = "custom build command that builds portable win32 package"
    user_options = [
        ('dist-dir=', None,
         "path of dist directory to use for building portable kivy, the end result will be output to this driectory. Defaults to cwd."),
        ('deps-url=', None,
         "url of binary dependancies for portable kivy package default: http://kivy.googlecode.com/files/portable-deps-win32.zip"),
        ('no-cext', None,
         "flag to disable building of c extensions"),
        ('no-mingw', None,
         "flag to disable bundling of mingw compiler for compiling c/cython extensions")]

    def initialize_options(self):
        self.dist_dir = None
        self.deps_url = None
        self.no_cext = None
        self.no_mingw = None

    def finalize_options(self):
        if not self.deps_url:
            self.deps_url = 'http://kivy.googlecode.com/files/portable-deps-win32.zip'
        if not self.dist_dir:
            self.dist_dir = os.getcwd()

        self.src_dir = dirname(sys.modules['__main__'].__file__)
        self.dist_name = self.distribution.get_fullname() # e.g. Kivy-0.5 (name and verison passed to setup())
        self.build_dir = join(self.dist_dir, '{}-py{}-win32'.format(
            self.dist_name, PYVER))

    def run(self):
        width = 30
        print("-" * width)
        print("Building Kivy Portable for Win 32")
        print("-" * width)
        print("\nPreparing Build...")
        print("-" * width)
        if exists(self.build_dir):
            print("*Cleaning old build dir")
            shutil.rmtree(self.build_dir, ignore_errors=True)
        print("*Creating build directory:", self.build_dir)
        os.makedirs(self.build_dir)


        print("\nGetting binary dependencies...")
        print("---------------------------------------")
        print("*Downloading:", self.deps_url)
        #report_hook is called every time a piece of teh file is downloaded to print progress
        def report_hook(block_count, block_size, total_size):
            p = block_count * block_size * 100.0 / total_size
            print("\b\b\b\b\b\b\b\b\b", "%06.2f" % p + "%", end=' ')
        print(" Progress: 000.00%", end=' ')
        urlretrieve(self.deps_url, # location of binary dependencies needed for portable kivy
                    join(self.build_dir, 'deps.zip'), # tmp file to store the archive
                    reporthook = report_hook)
        print(" [Done]")


        print("*Extracting binary dependencies...")
        zf = ZipFile(join(self.build_dir, 'deps.zip'))
        zf.extractall(self.build_dir)
        zf.close()
        if self.no_mingw:
            print("*Excluding MinGW from portable distribution (--no-mingw option is set)")
            shutil.rmtree(join(self.build_dir, 'MinGW'), ignore_errors=True)

        # let only the right python in the directory
        if PY2:
            shutil.rmtree(join(self.build_dir, 'Python33'), ignore_errors=True)
        else:
            shutil.rmtree(join(self.build_dir, 'Python27'), ignore_errors=True)


        print("\nPutting kivy into portable environment")
        print("---------------------------------------")
        print("*Building kivy source distribution")
        sdist_cmd = [sys.executable, #path to python.exe
                     join(self.src_dir, 'setup.py'), #path to setup.py
                     'sdist', #make setup.py create a src distribution
                     '--dist-dir=%s'%self.build_dir] #put it into build folder
        Popen(sdist_cmd, stdout=PIPE, stderr=PIPE).communicate()


        print("*Placing kivy source distribution in portable context")
        src_dist = join(self.build_dir, self.dist_name)
        zf = ZipFile(src_dist+'.zip')
        zf.extractall(self.build_dir)
        zf.close()
        if self.no_mingw or self.no_cext:
            print("*Skipping C Extension build (either --no_cext or --no_mingw option set)")
        else:
            print("*Compiling C Extensions inplace for portable distribution")
            cext_cmd = [sys.executable, #path to python.exe
                        'setup.py',
                        'build_ext', #make setup.py create a src distribution
                        '--force',
                        '--inplace'] #do it inplace
            #this time it runs teh setup.py inside the source distribution
            #thats has been generated inside the build dir (to generate ext
            #for teh target, instead of the source were building from)
            Popen(cext_cmd, cwd=src_dist).communicate()


        print("\nFinalizing kivy portable distribution...")
        print("---------------------------------------")
        print("*Copying scripts and resources")
        #copy launcher script and readme to portable root dir/build dir
        for srcname, dstname in (
                ('kivy-{}.bat', 'kivy.bat'),
                ('kivyenv-{}.sh', 'kivyenv.sh'),
                ('kivyenvwine-{}.sh', 'kivywineenv.sh'),
                ('README.txt', 'README.txt')):
            srcname = srcname.format(PYVER)
            shutil.copy(
                join(src_dist, 'kivy', 'tools', 'packaging', 'win32', srcname),
                join(self.build_dir, dstname))

        #rename kivy directory to "kivy"
        os.rename(src_dist, join(self.build_dir, 'kivy'))

        print("*Removing intermediate file")
        os.remove(join(self.build_dir, 'deps.zip'))
        os.remove(join(self.build_dir, src_dist + '.zip'))

        print("*Compressing portable distribution target")
        target = join(self.dist_dir, "{}-py{}-win32.zip".format(
            self.dist_name, PYVER))
        zip_directory(self.build_dir, target)
        print("*Writing target:", target)
        print("*Removing build dir")
        shutil.rmtree(self.build_dir, ignore_errors=True)

