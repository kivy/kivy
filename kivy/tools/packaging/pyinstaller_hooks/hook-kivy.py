from kivy.tools.packaging.pyinstaller_hooks import (
    add_dep_paths, excludedimports, datas, get_kivy_providers,
    get_factory_modules, kivy_modules)

add_dep_paths()

hiddenimports = []  # get_kivy_providers()['hiddenimports']
hiddenimports = list(set(
    get_factory_modules() + kivy_modules + hiddenimports))
