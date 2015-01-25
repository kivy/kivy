PYTHON = python
CHECKSCRIPT = kivy/tools/pep8checker/pep8kivy.py
KIVY_DIR = kivy/
NOSETESTS = nosetests
KIVY_USE_DEFAULTCONFIG = 1
HOSTPYTHON = $(KIVYIOSROOT)/tmp/Python-$(PYTHON_VERSION)/hostpython

GIT_COMMAND := $(shell which git)

IOSPATH := $(PATH):/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin

BUILD_OPTS       = build_ext --inplace
BUILD_OPTS_FORCE = $(BUILD_OPTS) -f
BUILD_OPTS_DEBUG = $(BUILD_OPTS_FORCE)-g

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


.PHONY: build force mesabuild pdf style stylereport hook test batchtest cover clean distclean theming

prebuild:
ifeq ("$(wildcard kivy-already-built-for-$(PYTHON))","")
	@echo Building Kivy as it is not already done!
	$(PYTHON) setup.py $(BUILD_OPTS)
	touch kivy-already-built-for-$(PYTHON)
else
	@echo Kivy is already built for \"$(PYTHON)\"!
endif

build:
	$(PYTHON) setup.py $(BUILD_OPTS)

force:
	$(PYTHON) setup.py $(BUILD_OPTS_FORCE)

debug:
	$(PYTHON) setup.py $(BUILD_OPTS_DEBUG)

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

pdf: prebuild
	cd doc && $(MAKE) pdf

html: prebuild
	cd doc && $(MAKE) html

html-embedded:
	env USE_EMBEDSIGNATURE=1 $(MAKE) force
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
	$(PYTHON) setup.py $(INSTALL_OPTIONS)

clean:
	$(MAKE) -C doc clean
	-rm -f kivy-already-built*
	-rm -rf build
	-rm -rf htmlcov
	-rm -f .coverage
	-rm -f .noseids
	-rm -rf kivy/tests/build
	-find kivy -iname '*.so' -exec rm {} \;
	-find kivy -iname '*.pyc' -exec rm {} \;
	-find kivy -iname '*.pyo' -exec rm {} \;
	-find . -iname '*.pyx' -exec sh -c 'echo `dirname {}`/`basename {} .pyx`.c' \; | xargs rm

distclean: clean
ifneq ($(GIT_COMMAND),)
	@echo "Using GIT at $(GIT_COMMAND) to make a distclean..."
	-git clean -dxf -e debian
else
	@echo "GIT not found to make a distclean..."
endif

theming:
	$(PYTHON) -m kivy.atlas kivy/data/images/defaulttheme 512 kivy/tools/theming/defaulttheme/*.png
