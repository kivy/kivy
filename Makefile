PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/

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
	python setup.py nosetests

cover:
	coverage html --include='kivy*' --omit 'kivy/lib/*,kivy/tools/*,kivy/tests/*'
