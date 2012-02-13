'''
reStructuredText renderer
=========================

.. versionadded:: 1.1.0

`reStructuredText <http://docutils.sourceforge.net/rst.html>`_ is an
easy-to-read, what-you-see-is-what-you-get plaintext markup syntax and parser
system.

.. warning::

    This widget is highly experimental. The whole styling and implementation are
    not stable until this warning have been removed.

Usage with text
---------------

::

    text = """
    .. _top:

    Hello world
    ===========

    This is an **emphased text**, some ``interpreted text``.
    And this is a reference to top_::

        $ print "Hello world"

    """
    document = RstDocument(text=text)

The rendering will output:

.. image:: images/rstdocument.png

Usage with source
-----------------

You can also render a rst filename by using :data:`RstDocument.source`::

    document = RstDocument(source='index.rst')

You can reference other documents with the role ``:doc:``. For example, in the
document ``index.rst`` you can write::

    Go to my next document: :doc:`moreinfo.rst`

It will generate a link that user can click, and the document ``moreinfo.rst``
will be loaded.

'''

__all__ = ('RstDocument', )

import os
from os.path import dirname, join, exists
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, \
        DictProperty, ListProperty, StringProperty, \
        BooleanProperty
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.animation import Animation
from kivy.logger import Logger

from docutils.parsers import rst
from docutils.parsers.rst import roles
from docutils import nodes, frontend, utils

#
# Handle some additional roles
#
if 'KIVY_DOC' not in os.environ:

    class role_doc(nodes.Inline, nodes.TextElement):
        pass

    generic_docroles = {
        'doc': role_doc}

    for rolename, nodeclass in generic_docroles.iteritems():
        generic = roles.GenericRole(rolename, nodeclass)
        role = roles.CustomRole(rolename, generic, {'classes': [rolename]})
        roles.register_local_role(rolename, role)

Builder.load_string('''
#:import parse_color kivy.parser.parse_color

<RstDocument>:
    content: content
    scatter: scatter
    canvas:
        Color:
            rgb: .9, .905, .910
        Rectangle:
            pos: self.pos
            size: self.size

    Scatter:
        id: scatter
        size_hint_y: None
        height: content.minimum_height
        width: root.width
        scale: 1
        do_translation: False, False
        do_scale: False
        do_rotation: False

        GridLayout:
            id: content
            cols: 1
            height: self.minimum_height
            width: root.width
            padding: 10

<RstTitle>:
    markup: True
    font_size: 24 - self.section * 2
    size_hint_y: None
    height: self.texture_size[1] + 20
    text_size: self.width, None
    bold: True

    canvas:
        Color:
            rgba: parse_color('204a9699')
        Rectangle:
            pos: self.x, self.y + 5
            size: self.width, 1


<RstParagraph>:
    markup: True
    size_hint_y: None
    height: self.texture_size[1] + self.my
    text_size: self.width - self.mx, None

<RstTerm>:
    markup: True
    size_hint: None, None
    height: self.texture_size[1] + 10
    width: self.texture_size[0] + 10

<RstBlockQuote>:
    cols: 2
    content: content
    size_hint_y: None
    height: content.height
    Widget:
        size_hint_x: None
        width: 20
    GridLayout:
        id: content
        cols: 1
        size_hint_y: None
        height: self.minimum_height

<RstLiteralBlock>:
    cols: 1
    content: content
    size_hint_y: None
    height: content.texture_size[1] + 20
    canvas:
        Color:
            rgb: parse_color('#cccccc')
        Rectangle:
            pos: self.x - 1, self.y - 1
            size: self.width + 2, self.height + 2
        Color:
            rgb: parse_color('#eeeeee')
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        id: content
        markup: True
        text_size: self.width - 20, None
        font_name: 'data/fonts/DroidSansMono.ttf'
        color: (0, 0, 0, 1)

<RstList>:
    cols: 2
    size_hint_y: None
    height: self.minimum_height

<RstListItem>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height

<RstSystemMessage>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height
    canvas:
        Color:
            rgba: 1, 0, 0, .3
        Rectangle:
            pos: self.pos
            size: self.size

<RstWarning>:
    content: content
    cols: 1
    padding: 20
    size_hint_y: None
    height: self.minimum_height
    canvas:
        Color:
            rgba: 1, 0, 0, .5
        Rectangle:
            pos: self.x + 10, self.y + 10
            size: self.width - 20, self.height - 20
    GridLayout:
        cols: 1
        id: content
        size_hint_y: None
        height: self.minimum_height

<RstNote>:
    content: content
    cols: 1
    padding: 20
    size_hint_y: None
    height: self.minimum_height
    canvas:
        Color:
            rgba: 0, 1, 0, .5
        Rectangle:
            pos: self.x + 10, self.y + 10
            size: self.width - 20, self.height - 20
    GridLayout:
        cols: 1
        id: content
        size_hint_y: None
        height: self.minimum_height

<RstImage>:
    size_hint_y: None
    height: self.texture_size[1] + 10

<RstDefinitionList>:
    cols: 2
    size_hint_y: None
    height: self.minimum_height

<RstDefinition>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height

<RstFieldList>:
    cols: 2
    size_hint_y: None
    height: self.minimum_height

<RstFieldName>:
    markup: True
    size_hint: None, 1
    color: (0, 0, 0, 1)
    bold: True
    text_size: self.width - 10, self.height - 10
    valign: 'top'

<RstFieldBody>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height

<RstTable>:
    size_hint_y: None
    height: self.minimum_height

<RstEntry>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height

    canvas:
        Color:
            rgb: .2, .2, .2
        Line:
            points: [self.x, self.y, self.right, self.y, self.right, self.top, self.x, self.top, self.x, self.y]

<RstTransition>:
    size_hint_y: None
    height: 20
    canvas:
        Color:
            rgb: .2, .2, .2
        Line:
            points: [self.x, self.center_y, self.right, self.center_y]

<RstListBullet>:
    markup: True
    size_hint_x: None
    width: self.texture_size[0] + 10
    text_size: None, self.height - 10

<RstEmptySpace>:
    size_hint: 0.01, 0.01
''')


class RstDocument(ScrollView):
    '''Base widget used to store an Rst document. See module documentation for
    more information.
    '''

    source = StringProperty(None)
    '''Filename of the RST document

    :data:`source` is a :class:`~kivy.properties.StringProperty`, default to
    None.
    '''

    text = StringProperty(None)
    '''RST markup text of the document

    :data:`text` is a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    document_root = StringProperty(None)
    '''Root path where :doc: will search any rst document. If no path are
    given, then it will use the directory of the first loaded source.

    :data:`document_root` is a :class:`~kivy.properties.StringProperty`, default
    to None.
    '''

    show_errors = BooleanProperty(False)
    '''Indicate if RST parsers errors must be showed on the screen or not.

    :data:`show_errors` is a :class:`~kivy.properties.BooleanProperty`, default
    to False
    '''

    colors = DictProperty({
        'link': 'ce5c00',
        'paragraph': '202020',
        'title': '204a87',
        'bullet': '000000'})
    '''Dictionnary of all the colors used in the RST rendering.

    .. warning::

        This dictionnary is not yet used completly. You also need to call
        :meth:`RstDocument.render` if you change them after loading.

    :data:`colors` is a :class:`~kivy.properties.DictProperty`.
    '''

    title = StringProperty('')
    '''Title of the current document.

    :data:`title` is a :class:`~kivy.properties.StringProperty`, default to ''
    in read-only.
    '''

    toctrees = DictProperty({})
    '''Toctree of all loaded or preloaded documents. This dictionnary is filled
    when a rst document is explicitly loaded, or where :func:`preload` have been
    called.

    If the document have no filename, ie the document is loaded from a text,
    then the key will be ''.

    :data:`toctrees` is a :class:`~kivy.properties.DictProperty`, default to {}.
    '''

    # internals.
    content = ObjectProperty(None)
    scatter = ObjectProperty(None)
    anchors_widgets = ListProperty([])
    refs_assoc = DictProperty({})

    def __init__(self, **kwargs):
        self._trigger_load = Clock.create_trigger(self._load_from_text, -1)
        self._parser = rst.Parser()
        self._settings = frontend.OptionParser(
            components=(rst.Parser, )
            ).get_default_values()
        super(RstDocument, self).__init__(**kwargs)

    def on_source(self, instance, value):
        if self.document_root is None:
            # set the documentation root to the directory name of the first tile
            self.document_root = dirname(value)
        self._load_from_source()

    def on_text(self, instance, value):
        self._trigger_load()

    def render(self):
        '''Force the document rendering
        '''
        self._load_from_text()

    def resolve_path(self, filename):
        '''Get the path for this filename file. If the filename doesn't exist,
        it will return the document_root + filename.
        '''
        if exists(filename):
            return filename
        return join(self.document_root, filename)

    def preload(self, filename):
        '''Preload a rst file to get its toctree, and its title.

        The result will be stored in :data:`toctrees` with the ``filename`` as
        key.
        '''
        if filename in self.toctrees:
            return
        if not exists(filename):
            return

        with open(filename) as fd:
            text = fd.read()
        # parse the source
        document = utils.new_document('Document', self._settings)
        self._parser.parse(text, document)
        # fill the current document node
        visitor = _ToctreeVisitor(document)
        document.walkabout(visitor)
        self.toctrees[filename] = visitor.toctree

    def _load_from_source(self):
        filename = self.resolve_path(self.source)
        self.preload(filename)
        with open(filename) as fd:
            self.text = fd.read()

    def _load_from_text(self, *largs):
        try:
            # clear the current widgets
            self.content.clear_widgets()
            self.anchors_widgets = []
            self.refs_assoc = {}

            # parse the source
            document = utils.new_document('Document', self._settings)
            self._parser.parse(self.text, document)

            # fill the current document node
            visitor = _Visitor(self, document)
            document.walkabout(visitor)

            self.title = visitor.title or 'No title'
        except:
            Logger.exception('Rst: error while loading text')

    def on_ref_press(self, node, ref):
        # check if it's a file ?
        if self.document_root is not None and ref.endswith('.rst'):
            filename = join(self.document_root, ref)
            if exists(filename):
                self.source = filename
                return

        # get the association
        ref = self.refs_assoc.get(ref)
        #print 'want to go to', ref

        # search into all the nodes containing anchors
        ax = ay = None
        for node in self.anchors_widgets:
            if ref in node.anchors:
                ax, ay = node.anchors[ref]
                break

        # not found, stop here
        if ax is None:
            return

        # found, calculate the real coordinate

        # get the anchor coordinate inside widget space
        ax += node.x
        ay = node.top - ay
        #ay += node.y

        # what's the current coordinate for us?
        sx, sy = self.scatter.x, self.scatter.top
        #ax, ay = self.scatter.to_parent(ax, ay)

        ay -= self.height

        dx, dy = self.convert_distance_to_scroll(0, ay)
        dy = max(0, min(1, dy))
        Animation(scroll_y=dy, d=.25, t='in_out_expo').start(self)

    def add_anchors(self, node):
        self.anchors_widgets.append(node)


class RstTitle(Label):

    section = NumericProperty(0)


class RstParagraph(Label):

    mx = NumericProperty(10)

    my = NumericProperty(10)


class RstTerm(Label):
    pass


class RstBlockQuote(GridLayout):
    content = ObjectProperty(None)


class RstLiteralBlock(GridLayout):
    content = ObjectProperty(None)


class RstList(GridLayout):
    pass


class RstListItem(GridLayout):
    content = ObjectProperty(None)


class RstListBullet(Label):
    pass


class RstSystemMessage(GridLayout):
    pass


class RstWarning(GridLayout):
    content = ObjectProperty(None)


class RstNote(GridLayout):
    content = ObjectProperty(None)


class RstImage(AsyncImage):
    pass


class RstDefinitionList(GridLayout):
    pass


class RstDefinition(GridLayout):
    pass


class RstFieldList(GridLayout):
    pass


class RstFieldName(Label):
    pass


class RstFieldBody(GridLayout):
    pass


class RstGridLayout(GridLayout):
    pass


class RstTable(GridLayout):
    pass


class RstEntry(GridLayout):
    pass


class RstTransition(Widget):
    pass


class RstEmptySpace(Widget):
    pass


class _ToctreeVisitor(nodes.NodeVisitor):

    def __init__(self, *largs):
        self.toctree = self.current = []
        self.queue = []
        self.text = ''
        nodes.NodeVisitor.__init__(self, *largs)

    def push(self, tree):
        self.queue.append(tree)
        self.current = tree

    def pop(self):
        self.current = self.queue.pop()

    def dispatch_visit(self, node):
        cls = node.__class__
        #print '>>>', cls, node.attlist() if hasattr(node, 'attlist') else ''
        if cls is nodes.section:
            section = {
                'ids': node['ids'],
                'names': node['names'],
                'title': '',
                'children': []}
            if isinstance(self.current, dict):
                self.current['children'].append(section)
            else:
                self.current.append(section)
            self.push(section)
        elif cls is nodes.title:
            self.text = ''
        elif cls is nodes.Text:
            self.text += node

    def dispatch_departure(self, node):
        cls = node.__class__
        #print '<--', cls, node.attlist() if hasattr(node, 'attlist') else ''
        if cls is nodes.section:
            self.pop()
        elif cls is nodes.title:
            self.current['title'] = self.text


class _Visitor(nodes.NodeVisitor):

    def __init__(self, root, *largs):
        self.root = root
        self.title = None
        self.current_list = []
        self.current = None
        self.idx_list = None
        self.text = ''
        self.text_have_anchor = False
        self.section = 0
        self.do_strip_text = False
        nodes.NodeVisitor.__init__(self, *largs)

    def push(self, widget):
        self.current_list.append(self.current)
        self.current = widget

    def pop(self):
        self.current = self.current_list.pop()

    def dispatch_visit(self, node):
        cls = node.__class__
        #print '>>>', cls, node.attlist() if hasattr(node, 'attlist') else ''
        if cls is nodes.document:
            self.push(self.root.content)

        elif cls is nodes.section:
            self.section += 1

        elif cls is nodes.title:
            label = RstTitle(section=self.section)
            self.current.add_widget(label)
            self.push(label)
            #assert(self.text == '')

        elif cls is nodes.Text:
            if self.do_strip_text:
                node = node.replace('\n', ' ')
                node = node.replace('  ', ' ')
                node = node.replace('\t', ' ')
                node = node.replace('  ', ' ')
                if node.startswith(' '):
                    node = ' ' + node.lstrip(' ')
                if node.endswith(' '):
                    node = node.rstrip(' ') + ' '
                if self.text.endswith(' ') and node.startswith(' '):
                    node = node[1:]
            self.text += node

        elif cls is nodes.paragraph:
            self.do_strip_text = True
            label = RstParagraph()
            if isinstance(self.current, RstEntry):
                label.mx = 10
            self.current.add_widget(label)
            self.push(label)

        elif cls is nodes.literal_block:
            box = RstLiteralBlock()
            self.current.add_widget(box)
            self.push(box)

        elif cls is nodes.emphasis:
            self.text += '[i]'

        elif cls is nodes.strong:
            self.text += '[b]'

        elif cls is nodes.literal:
            self.text += '[font=fonts/DroidSansMono.ttf]'

        elif cls is nodes.block_quote:
            box = RstBlockQuote()
            self.current.add_widget(box)
            self.push(box.content)
            assert(self.text == '')

        elif cls is nodes.enumerated_list:
            box = RstList()
            self.current.add_widget(box)
            self.push(box)
            self.idx_list = 0

        elif cls is nodes.bullet_list:
            box = RstList()
            self.current.add_widget(box)
            self.push(box)
            self.idx_list = None

        elif cls is nodes.list_item:
            bullet = '-'
            if self.idx_list is not None:
                self.idx_list += 1
                bullet = '%d.' % self.idx_list
            bullet = self.colorize(bullet, 'bullet')
            item = RstListItem()
            self.current.add_widget(RstListBullet(text=bullet))
            self.current.add_widget(item)
            self.push(item)

        elif cls is nodes.system_message:
            label = RstSystemMessage()
            if self.root.show_errors:
                self.current.add_widget(label)
            self.push(label)

        elif cls is nodes.warning:
            label = RstWarning()
            self.current.add_widget(label)
            self.push(label.content)
            assert(self.text == '')

        elif cls is nodes.note:
            label = RstNote()
            self.current.add_widget(label)
            self.push(label.content)
            assert(self.text == '')

        elif cls is nodes.image:
            image = RstImage(source=node['uri'])
            self.current.add_widget(image)

        elif cls is nodes.definition_list:
            lst = RstDefinitionList()
            self.current.add_widget(lst)
            self.push(lst)

        elif cls is nodes.term:
            assert(isinstance(self.current, RstDefinitionList))
            term = RstTerm()
            self.current.add_widget(term)
            self.current.add_widget(RstEmptySpace())
            self.push(term)

        elif cls is nodes.definition:
            assert(isinstance(self.current, RstDefinitionList))
            definition = RstDefinition()
            self.current.add_widget(RstEmptySpace())
            self.current.add_widget(definition)
            self.push(definition)

        elif cls is nodes.field_list:
            fieldlist = RstFieldList()
            self.current.add_widget(fieldlist)
            self.push(fieldlist)

        elif cls is nodes.field_name:
            name = RstFieldName()
            self.current.add_widget(name)
            self.push(name)

        elif cls is nodes.field_body:
            body = RstFieldBody()
            self.current.add_widget(body)
            self.push(body)

        elif cls is nodes.table:
            table = RstTable(cols=0)
            self.current.add_widget(table)
            self.push(table)

        elif cls is nodes.colspec:
            self.current.cols += 1

        elif cls is nodes.entry:
            entry = RstEntry()
            self.current.add_widget(entry)
            self.push(entry)

        elif cls is nodes.transition:
            self.current.add_widget(RstTransition())

        elif cls is nodes.reference:
            name = node.get('name', node.get('refuri'))
            self.text += '[ref=%s][color=%s]' % (name,
                    self.root.colors.get('link', self.root.colors.get('paragraph')))
            if 'refname' in node and 'name' in node:
                self.root.refs_assoc[node['name']] = node['refname']

        elif cls is nodes.target:
            name = None
            if 'ids' in node:
                name = node['ids'][0]
            elif 'names' in node:
                name = node['names'][0]
            self.text += '[anchor=%s]' % name
            self.text_have_anchor = True

        elif cls is role_doc:
            self.doc_index = len(self.text)

    def dispatch_departure(self, node):
        cls = node.__class__
        #print '<--', cls
        if cls is nodes.document:
            self.pop()

        elif cls is nodes.section:
            self.section -= 1

        elif cls is nodes.title:
            assert(isinstance(self.current, RstTitle))
            if not self.title:
                self.title = self.text
            self.set_text(self.current, 'title')
            self.pop()

        elif cls is nodes.Text:
            pass

        elif cls is nodes.paragraph:
            self.do_strip_text = False
            assert(isinstance(self.current, RstParagraph))
            self.set_text(self.current, 'paragraph')
            self.pop()

        elif cls is nodes.literal_block:
            assert(isinstance(self.current, RstLiteralBlock))
            self.set_text(self.current.content, 'literal_block')
            self.pop()

        elif cls is nodes.emphasis:
            self.text += '[/i]'

        elif cls is nodes.strong:
            self.text += '[/b]'

        elif cls is nodes.literal:
            self.text += '[/font]'

        elif cls is nodes.block_quote:
            self.pop()

        elif cls is nodes.enumerated_list:
            self.idx_list = None
            self.pop()

        elif cls is nodes.bullet_list:
            self.pop()

        elif cls is nodes.list_item:
            self.pop()

        elif cls is nodes.system_message:
            self.pop()

        elif cls is nodes.warning:
            self.pop()

        elif cls is nodes.note:
            self.pop()

        elif cls is nodes.definition_list:
            self.pop()

        elif cls is nodes.term:
            assert(isinstance(self.current, RstTerm))
            self.set_text(self.current, 'term')
            self.pop()

        elif cls is nodes.definition:
            self.pop()

        elif cls is nodes.field_list:
            self.pop()

        elif cls is nodes.field_name:
            assert(isinstance(self.current, RstFieldName))
            self.set_text(self.current, 'field_name')
            self.pop()

        elif cls is nodes.field_body:
            self.pop()

        elif cls is nodes.table:
            self.pop()

        elif cls is nodes.colspec:
            pass

        elif cls is nodes.entry:
            self.pop()

        elif cls is nodes.reference:
            self.text += '[/color][/ref]'

        elif cls is role_doc:
            docname = self.text[self.doc_index:]
            rst_docname = docname
            if rst_docname.endswith('.rst'):
                docname = docname[:-4]
            else:
                rst_docname += '.rst'

            # try to preload it
            filename = self.root.resolve_path(rst_docname)
            self.root.preload(filename)

            # if exist, use the title of the first section found in the document
            title = docname
            if filename in self.root.toctrees:
                toctree = self.root.toctrees[filename]
                if len(toctree):
                    title = toctree[0]['title']

            # replace the text with a good reference
            text = '[ref=%s]%s[/ref]' % (
                    rst_docname,
                    self.colorize(title, 'link'))
            self.text = self.text[:self.doc_index] + text

    def set_text(self, node, parent):
        text = self.text
        if parent == 'term' or parent == 'field_name':
            text = '[b]%s[/b]' % text
        # search anchors
        node.text = self.colorize(text, parent)
        node.bind(on_ref_press=self.root.on_ref_press)
        if self.text_have_anchor:
            self.root.add_anchors(node)
        self.text = ''
        self.text_have_anchor = False

    def colorize(self, text, name):
        return '[color=%s]%s[/color]' % (
            self.root.colors.get(name, self.root.colors['paragraph']),
            text)

