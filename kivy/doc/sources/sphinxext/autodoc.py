# -*- coding: utf-8 -*-
from sphinx.ext.autodoc import Documenter, ClassDocumenter
from sphinx.ext.autodoc import setup as core_setup
from sphinx.locale import _


class KivyClassDocumenter(ClassDocumenter):
    def add_directive_header(self, sig):
        if self.doc_as_attr:
            self.directivetype = 'attribute'
        Documenter.add_directive_header(self, sig)

        def fix(mod):
            if mod == 'kivy._event':
                mod = 'kivy.event'
            return mod

        # add inheritance info, if wanted
        if not self.doc_as_attr and self.options.show_inheritance:
            self.add_line('', '<autodoc>')
            if len(self.object.__bases__):
                bases = [b.__module__ == '__builtin__' and
                         ':class:`%s`' % b.__name__ or
                         ':class:`%s.%s`' % (fix(b.__module__), b.__name__)
                         for b in self.object.__bases__]
                self.add_line(_('   Bases: %s') % ', '.join(bases),
                              '<autodoc>')
def setup(app):
    core_setup(app)
    app.add_autodocumenter(KivyClassDocumenter)
