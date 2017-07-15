import os
from os.path import basename, realpath, relpath
from .lddtree import parse_ld_paths

from elftools.elf.elffile import ELFFile  # type: ignore
from elftools.common.exceptions import ELFError  # type: ignore
from typing import Iterator, Tuple, Optional, Dict, List


def elf_read_dt_needed(fn : str) -> List[str]:
    needed = []
    with open(fn, 'rb') as f:
        elf = ELFFile(f)
        section = elf.get_section_by_name('.dynamic')
        if section is None:
            raise ValueError('Could not find soname in %s' % fn)

        if not hasattr(section, 'iter_tags'):
            return needed

        for t in section.iter_tags():
            if t.entry.d_tag == 'DT_NEEDED':
                needed.append(t.needed)

    return needed


def elf_file_filter(paths: Iterator[str]) -> Iterator[Tuple[str, ELFFile]]:
    """Filter through an iterator of filenames and load up only ELF
    files
    """

    for path in paths:
        if path.endswith('.py'):
            continue
        else:
            try:
                with open(path, 'rb') as f:
                    candidate = ELFFile(f)
                    yield path, candidate
            except ELFError:
                # not an elf file
                continue


def elf_find_versioned_symbols(elf: ELFFile) -> Iterator[Tuple[str, str]]:
    section = elf.get_section_by_name('.gnu.version_r')

    if section is not None:
        for verneed, verneed_iter in section.iter_versions():
            if verneed.name.startswith('ld-linux'):
                continue
            for vernaux in verneed_iter:
                yield (verneed.name,
                       vernaux.name)


def elf_find_ucs2_symbols(elf: ELFFile) -> Iterator[str]:
    section = elf.get_section_by_name('.dynsym')
    if section is not None:
        # look for UCS2 symbols that are externally referenced
        for sym in section.iter_symbols():
            if ('PyUnicodeUCS2_' in sym.name and
                    sym['st_shndx'] == 'SHN_UNDEF' and
                    sym['st_info']['type'] == 'STT_FUNC'):

                yield sym.name


def elf_references_PyFPE_jbuf(elf: ELFFile) -> bool:
    offending_symbol_names = ('PyFPE_jbuf', 'PyFPE_dummy', 'PyFPE_counter')
    section = elf.get_section_by_name('.dynsym')
    if section is not None:
        # look for symbols that are externally referenced
        for sym in section.iter_symbols():
            if (sym.name in offending_symbol_names and
                    sym['st_shndx'] == 'SHN_UNDEF' and
                    sym['st_info']['type'] in ('STT_FUNC', 'STT_NOTYPE')):
                return True
    return False


def elf_is_python_extension(fn, elf) -> Tuple[bool, Optional[int]]:
    modname = basename(fn).split('.', 1)[0]
    module_init_f = {'init' + modname: 2, 'PyInit_' + modname: 3}

    sect = elf.get_section_by_name('.dynsym')
    if sect is None:
        return False, None

    for sym in sect.iter_symbols():
        if (sym.name in module_init_f and
                sym['st_shndx'] != 'SHN_UNDEF' and
                sym['st_info']['type'] == 'STT_FUNC'):

            return True, module_init_f[sym.name]

    return False, None


def elf_read_rpaths(fn: str) -> Dict[str, List[str]]:
    result = {'rpaths': [], 'runpaths': []}  # type: Dict[str, List[str]]

    with open(fn, 'rb') as f:
        elf = ELFFile(f)
        section = elf.get_section_by_name('.dynamic')
        if section is None:
            return result

        for t in section.iter_tags():
            if t.entry.d_tag == 'DT_RPATH':
                result['rpaths'] = parse_ld_paths(
                    t.rpath,
                    root='/',
                    path=fn)
            elif t.entry.d_tag == 'DT_RUNPATH':
                result['runpaths'] = parse_ld_paths(
                    t.runpath,
                    root='/',
                    path=fn)

    return result


def is_subdir(path: str, directory: str) -> bool:
    if path is None:
        return False

    path = realpath(path)
    directory = realpath(directory)

    relative = relpath(path, directory)
    if relative.startswith(os.pardir):
        return False
    return True
