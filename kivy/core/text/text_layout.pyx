'''
Text layout
============

An internal module for laying out text according to options and constraints.
This is not part of the API and may change at any time.
'''


__all__ = ('layout_text', 'LayoutWord', 'LayoutLine')


cdef inline int max(int a, int b): return b if a <= b else a
cdef inline int min(int a, int b): return a if a <= b else b


cdef class LayoutWord:
    '''Formally describes a word contained in a line. The name word simply
    means a chunk of text and can be used to describe any text.

    A word has some width, height and is rendered according to options saved
    in :attr:`options`. See :class:`LayoutLine` for its usage.

    :Parameters:
        `options`: dict
            the label options dictionary for this word.
        `lw`: int
            the width of the text in pixels.
        `lh`: int
            the height of the text in pixels.
        `text`: string
            the text of the word.
    '''

    def __cinit__(self, dict options, int lw, int lh, object text):
        self.text = text
        self.lw = lw
        self.lh = lh
        self.options = options


cdef class LayoutLine:
    ''' Formally describes a line of text. A line of text is composed of many
    :class:`LayoutWord` instances, each with it's own text, size and options.

    A :class:`LayoutLine` instance does not always imply that the words
    contained in the line ended with a newline. That is only the case if
    :attr:`is_last_line` is True. For example a single real line of text can
    be split across multiple :class:`LayoutLine` instances if the whole line
    doesn't fit in the constrained width.

    :Parameters:
        `x`: int
            the location in a texture from where the left side of this line is
            began drawn.
        `y`: int
            the location in a texture from where the bottom of this line is
            drawn.
        `w`: int
            the width of the line. This is the sum of the individual widths
            of its :class:`LayoutWord` instances. Does not include any padding.
        `h`: int
            the height of the line. This is the maximum of the individual
            heights of its :class:`LayoutWord` instances multiplied by the
            `line_height` of these instance. So this is larger then the word
            height.
        `is_last_line`: bool
            whether this line was the last line in a paragraph. When True, it
            implies that the line was followed by a newline. Newlines should
            not be included in the text of words, but is implicit by setting
            this to True.
        `line_wrap`: bool
            whether this line is continued from a previous line which didn't
            fit into a constrained width and was therefore split across
            multiple :class:`LayoutLine` instances. `line_wrap` can be True
            or False independently of `is_last_line`.
        `words`: python list
            a list that contains only :class:`LayoutWord` instances describing
            the text of the line.

    '''

    def __cinit__(self, int x=0, int y=0, int w=0, int h=0, int is_last_line=0,
                  int line_wrap=0, list words=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_last_line = is_last_line
        self.line_wrap = line_wrap
        if words is None:
            words = []
        self.words = words


cdef inline LayoutLine add_line(object text, int lw, int lh, LayoutLine line,
        list lines, dict options, float line_height, int xpad, int *w, int *h,
        int pos, int strip):
        ''' Adds to the current line the text if lw is not zero. Increases that
        line's w/h by required amount, increases global h/w by required amount
        and returns new empty line.

        pos being -1 indicates we just append line, else, we insert the line at
        index pos in lines. E.g. if we add lines from bottom up.

        This assumes that global h is accurate and includes the text previously
        added to the line.
        '''
        cdef int old_lh = line.h, count = <int>len(lines), add_h
        if lw:
            line.words.append(LayoutWord(options, lw, lh, text))
            line.w += lw

        line.h = max(int(lh * line_height), line.h)
        if count:
            add_h = line.h
        else:
            add_h = max(lh, line.h)
        # if we're appending to existing line don't add height twice
        h[0] = h[0] + add_h - old_lh
        w[0] = max(w[0], line.w + 2 * xpad)
        if strip:
            final_strip(line)
        if pos == -1:
            lines.append(line)
        else:
            lines.insert(pos, line)
        return LayoutLine()


cdef inline void final_strip(LayoutLine line):
    ''' Ensures that the line does not end with trailing spaces.

    Given the line, it'll start from the last word and strip from the
    right. If the word becomes empty, it'll remove it and strip the word
    previous to that and so on.
    '''
    cdef int diff
    cdef LayoutWord last_word
    cdef object stripped

    # XXX: here we strip any trailing spaces reducing the width of the line
    # however, the height is not reduced, even if the part that might be larger
    # is removed, potentially reducing the height of the line. It is not likely
    # a issue, but can be 'fixed' at the cost of re-computing line height

    while (len(line.words) and (line.words[-1].text.endswith(' ') or
                                line.words[-1].text == '')):
        last_word = line.words.pop()

        if last_word.text == '':  # empty str, pop it
            line.w -= last_word.lw  # likely 0
            continue

        stripped = last_word.text.rstrip()  # ends with space
        # subtract ending space length
        diff = ((<int>len(last_word.text) - <int>len(stripped)) *
                last_word.options['space_width'])
        line.w = max(0, line.w - diff)  # line w
        line.words.append(LayoutWord(   # re-add last word
        last_word.options, max(0, last_word.lw - diff),
        last_word.lh, stripped))


cdef inline layout_text_unrestricted(object text, list lines, int w, int h,
    int uh, dict options, object get_extents, int dwn, int complete,
    int xpad, int max_lines, float line_height, int strip):
    ''' Layout when the width is unrestricted; text_size[0] is None.
    It's a bit faster.
    '''

    cdef list new_lines
    cdef int s, lw, lh, old_lh, i = -1, n
    cdef int lhh, k, pos, add_h
    cdef object line, val = False, indices
    cdef LayoutLine _line

    new_lines = text.split('\n')
    n = <int>len(new_lines)
    s = 0
    k = n
    pos = <int>len(lines)  # always include first line, start w/ no lines added
    # there's a last line to which first (last) new line must be appended
    if pos:
        if dwn:  # append to last line
            _line = lines[-1]
            line = new_lines[0]
            s = 1
        else:  # append to first line
            _line = lines[0]
            line = new_lines[-1]
            k = n - 1
        if strip:
            if not _line.w:  # no proceeding text: strip leading
                line = line.lstrip()
            # ends this line so right strip
            if complete or (dwn and n > 1 or not dwn and pos > 1):
                line = line.rstrip()
        lw, lh = get_extents(line)

        old_lh = _line.h
        if lw:  # when adding to existing line, don't check uh
            _line.words.append(LayoutWord(options, lw, lh, line))
            _line.w += lw
            _line.h = max(int(lh * line_height), _line.h)
            if pos == 1:  # still first line
                add_h = max(lh, _line.h)
            else:
                add_h = _line.h
        elif strip and (complete or (dwn and n > 1 or not dwn and pos > 1)):
            # if we finish this line, make sure it doesn't end in spaces
            final_strip(_line)
            add_h = _line.h
        else:
            add_h = _line.h

        w = max(w, _line.w + 2 * xpad)
        h += add_h - old_lh

    # now do the remaining lines
    indices = range(s, k) if dwn else reversed(range(s, k))
    for i in indices:
        # always compute first line, even if it won't be displayed
        if (max_lines > 0 and pos + 1 > max_lines or pos and
            uh != -1 and h > uh):
            i += -1 if dwn else 1
            break
        line = new_lines[i]
        # the last line is only stripped from left
        if strip:
            if complete or (dwn and i < n - 1 or not dwn and i > s):
                line = line.strip()
            else:
                line = line.lstrip()
        lw, lh = get_extents(line)

        lhh = int(lh * line_height)
        if pos:
            add_h = lhh
        else:  # for the first line, always use full height
            add_h = lh
        if uh != -1 and h + add_h > uh and pos:  # too high
            i += -1 if dwn else 1
            break

        pos += 1
        w = max(w, int(lw + 2 * xpad))
        h += add_h
        if lw:
            _line = LayoutLine(0, 0, lw, lhh, 1, 0, [LayoutWord(options, lw,
                                                                lh, line)])
        else:
            _line = LayoutLine(0, 0, 0, lhh, 1, 0, [])
        new_lines[i] = _line

    if s != k:
        if dwn:
            lines.extend(new_lines[s:i + 1])
            val = i != k - 1
        else:
            if k != i:
                lines.extend([None, ] * (k - i))
                lines[(k - i):] = lines[:len(lines) - (k - i)]
                lines[:(k - i)] = new_lines[i:k]
            val = i != 0

    return w, h, val


def layout_text(object text, list lines, tuple size, tuple text_size,
                dict options, object get_extents, int append_down,
                int complete):
    ''' Lays out text into a series of :class:`LayoutWord` and
    :class:`LayoutLine` instances according to the options specified.

    The function is designed to be called many times, each time new text is
    appended to the last line (or first line if appending upwards), unless a
    newline is present in the text. Each text appended is described by its own
    options which can change between successive calls. If the text is
    constrained, we stop as soon as the constraint is reached.

    :Parameters:
        `text`: string or bytes
            the text to be broken down into lines. If lines is not empty,
            the text is added to the last line (or first line if `append_down`
            is False) until a newline is reached which creates a new line in
            `lines`. See :class:`LayoutLine`.
        `lines`: list
            a list of :class:`LayoutLine` instances, each describing a line of
            the text. Calls to :func:`layout_text` append or create
            new :class:`LayoutLine` instances in `lines`.
        `size`: 2-tuple of ints
            the size of the laid out text so far. Upon first call it should
            probably be (0, 0), afterwards it should be the (w, h) returned
            by this function in a previous call. When size reaches the
            constraining size, `text_size`, we stop adding lines and return
            True for the clipped parameter. size includes the x and y padding.
        `text_size`: 2-tuple of ints or None.
            the size constraint on the laid out text. If either element is
            None, the text is not constrained in that dimension. For example,
            (None, 200) will constrain the height, including padding to 200,
            while the width is unconstrained. The first line, and the first
            character of a line is always returned, even if it exceeds the
            constraint. The value be changed between different calls.
        `options`: dict
            the label options of this `text`. The options are saved with each
            word allowing different words to have different options from
            successive calls.

            Note, `options` must include a `space_width` key with a value
            indicating the width of a space for that set of options.
        `get_extents`: callable
            a function called with a string, which returns a tuple containing
            the width, height of the string.
        `append_down`: bool
            Whether successive calls to the function appends lines before or
            after the existing lines. If True, they are appended to the last
            line and below it. If False, it's appended at the first line and
            above. For example, if False, everything after the last
            newline in `text` is appended to the first line in lines.
            Everything before the last newline is inserted at the start of
            lines in same order as text; that is we do not invert the line
            order.

            This allows laying out from top to bottom until the constrained is
            reached, or from bottom to top until the constrained is reached.
        `complete`: bool
            whether this text complete lines. It use is that normally is
            strip in `options` is True, all leading and trailing spaces
            are removed from each line except from the last line (or first
            line if `append_down` is False) which only removes leading spaces.
            That's because further text can still be appended to the last line
            so we cannot strip them. If `complete` is True, it indicates no
            further text is coming and all lines will be stripped.

            The function can also be called with `text` set to the empty string
            and `complete` set to True in order for the last (first) line to
            be stripped.

    :returns:
        3-tuple, (w, h, clipped).
        w and h is the width and height of the text in lines so far and
        includes padding. This can be larger than `text_size`, e.g. if not even
        a single fitted, the first line would still be returned.
        `clipped` is True if not all the text has been added to lines because
        w, h reached the constrained size.

    Following is a simple example with no padding and no stripping::

        >>> from kivy.core.text import Label
        >>> from kivy.core.text.text_layout import layout_text

        >>> l = Label()
        >>> lines = []
        >>> # layout text with width constraint by 50, but no height constraint
        >>> w, h, clipped = layout_text('heres some text\\nah, another line',
        ... lines, (0, 0), (50, None), l.options, l.get_cached_extents(), True,
        ... False)
        >>> w, h, clipped
        (46, 90, False)
        # now add text from bottom up, and constrain width only be 100
        >>> w, h, clipped = layout_text('\\nyay, more text\\n', lines, (w, h),
        ... (100, None), l.options, l.get_cached_extents(), False, True)
        >>> w, h, clipped
        (77, 120, 0)
        >>> for line in lines:
        ...     print('line w: {}, line h: {}'.format(line.w, line.h))
        ...     for word in line.words:
        ...         print('w: {}, h: {}, text: {}'.format(word.lw, word.lh,
        ...         [word.text]))
        line w: 0, line h: 15
        line w: 77, line h: 15
        w: 77, h: 15, text: ['yay, more text']
        line w: 31, line h: 15
        w: 31, h: 15, text: ['heres']
        line w: 34, line h: 15
        w: 34, h: 15, text: [' some']
        line w: 24, line h: 15
        w: 24, h: 15, text: [' text']
        line w: 17, line h: 15
        w: 17, h: 15, text: ['ah,']
        line w: 46, line h: 15
        w: 46, h: 15, text: [' another']
        line w: 23, line h: 15
        w: 23, h: 15, text: [' line']
    '''

    cdef int uw, uh,  _do_last_line, lwe, lhe, ends_line, is_last_line
    cdef int xpad = options['padding_x'], ypad = options['padding_y']
    cdef int max_lines = int(options.get('max_lines', 0))
    cdef float line_height = options['line_height']
    cdef int strip = options['strip'] or options['halign'] == 'justify'
    cdef int ref_strip = options['strip_reflow']
    cdef int w = size[0], h = size[1]  # width and height of the texture so far
    cdef list new_lines
    cdef int s, lw = -1, lh = -1, old_lh, i = -1, n, m, e
    cdef int lhh, lww, k, bare_h, dwn = append_down, pos = 0
    cdef object line, ln, val, indices
    cdef LayoutLine _line
    cdef int is_space = 0
    uw = text_size[0] if text_size[0] is not None else -1
    uh = text_size[1] if text_size[1] is not None else -1

    if not h:
        h = ypad * 2

    if uw == -1:  # no width specified
        return layout_text_unrestricted(text, lines, w, h, uh, options,
        get_extents, dwn, complete, xpad, max_lines, line_height, strip)


    new_lines = text.split('\n')
    n = <int>len(new_lines)
    uw = max(0, uw - xpad * 2)  # actual w, h allowed for rendering
    _, bare_h = get_extents('')
    if dwn:
        pos = -1  # don't use pos when going down b/c we append at end of lines

    # split into lines and find how many line wraps each line requires
    indices = range(n) if dwn else reversed(range(n))
    for i in indices:
        k = <int>len(lines)
        if (max_lines > 0 and k > max_lines or uh != -1 and
            h > uh and k > 1):
            break

        is_last_line = not (dwn and i < n - 1 or not dwn and i)
        # whether this line is ended, or if we may append to it later
        ends_line = complete or not is_last_line
        if not dwn:  # new line will be appended at top, unless changed below
            pos = 0
        # for the first (last if not down) new line, append it to previous line
        if (i and dwn or not dwn and i != n - 1) or not k:  # interior line
            _line = LayoutLine()
        else:
            if dwn:  # take last line
                _line = lines.pop()
            else:  # need to append right before 1st line ends in case of wrap
                while pos + 1 < k and not lines[pos + 1].line_wrap:
                    pos += 1
                _line = lines.pop(pos)

        line = new_lines[i]
        # there's no proceeding text, so strip leading
        if not _line.w and (strip or ref_strip and _line.line_wrap):
            line = line.lstrip()
        if strip and ends_line:
            line = line.rstrip()

        k = <int>len(line)
        if not k:  # just add empty line if empty
            _line.is_last_line = ends_line  # nothing will be appended
            # ensure we don't leave trailing from before
            _line = add_line('', 0, bare_h, _line, lines, options, line_height,
                             xpad, &w, &h, pos, _line.w and ends_line)
            continue

        '''----------------- we now a non-empty line ------------------------
        what we do is given the current text in this real line if we can fit
        another word, add it. Otherwise add it to a new line. But if a single
        word doesn't fit on a single line, just split the word itself into
        multiple lines'''

        # s is idx in line of start of this actual line, e is idx of
        # next space, m is idx after s that still fits on this line
        s = m = e = 0
        while s != k:
            # find next space or end, if end don't keep checking
            if e != k:
                # leading spaces
                if s == m and not _line.w and line[s] == ' ' and (strip or ref_strip and _line.line_wrap):
                    s = m = s + 1
                    # trailing spaces were stripped, so end is always not space
                    continue

                # when not stripping, if we found a space last, don't jump to
                # the next space, but instead move pos to after this space, to
                # allow fitting this space on the current line
                if strip or not is_space:
                    e = line.find(' ', m + 1)
                    is_space = 1
                else:
                    e = m + 1
                    is_space = 0
                if e is -1:
                    e = k

            lwe, lhe = get_extents(line[s:e])  # does next word fit?
            if lwe + _line.w > uw:  # too wide
                ln = ''
                lww, lhh = 0, bare_h
                _do_last_line = 0
                # if there's already some text, commit and go next line
                if s != m:
                    _do_last_line = 1
                    if (strip or ref_strip) and line[m - 1] == ' ':
                        ln = line[s:m].rstrip()
                        lww, lhh = get_extents(ln)
                    else:
                        ln = line[s:m]
                        lww, lhh = lw, lh
                    s = m
                elif _line.w:
                    _do_last_line = 1

                if _do_last_line:
                    # if there's proceeding text and ln is '': strip trailing
                    _line = add_line(ln, lww, lhh, _line, lines, options,
                        line_height, xpad, &w, &h, pos, _line.w and not lww)
                    _line.line_wrap = 1
                    if not dwn:
                        pos += 1

                # try to fit word on new line, if it doesn't fit we'll
                # have to break the word into as many lines needed
                if strip or ref_strip and _line.line_wrap:
                    s = e - <int>len(line[s:e].lstrip())
                if s == e:  # if it was only a stripped space, move on
                    m = s
                    continue

                # now break single word into as many lines needed
                m = s
                while s != e:
                    # does remainder fit in single line?
                    lwe, lhe = get_extents(line[s:e])
                    if lwe + _line.w <= uw:
                        m = e
                        break
                    # if not, fit as much as possible into this line
                    while (m != e and
                           get_extents(line[s:m + 1])[0] + _line.w <= uw):
                        m += 1
                    # not enough room for even single char, skip it
                    if m == s:
                        m += 1
                    _line.is_last_line = m == k  # is last line?
                    lww, lhh = get_extents(line[s:m])
                    _line = add_line(line[s:m], lww, lhh, _line, lines,
                        options, line_height, xpad, &w, &h, pos, 0)
                    _line.line_wrap = 1
                    if not dwn:
                        pos += 1
                    s = m
                m = s  # done with long word, go back to normal

            else:   # the word fits
                # don't allow leading spaces on empty lines
                #if strip and m == s and line[s:e] == ' ' and not _line.w:
                if (strip or ref_strip and _line.line_wrap) and line[s:e] == ' ' and not _line.w:
                    s = m = e
                    continue
                m = e

            if m == k:  # we're done
                if s != k or _line.w:
                    _line.is_last_line = ends_line  # line end
                    _line = add_line(line[s:], lwe, lhe, _line, lines, options,
                                     line_height, xpad, &w, &h, pos, 0)
                break
            lw, lh = lwe, lhe  # save current lw/lh, then fit more in line

    val = dwn and i != n - 1 or not dwn and i
    # ensure the number of lines is not more than the user asked
    # above, we might have gone a few lines over
    if max_lines > 0 and len(lines) > max_lines:
        val = True
        if dwn:
            h-= sum(l.h for l in lines[max_lines:])
            del lines[max_lines:]
        else:
            h-= sum(l.h for l in lines[:max(0, <int>len(lines) - max_lines)])
            del lines[:max(0, <int>len(lines) - max_lines)]

    # now make sure we don't have lines outside specified height
    k = <int>len(lines)
    if k > 1 and uh != -1 and h > uh:
        val = True
        if dwn:  # remove from last line going up
            i = k -1  # will removing the ith line make it fit?
            while i > 0 and h > uh:
                h -= lines[i].h
                i -= 1
            del lines[i + 1:]  # we stopped when keeping the ith line still fits
        else:  # remove from first line going down
            i = 0  # will removing the ith line make it fit?
            while i < k - 1 and h > uh:
                h -= lines[i].h
                i += 1
            del lines[:i]

    return w, h, val
