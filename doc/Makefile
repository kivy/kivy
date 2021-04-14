# Makefile for Sphinx documentation
#

ENDUSER_BUILD	= yes

# You can set these variables from the command line.
PYTHON = python3
ifeq (, $(shell which $(PYTHON) 2> /dev/null ))
  PYTHON := python
endif

ifeq (, $(shell which $(PYTHON) 2> /dev/null))
  $(error "PYTHON=$(PYTHON) not found in $(PATH)")
endif

SPHINXOPTS	= -Q
SPHINXOPTS_TEST	= -W -T
SPHINXBUILD	= sphinx-build
PAPER		=

fasthtml: SPHINXOPTS += -j4

# platform independent path separator
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
PAPEROPT_a4		= -D latex_paper_size=a4
PAPEROPT_letter		= -D latex_paper_size=letter
ALLSPHINXOPTS		= -d build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) sources
ALLSPHINXOPTS_TEST	= -d build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS_TEST) sources
ALLSPHINXOPTSGT		= -d build/doctrees_gettext $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) sources
ALLSPHINXOPTSGT_TEST	= -d build/doctrees_gettext $(PAPEROPT_$(PAPER)) $(SPHINXOPTS_TEST) sources
LATEXOPTS		= -interaction=batchmode
LATEXOPTS_TESTS		=

ifeq ($(ENDUSER_BUILD),yes)
	_TESTS =
else
	_TESTS = _TEST
endif

# Created in autobuild.py
AUTOBUILD_STAMP = "autobuild.py-done"

.PHONY: help clean html web pickle htmlhelp latex changes linkcheck gettext

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  build-all to build the common documentation types."
	@echo "  changes   to make an overview over all changed/added/deprecated items"
	@echo "  clean     to remove generated files"
	@echo "  gettext   to make gettext pages"
	@echo "  html      to make standalone HTML files"
	@echo "  fasthtml  same as html, with 4 concurrent processes"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  linkcheck to check through the reference linking"
	@echo "  man       to build Man doctrees."
	@echo "  pdf       to make standalone PDF files"
	@echo "  pickle    to make pickle files (usable by e.g. sphinx-web)"
	@echo "  ps        to make standalone PS files"
	@echo "  web       same as pickle"

clean:
	-rm -rf sources/api-*.rst
	-rm -rf sources/examples/gen__*.rst
	-rm -rf sources/examples/gallery.rst
	-rm -rf sources/examples/index.rst
# windows just doesn't support e.g. build\*
ifdef ComSpec
	-rmdir /s /q build
else
	-rm -rf build/*
	-rm $(AUTOBUILD_STAMP)*
endif

fasthtml: html

html:
	$(MKDIR) build$(P)html build$(P)doctrees
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS$(_TESTS)) build/html
	@echo
	@echo "Build finished. The HTML pages are in build/html."

gettext:
	$(MKDIR) build$(P)html build$(P)doctrees_gettext
	$(SPHINXBUILD) -b gettext $(ALLSPHINXOPTSGT$(_TESTS)) build/gettext
	@echo
	@echo "Build finished. The Gettext pages are in build/gettext."


pickle:
	$(MKDIR) build$(P)pickle build$(P)doctrees
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS$(_TESTS)) build/pickle
	@echo
	@echo "Build finished; now you can process the pickle files or run"
	@echo "  sphinx-web build/pickle"
	@echo "to start the sphinx-web server."

web: pickle

htmlhelp:
	$(MKDIR) build$(P)htmlhelp build$(P)doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS$(_TESTS)) build/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in build/htmlhelp."

latex:
	$(MKDIR) build$(P)latex build$(P)doctrees
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS$(_TESTS)) build/latex
	@echo
	@echo "Build finished; the LaTeX files are in build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' to" \
	      "run these through (pdf)latex."

pdf: latex
	rm -f build$(P)latex$(P)Kivy.pdf
	-$(MAKE) -C build$(P)latex all-pdf LATEXOPTS=$(LATEXOPTS$(_TESTS))

ifneq ("$(wildcard build$(P)latex$(P)Kivy.pdf)","")
	@echo
	@echo "Build finished; the PDF file(s) are in build/latex."
	@echo "You can safely ignore the errors which might appeared above!"
else
	@echo
	@echo "Build failed; there is no PDF file(s) in build/latex."
	exit 1
endif

ps: latex
	$(MAKE) -C build$(P)latex all-ps
	@echo
	@echo "Build finished; the PS files are in build/latex."

man:
	$(MKDIR) build$(P)man build$(P)doctrees
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS$(_TESTS)) build/man
	@echo
	@echo "Build finished. The manual pages are in build/man."

changes:
	$(MKDIR) build$(P)changes build$(P)doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS$(_TESTS)) build/changes
	@echo
	@echo "The overview file is in build/changes."

linkcheck:
	$(MKDIR) build$(P)linkcheck build$(P)doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS$(_TESTS)) build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in build/linkcheck/output.txt."

build-all: html pickle htmlhelp pdf ps gettext

# TODO: Make test run in non-enduser-build mode
test: build-all
