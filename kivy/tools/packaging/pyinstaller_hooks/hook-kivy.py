from kivy.tools.packaging.pyinstaller_hooks import (
    add_dep_paths, excludedimports, datas, get_deps_all,
    get_factory_modules, kivy_modules)

add_dep_paths()

hiddenimports = []  # get_deps_all()['hiddenimports']
hiddenimports = list(set(
    get_factory_modules() + kivy_modules + hiddenimports))
