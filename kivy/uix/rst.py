'''
reStructuredText renderer
=========================

.. versionadded:: 1.1.0

`reStructuredText <http://docutils.sourceforge.net/rst.html>`_ is an
easy-to-read, what-you-see-is-what-you-get plaintext markup syntax and parser
system.

.. note::

    This widget requires the ``docutils`` package to run. Install it with
    ``pip`` or include it as one of your deployment requirements.

.. warning::

    This widget is highly experimental. The styling and implementation should
    not be considered stable until this warning has been removed.

Usage with Text
---------------

::

    text = """
    .. _top:

    Hello world
    ===========

    This is an **emphased text**, some ``interpreted text``.
    And this is a reference to top_::

        $ print("Hello world")

    """
    document = RstDocument(text=text)

The rendering will output:

.. image:: images/rstdocument.png

Usage with Source
-----------------

You can also render a rst file using the :attr:`~RstDocument.source` property::

    document = RstDocument(source='index.rst')

You can reference other documents using the role ``:doc:``. For example, in the
document ``index.rst`` you can write::

    Go to my next document: :doc:`moreinfo.rst`

It will generate a link that, when clicked, opens the ``moreinfo.rst``
document.

'''

__all__ = ('RstDocument', )

import os
from os.path import dirname, join, exists, abspath
from kivy.clock import Clock
from kivy.compat import PY2
from kivy.properties import ObjectProperty, NumericProperty, \
    DictProperty, ListProperty, StringProperty, \
    BooleanProperty, OptionProperty, AliasProperty
from kivy.lang import Builder
from kivy.utils import get_hex_from_color, get_color_from_hex
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage, Image
from kivy.uix.videoplayer import VideoPlayer
from kivy.uix.anchorlayout import AnchorLayout
from kivy.animation import Animation
from kivy.logger import Logger
from docutils.parsers import rst
from docutils.parsers.rst import roles
from docutils import nodes, frontend, utils
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.roles import set_classes


#
# Handle some additional roles
#
if 'KIVY_DOC' not in os.environ:

    class role_doc(nodes.Inline, nodes.TextElement):
        pass

    class role_video(nodes.General, nodes.TextElement):
        pass

    class VideoDirective(Directive):
        has_content = False
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = True
        option_spec = {'width': directives.nonnegative_int,
                       'height': directives.nonnegative_int}

        def run(self):
            set_classes(self.options)
            node = role_video(source=self.arguments[0], **self.options)
            return [node]

    generic_docroles = {
        'doc': role_doc}

    for rolename, nodeclass in generic_docroles.items():
        generic = roles.GenericRole(rolename, nodeclass)
        role = roles.CustomRole(rolename, generic, {'classes': [rolename]})
        roles.register_local_role(rolename, role)

    directives.register_directive('video', VideoDirective)

Builder.load_string('''
#:import parse_color kivy.parser.parse_color



<RstDocument>:
    content: content
    scatter: scatter
    do_scroll_x: False
    canvas.before:
        Color:
            rgba: parse_color(root.colors['background'])
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
    valign: 'top'
    font_size:
        sp(self.document.base_font_size - self.section * (
        self.document.base_font_size / 31.0 * 2))
    size_hint_y: None
    height: self.texture_size[1] + dp(20)
    text_size: self.width, None
    bold: True

    canvas:
        Color:
            rgba: parse_color(self.document.underline_color)
        Rectangle:
            pos: self.x, self.y + 5
            size: self.width, 1


<RstParagraph>:
    markup: True
    valign: 'top'
    size_hint_y: None
    height: self.texture_size[1] + self.my
    text_size: self.width - self.mx, None
    font_size: sp(self.document.base_font_size / 2.0)

<RstTerm>:
    size_hint: None, None
    height: label.height
    anchor_x: 'left'
    Label:
        id: label
        text: root.text
        markup: True
        valign: 'top'
        size_hint: None, None
        size: self.texture_size[0] + dp(10), self.texture_size[1] + dp(10)
        font_size: sp(root.document.base_font_size / 2.0)

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
    height: content.texture_size[1] + dp(20)
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
        valign: 'top'
        text_size: self.width - 20, None
        font_name: 'data/fonts/RobotoMono-Regular.ttf'
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
    size_hint: None, None
    size: self.texture_size[0], self.texture_size[1] + dp(10)

<RstAsyncImage>:
    size_hint: None, None
    size: self.texture_size[0], self.texture_size[1] + dp(10)

<RstDefinitionList>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height
    font_size: sp(self.document.base_font_size / 2.0)

<RstDefinition>:
    cols: 2
    size_hint_y: None
    height: self.minimum_height
    font_size: sp(self.document.base_font_size / 2.0)

<RstFieldList>:
    cols: 2
    size_hint_y: None
    height: self.minimum_height

<RstFieldName>:
    markup: True
    valign: 'top'
    size_hint: 0.2, 1
    color: (0, 0, 0, 1)
    bold: True
    text_size: self.width-10, self.height - 10
    valign: 'top'
    font_size: sp(self.document.base_font_size / 2.0)

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
            points: [\
            self.x,\
            self.y,\
            self.right,\
            self.y,\
            self.right,\
            self.top,\
            self.x,\
            self.top,\
            self.x,\
            self.y]

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
    valign: 'top'
    size_hint_x: None
    width: self.texture_size[0] + dp(10)
    text_size: None, self.height - dp(10)
    font_size: sp(self.document.base_font_size / 2.0)

<RstEmptySpace>:
    size_hint: 0.01, 0.01

<RstDefinitionSpace>:
    size_hint: None, 0.1
    width: 50
    font_size: sp(self.document.base_font_size / 2.0)

<RstVideoPlayer>:
    options: {'allow_stretch': True}
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1)
        BorderImage:
            source: 'atlas://data/images/defaulttheme/player-background'
            pos: self.x - 25, self.y - 25
            size: self.width + 50, self.height + 50
            border: (25, 25, 25, 25)
''')


class RstVideoPlayer(VideoPlayer):
    pass


class RstDocument(ScrollView):
    '''Base widget used to store an Rst document. See module documentation for
    more information.
    '''
    source = StringProperty(None)
    '''Filename of the RST document.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    source_encoding = StringProperty('utf-8')
    '''Encoding to be used for the :attr:`source` file.

    :attr:`source_encoding` is a :class:`~kivy.properties.StringProperty` and
    defaults to `utf-8`.

    .. Note::
        It is your responsibility to ensure that the value provided is a
        valid codec supported by python.
    '''

    source_error = OptionProperty('strict',
                                  options=('strict', 'ignore', 'replace',
                                           'xmlcharrefreplace',
                                           'backslashreplac'))
    '''Error handling to be used while encoding the :attr:`source` file.

    :attr:`source_error` is an :class:`~kivy.properties.OptionProperty` and
    defaults to `strict`. Can be one of 'strict', 'ignore', 'replace',
    'xmlcharrefreplace' or 'backslashreplac'.
    '''

    text = StringProperty(None)
    '''RST markup text of the document.

    :attr:`text` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.
    '''

    document_root = StringProperty(None)
    '''Root path where :doc: will search for rst documents. If no path is
    given, it will use the directory of the first loaded source file.

    :attr:`document_root` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    base_font_size = NumericProperty(31)
    '''Font size for the biggest title, 31 by default. All other font sizes are
    derived from this.

    .. versionadded:: 1.8.0
    '''

    show_errors = BooleanProperty(False)
    '''Indicate whether RST parsers errors should be shown on the screen
    or not.

    :attr:`show_errors` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    def _get_bgc(self):
        return get_color_from_hex(self.colors.background)

    def _set_bgc(self, value):
        self.colors.background = get_hex_from_color(value)[1:]

    background_color = AliasProperty(_get_bgc, _set_bgc, bind=('colors',))
    '''Specifies the background_color to be used for the RstDocument.

    .. versionadded:: 1.8.0

    :attr:`background_color` is an :class:`~kivy.properties.AliasProperty`
    for colors['background'].
    '''

    colors = DictProperty({
        'background': 'e5e6e9ff',
        'link': 'ce5c00ff',
        'paragraph': '202020ff',
        'title': '204a87ff',
        'bullet': '000000ff'})
    '''Dictionary of all the colors used in the RST rendering.

    .. warning::

        This dictionary is needs special handling. You also need to call
        :meth:`RstDocument.render` if you change them after loading.

    :attr:`colors` is a :class:`~kivy.properties.DictProperty`.
    '''

    title = StringProperty('')
    '''Title of the current document.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults to
    ''. It is read-only.
    '''

    toctrees = DictProperty({})
    '''Toctree of all loaded or preloaded documents. This dictionary is filled
    when a rst document is explicitly loaded or where :meth:`preload` has been
    called.

    If the document has no filename, e.g. when the document is loaded from a
    text file, the key will be ''.

    :attr:`toctrees` is a :class:`~kivy.properties.DictProperty` and defaults
    to {}.
    '''

    underline_color = StringProperty('204a9699')
    '''underline color of the titles, expressed in html color notation

    :attr:`underline_color` is a
    :class:`~kivy.properties.StringProperty` and defaults to '204a9699'.

    .. versionadded: 1.9.0
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
            components=(rst.Parser, )).get_default_values()
        super(RstDocument, self).__init__(**kwargs)

    def on_source(self, instance, value):
        if not value:
            return
        if self.document_root is None:
            # set the documentation root to the directory name of the
            # first tile
            self.document_root = abspath(dirname(value))
        self._load_from_source()

    def on_text(self, instance, value):
        self._trigger_load()

    def render(self):
        '''Force document rendering.
        '''
        self._load_from_text()

    def resolve_path(self, filename):
        '''Get the path for this filename. If the filename doesn't exist,
        it returns the document_root + filename.
        '''
        if exists(filename):
            return filename
        return join(self.document_root, filename)

    def preload(self, filename, encoding='utf-8', errors='strict'):
        '''Preload a rst file to get its toctree and its title.

        The result will be stored in :attr:`toctrees` with the ``filename`` as
        key.
        '''

        with open(filename, 'rb') as fd:
            text = fd.read().decode(encoding, errors)
        # parse the source
        document = utils.new_document('Document', self._settings)
        self._parser.parse(text, document)
        # fill the current document node
        visitor = _ToctreeVisitor(document)
        document.walkabout(visitor)
        self.toctrees[filename] = visitor.toctree
        return text

    def _load_from_source(self):
        filename = self.resolve_path(self.source)
        self.text = self.preload(filename,
                                 self.source_encoding,
                                 self.source_error)

    def _load_from_text(self, *largs):
        try:
            # clear the current widgets
            self.content.clear_widgets()
            self.anchors_widgets = []
            self.refs_assoc = {}

            # parse the source
            document = utils.new_document('Document', self._settings)
            text = self.text
            if PY2 and type(text) is str:
                text = text.decode('utf-8')
            self._parser.parse(text, document)

            # fill the current document node
            visitor = _Visitor(self, document)
            document.walkabout(visitor)

            self.title = visitor.title or 'No title'
        except:
            Logger.exception('Rst: error while loading text')

    def on_ref_press(self, node, ref):
        self.goto(ref)

    def goto(self, ref, *largs):
        '''Scroll to the reference. If it's not found, nothing will be done.

        For this text::

            .. _myref:

            This is something I always wanted.

        You can do::

            from kivy.clock import Clock
            from functools import partial

            doc = RstDocument(...)
            Clock.schedule_once(partial(doc.goto, 'myref'), 0.1)

        .. note::

            It is preferable to delay the call of the goto if you just loaded
            the document because the layout might not be finished or the
            size of the RstDocument has not yet been determined. In
            either case, the calculation of the scrolling would be
            wrong.

            You can, however, do a direct call if the document is already
            loaded.

        .. versionadded:: 1.3.0
        '''
        # check if it's a file ?
        if ref.endswith('.rst'):
            # whether it's a valid or invalid file, let source deal with it
            self.source = ref
            return

        # get the association
        ref = self.refs_assoc.get(ref, ref)

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
        # ay += node.y

        # what's the current coordinate for us?
        sx, sy = self.scatter.x, self.scatter.top
        # ax, ay = self.scatter.to_parent(ax, ay)

        ay -= self.height

        dx, dy = self.convert_distance_to_scroll(0, ay)
        dy = max(0, min(1, dy))
        Animation(scroll_y=dy, d=.25, t='in_out_expo').start(self)

    def add_anchors(self, node):
        self.anchors_widgets.append(node)


class RstTitle(Label):

    section = NumericProperty(0)

    document = ObjectProperty(None)


class RstParagraph(Label):

    mx = NumericProperty(10)

    my = NumericProperty(10)

    document = ObjectProperty(None)


class RstTerm(AnchorLayout):

    text = StringProperty('')

    document = ObjectProperty(None)


class RstBlockQuote(GridLayout):
    content = ObjectProperty(None)


class RstLiteralBlock(GridLayout):
    content = ObjectProperty(None)


class RstList(GridLayout):
    pass


class RstListItem(GridLayout):
    content = ObjectProperty(None)


class RstListBullet(Label):

    document = ObjectProperty(None)


class RstSystemMessage(GridLayout):
    pass


class RstWarning(GridLayout):
    content = ObjectProperty(None)


class RstNote(GridLayout):
    content = ObjectProperty(None)


class RstImage(Image):
    pass


class RstAsyncImage(AsyncImage):
    pass


class RstDefinitionList(GridLayout):

    document = ObjectProperty(None)


class RstDefinition(GridLayout):

    document = ObjectProperty(None)


class RstFieldList(GridLayout):
    pass


class RstFieldName(Label):

    document = ObjectProperty(None)


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


class RstDefinitionSpace(Widget):

    document = ObjectProperty(None)


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
        if cls is nodes.document:
            self.push(self.root.content)

        elif cls is nodes.section:
            self.section += 1

        elif cls is nodes.title:
            label = RstTitle(section=self.section, document=self.root)
            self.current.add_widget(label)
            self.push(label)
            # assert(self.text == '')

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
            label = RstParagraph(document=self.root)
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
            self.text += '[font=fonts/RobotoMono-Regular.ttf]'

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
            self.current.add_widget(RstListBullet(
                text=bullet, document=self.root))
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
            uri = node['uri']
            if uri.startswith('/') and self.root.document_root:
                uri = join(self.root.document_root, uri[1:])
            if uri.startswith('http://') or uri.startswith('https://'):
                image = RstAsyncImage(source=uri)
            else:
                image = RstImage(source=uri)

            align = node.get('align', 'center')
            root = AnchorLayout(size_hint_y=None, anchor_x=align,
                                height=image.height)
            image.bind(height=root.setter('height'))
            root.add_widget(image)
            self.current.add_widget(root)

        elif cls is nodes.definition_list:
            lst = RstDefinitionList(document=self.root)
            self.current.add_widget(lst)
            self.push(lst)

        elif cls is nodes.term:
            assert(isinstance(self.current, RstDefinitionList))
            term = RstTerm(document=self.root)
            self.current.add_widget(term)
            self.push(term)

        elif cls is nodes.definition:
            assert(isinstance(self.current, RstDefinitionList))
            definition = RstDefinition(document=self.root)
            definition.add_widget(RstDefinitionSpace(document=self.root))
            self.current.add_widget(definition)
            self.push(definition)

        elif cls is nodes.field_list:
            fieldlist = RstFieldList()
            self.current.add_widget(fieldlist)
            self.push(fieldlist)

        elif cls is nodes.field_name:
            name = RstFieldName(document=self.root)
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
            self.text += '[ref=%s][color=%s]' % (
                name, self.root.colors.get(
                    'link', self.root.colors.get('paragraph')))
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

        elif cls is role_video:
            pass

    def dispatch_departure(self, node):
        cls = node.__class__
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

            # if exist, use the title of the first section found in the
            # document
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

        elif cls is role_video:
            width = node['width'] if 'width' in node.attlist() else 400
            height = node['height'] if 'height' in node.attlist() else 300
            uri = node['source']
            if uri.startswith('/') and self.root.document_root:
                uri = join(self.root.document_root, uri[1:])
            video = RstVideoPlayer(
                source=uri,
                size_hint=(None, None),
                size=(width, height))
            anchor = AnchorLayout(size_hint_y=None, height=height + 20)
            anchor.add_widget(video)
            self.current.add_widget(anchor)

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


if __name__ == '__main__':
    from kivy.base import runTouchApp
    import sys
    runTouchApp(RstDocument(source=sys.argv[1]))
