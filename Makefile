PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/

mesabuild:
	$(PYTHON) setup.py build_ext --inplace --define __MESAGL__

build:
	$(PYTHON) setup.py build_ext --inplace

style:
	$(PYTHON) $(CHECKSCRIPT) $(KIVY_DIR)

stylereport:
	$(PYTHON) $(CHECKSCRIPT) -html $(KIVY_DIR)

hook:
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
