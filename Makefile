PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/

mesabuild:
	$(PYTHON) setup.py build_ext --inplace --define __MESAGL__
	$(PYTHON) setup.py build_factory

build:
	$(PYTHON) setup.py build_ext --inplace
	$(PYTHON) setup.py build_factory

style:
	$(PYTHON) $(CHECKSCRIPT) $(KIVY_DIR)

stylereport:
	$(PYTHON) $(CHECKSCRIPT) -html $(KIVY_DIR)

hook:
	cp kivy/tools/pep8checker/pre-commit.githook .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

test:
	-rm -rf kivy/tests/build
	nosetests kivy/tests
# python setup.py nosetests

cover:
	coverage html --include='$(KIVY_DIR)*' --omit '$(KIVY_DIR)lib/*,$(KIVY_DIR)tools/*,$(KIVY_DIR)tests/*'

clean:
	-rm -rf build
	-rm -rf htmlcov
	-rm .coverage
	-rm .noseids
	-rm -rf kivy/tests/build

distclean: clean
	-git clean -dxf
