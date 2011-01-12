PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/

style:
	$(PYTHON) $(CHECKSCRIPT) $(KIVY_DIR)

stylereport:
	$(PYTHON) $(CHECKSCRIPT) -html $(KIVY_DIR)
