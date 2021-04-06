
PYTHON = python3
ifeq (, $(shell which $(PYTHON) 2> /dev/null ))
  PYTHON := python
endif

ifeq (, $(shell which $(PYTHON) 2> /dev/null))
  $(error "PYTHON=$(PYTHON) not found in $(PATH)")
endif

PYTHON_VERSION_MIN=3.0
PYTHON_VERSION=$(shell $(PYTHON) -c 'import sys; print("%d.%d"% sys.version_info[0:2])' )
PYTHON_VERSION_OK=$(shell $(PYTHON) -c 'import sys;\
  print(int(float("%d.%d"% sys.version_info[0:2]) >= $(PYTHON_VERSION_MIN)))' )

ifeq ($(PYTHON_VERSION_OK),0)
  $(error "detected Python $(PYTHON_VERSION) need Python >= $(PYTHON_VERSION_MIN)")
endif
CHECKSCRIPT = -m flake8
KIVY_DIR = kivy/
PYTEST = $(PYTHON) -m pytest
KIVY_USE_DEFAULTCONFIG = 1
HOSTPYTHON = $(KIVYIOSROOT)/tmp/Python-$(PYTHON_VERSION)/hostpython

GIT_COMMAND := $(shell which git)

IOSPATH := $(PATH):/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin

BUILD_OPTS       = build_ext --inplace
BUILD_OPTS_FORCE = $(BUILD_OPTS) -f
BUILD_OPTS_DEBUG = $(BUILD_OPTS_FORCE) -g --cython-gdb

INSTALL_OPTIONS  = install
INSTALL_ROOT     =
INSTALL_PREFIX   =
INSTALL_LAYOUT   =

ifneq ($(INSTALL_ROOT),)
	INSTALL_OPTIONS += --root=$(INSTALL_ROOT)
endif
ifneq ($(INSTALL_PREFIX),)
	INSTALL_OPTIONS += --prefix=$(INSTALL_PREFIX)
endif
ifneq ($(INSTALL_LAYOUT),)
	INSTALL_OPTIONS += --install-layout=$(INSTALL_LAYOUT)
endif

.PHONY: build force mesabuild pdf style hook test batchtest cover clean distclean theming

build:
	$(PYTHON) setup.py $(BUILD_OPTS)

force:
	$(PYTHON) setup.py $(BUILD_OPTS_FORCE)

debug:
	env CFLAGS="-Og" $(PYTHON) setup.py $(BUILD_OPTS_DEBUG)

mesabuild:
	env USE_MESAGL=1 $(PYTHON) setup.py $(BUILD_OPTS)

ios:
	-ln -s $(KIVYIOSROOT)/Python-2.7.1/python
	-ln -s $(KIVYIOSROOT)/Python-2.7.1/python.exe

	-rm -rdf iosbuild/
	mkdir iosbuild

	echo "First build ========================================"
	-PATH="$(IOSPATH)" $(HOSTPYTHON) setup.py build_ext -g
	echo "cythoning =========================================="
	find . -name *.pyx -exec cython {} \;
	echo "Second build ======================================="
	PATH="$(IOSPATH)" $(HOSTPYTHON) setup.py build_ext -g
	PATH="$(IOSPATH)" $(HOSTPYTHON) setup.py install -O2 --root iosbuild
	# Strip away the large stuff
	find iosbuild/ | grep -E '.*\.(py|pyc|so\.o|so\.a|so\.libs)$$' | xargs rm
	-rm -rdf "$(BUILDROOT)/python/lib/python2.7/site-packages/kivy"
	# Copy to python for iOS installation
	cp -R "iosbuild/usr/local/lib/python2.7/site-packages/kivy" "$(BUILDROOT)/python/lib/python2.7/site-packages"

pdf: build
	-cd doc && $(MAKE) pdf
	cd doc && $(MAKE) pdf

html: build
	cd doc && $(MAKE) html

html-embedded:
	env USE_EMBEDSIGNATURE=1 $(MAKE) force
	$(MAKE) -C doc html

style:
	$(PYTHON) $(CHECKSCRIPT) .

hook:
	# Install pre-commit git hook to check your changes for styleguide
	# consistency.
	pre-commit install -f --config=kivy/tools/precommit_hooks/pre-commit-config.yaml

image-testsuite:
	mkdir -p "${KIVY_DIR}tests/image-testsuite"
	-${KIVY_DIR}tools/image-testsuite/imagemagick-testsuite.sh "${KIVY_DIR}tests/image-testsuite"

test:
	# Run tests and print output.
	-rm -rf kivy/tests/build
	env KIVY_NO_ARGS=1 $(PYTEST) kivy/tests

test-to-txt:
	# Run tests with missing line stats and save output to 'coverage.txt'.
	-rm -rf kivy/tests/build
	env KIVY_NO_ARGS=1 $(PYTEST) --cov-report term-missing --cov=kivy kivy/tests > coverage.txt

test-to-xml:
	# Run tests with missing line stats and save output to 'coverage.xml'.
	-rm -rf kivy/tests/build
	env KIVY_NO_ARGS=1 $(PYTEST) --cov-report xml --cov-report term-missing --cov=kivy kivy/tests

cover:
	# Note: This option does not currently support the missing lines analysis.
	coverage html --include='$(KIVY_DIR)*' --omit '$(KIVY_DIR)data/*,$(KIVY_DIR)lib/*,$(KIVY_DIR)tools/*,$(KIVY_DIR)tests/*'

install:
	$(PYTHON) setup.py $(INSTALL_OPTIONS)

clean:
	$(MAKE) -C doc clean
	-rm -rf build
	-rm -rf htmlcov
	-rm -f .coverage
	-rm -f .noseids
	-rm -rf kivy/tests/build
	-find kivy -iname '*.so' -exec rm {} \;
	-find kivy -iname '*.pyd' -exec rm {} \;
	-find kivy -iname '*.pyc' -exec rm {} \;
	-find kivy -iname '*.pyo' -exec rm {} \;
	-find kivy -iname '*.pyx' -exec sh -c 'echo `dirname {}`/`basename {} .pyx`.c' \; | xargs ls -d 2>/dev/null | xargs -r rm

distclean: clean
ifneq ($(GIT_COMMAND),)
ifneq ($(git rev-parse --git-dir 2> /dev/null),)
	@echo "Using GIT at $(GIT_COMMAND) to make a distclean..."
	-git clean -dxf -e debian
else
	@echo "Not in a git directory to make a distclean..."
endif
else
	@echo "GIT not found to make a distclean..."
endif

theming:
	$(PYTHON) -m kivy.atlas kivy/data/images/defaulttheme 512 kivy/tools/theming/defaulttheme/*.png

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  build          for a standard build"
	@echo "  clean          remove generated and compiled files"
	@echo "  cover          create an html coverage report of unittests"
	@echo "  debug          for a debug build (with -g)"
	@echo "  dist-clean     clean then use 'git clean'"
	@echo "  force          for a forced build (with -f)"
	@echo "  hook           add Pep-8 checking as a git precommit hook"
	@echo "  html           to make standalone HTML files"
	@echo "  install        run a setup.py install"
	@echo "  mesabuild      for a build with MesaGL"
	@echo "  style          to check Python code for style issues"
	@echo "  test           run unittests (nosetests)"
	@echo "  theming        create a default theme atlas"
	@echo "  "
	@echo "You can also 'cd doc && make help' to build more documentation types"
