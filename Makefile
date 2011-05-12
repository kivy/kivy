PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/
HOSTPYTHON = ../python-for-iphone/Python-2.6.5/hostpython

.PHONY: build force mesabuild pdf style stylereport hook test batchtest cover clean distclean

build:
	$(PYTHON) setup.py build_ext --inplace

force:
	$(PYTHON) setup.py build_ext --inplace -f

mesabuild:
	$(PYTHON) setup.py build_ext --inplace --define __MESAGL__

ios:
	-mkdir extralibs
	-ln -s ../python-for-iphone/Python-2.6.5/python

	-rm -rdf iosbuild/
	mkdir iosbuild

	echo "First build ========================================"
	-$(HOSTPYTHON) setup.py build
	echo "cythoning =========================================="
	find . -name *.pyx -exec cython {} \;
	echo "Second build ======================================="
	$(HOSTPYTHON) setup.py install -O2 --root iosbuild
	# Strip away the large stuff
	find iosbuild/ | grep -E '*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
	-rm -rdf "../python-for-iphone/Python-2.6.5/_install/lib/python2.6/site-packages/kivy"
	# Copy to python for iOS installation
	cp -R "iosbuild/usr/local/lib/python2.6/site-packages/kivy" "../python-for-iphone/Python-2.6.5/_install/lib/python2.6/site-packages"

pdf:
	$(MAKE) -C doc latex && make -C doc/build/latex all-pdf

style:
	$(PYTHON) $(CHECKSCRIPT) $(KIVY_DIR)

stylereport:
	$(PYTHON) $(CHECKSCRIPT) -html $(KIVY_DIR)

hook:
	# Install pre-commit git hook to check your changes for styleguide
	# consistency.
	cp kivy/tools/pep8checker/pre-commit.githook .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

test:
	-rm -rf kivy/tests/build
	UNITTEST_INTERACTIVE=1 nosetests kivy/tests

batchtest:
	-rm -rf kivy/tests/build
	nosetests kivy/tests

cover:
	coverage html --include='$(KIVY_DIR)*' --omit '$(KIVY_DIR)lib/*,$(KIVY_DIR)tools/*,$(KIVY_DIR)tests/*'

clean:
	-rm -rf doc/build
	-rm -rf build
	-rm -rf htmlcov
	-rm .coverage
	-rm .noseids
	-rm -rf kivy/tests/build
	-find kivy -iname '*.pyc' -exec rm {} \;
	-find kivy -iname '*.pyo' -exec rm {} \;

distclean: clean
	-git clean -dxf
