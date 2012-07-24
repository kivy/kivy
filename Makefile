PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/
NOSETESTS = nosetests

.PHONY: build force mesabuild pdf style stylereport hook test batchtest cover clean distclean theming

build:
	$(PYTHON) setup.py build_ext --inplace

force:
	$(PYTHON) setup.py build_ext --inplace -f

mesabuild:
	/usr/bin/env USE_MESAGL=1 $(PYTHON) setup.py build_ext --inplace

pdf:
	$(MAKE) -C doc latex && make -C doc/build/latex all-pdf

html:
	$(MAKE) -C doc html

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
	$(NOSETESTS) kivy/tests

cover:
	coverage html --include='$(KIVY_DIR)*' --omit '$(KIVY_DIR)data/*,$(KIVY_DIR)lib/*,$(KIVY_DIR)tools/*,$(KIVY_DIR)tests/*'

install:
	python setup.py install
clean:
	-rm -rf doc/build
	-rm -rf build
	-rm -rf htmlcov
	-rm .coverage
	-rm .noseids
	-rm -rf kivy/tests/build
	-find kivy -iname '*.so' -exec rm {} \;
	-find kivy -iname '*.pyc' -exec rm {} \;
	-find kivy -iname '*.pyo' -exec rm {} \;

distclean: clean
	-git clean -dxf

theming:
	python -m kivy.atlas kivy/data/images/defaulttheme 512 kivy/tools/theming/defaulttheme/*.png

