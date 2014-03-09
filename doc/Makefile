# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
PYTHON		  = python
SPHINXOPTS    = -W
#SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# platform indepnt path separator
# only system calls need to use $(P), b/c on win system calls have issues with /
ifdef ComSpec
	PATHSEP2=\\
	MKDIR=mkdir
else
	PATHSEP2=/
	MKDIR=mkdir -p
endif
P=$(strip $(PATHSEP2))

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) sources
ALLSPHINXOPTSGT = -d build/doctrees_gettext $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) sources

.PHONY: help clean html web pickle htmlhelp latex changes linkcheck gettext

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      to make standalone HTML files"
	@echo "  pickle    to make pickle files (usable by e.g. sphinx-web)"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  changes   to make an overview over all changed/added/deprecated items"
	@echo "  linkcheck to check all external links for integrity"

clean:
# windows just doesn't support e.g. build\*
ifdef ComSpec
	-rmdir /s /q build
else
	-rm -rf build/*
endif

html:
	$(MKDIR) build$(P)html build$(P)doctrees
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) build/html
	@echo
	@echo "Build finished. The HTML pages are in build/html."

gettext:
	$(MKDIR) build$(P)html build$(P)doctrees_gettext
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b gettext $(ALLSPHINXOPTSGT) build/gettext
	@echo
	@echo "Build finished. The Gettext pages are in build/gettext."


pickle:
	$(MKDIR) build$(P)pickle build$(P)doctrees
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) build/pickle
	@echo
	@echo "Build finished; now you can process the pickle files or run"
	@echo "  sphinx-web build/pickle"
	@echo "to start the sphinx-web server."

web: pickle

htmlhelp:
	$(MKDIR) build$(P)htmlhelp build$(P)doctrees
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) build/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in build/htmlhelp."

latex:
	$(MKDIR) build$(P)latex build$(P)doctrees
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) build/latex
	@echo
	@echo "Build finished; the LaTeX files are in build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	$(MKDIR) build$(P)changes build$(P)doctrees
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) build/changes
	@echo
	@echo "The overview file is in build/changes."

linkcheck:
	$(MKDIR) build$(P)linkcheck build$(P)doctrees
	$(PYTHON) autobuild.py
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in build/linkcheck/output.txt."
