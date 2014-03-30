'''
layout text
============
'''


__all__ = ('layout_text', 'LayoutWord', 'LayoutLine')


cdef inline int max(int a, int b): return b if a <= b else a
cdef inline int min(int a, int b): return a if a <= b else b


cdef class LayoutWord:

    def __cinit__(self, dict options, int lw, int lh, object text):
        self.text = text
        self.lw = lw
        self.lh = lh
        self.options = options


cdef class LayoutLine:

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


cdef inline LayoutLine add_line(text, int lw, int lh, LayoutLine _line,
                                list lines, dict options, int line_height,
                                int xpad, int *w, int *h, int *iw, int *ih,
                                int pos):
        ''' Adds to the current _line the text, increases that line's w/h
        by required amount, increases global h by required amount and
        returns new empty line and global w, h.
        '''
        if len(text):
            _line.words.append(LayoutWord(options, lw, lh, text))
        _line.h = max(int(lh * line_height), ih[0])
        _line.w += lw
        # if we're appending to existing line, ih is last line height
        h[0] = h[0] + _line.h - ih[0]
        ih[0] = iw[0] = 0  # after first new line, it's always zero
        w[0] = max(w[0], _line.w + 2 * xpad)
        if pos == -1:
            lines.append(_line)
        else:
            lines.insert(pos, _line)
        return LayoutLine()

def layout_text(object text, list lines, tuple size, tuple text_size,
                dict options, object get_extents, int append_down):
    '''if start of line and space, if trip it's removed
    the last line, unless it ends with a new line won't be stripped on
    right. same if not append_down and line starts with
    lines is list of LayoutLine object; [LayoutLine1, LayoutLine2, ...].
    Each line:
    note that lh is the actual height of the line, while height is the
    height of the line including multiplied by 'line_height'.

    options must contain 'space_width'. This is in case we have to walk
    back to prev lines with different options.

    size, takes the previous size and increments by the text added
    height be larger than text_size, or smaller. width is always <=.
    size includes padding

    Note, this is not part of the external API and may change in the
    future.

    when append_down is False, the added text is appended before the exiting
    layout processed lines. In addition, the last line of the new lines
    is appended to the first line of processed lines.
    '''

    cdef int uw, uh
    cdef int xpad = options['padding_x'], ypad = options['padding_y']
    cdef int max_lines = int(options.get('max_lines', 0))
    cdef int line_height = options['line_height']
    cdef int strip = options['strip'] or options['halign'][-1] == 'y'
    cdef int w = size[0], h = size[1]  # width and height of the texture so far
    cdef list new_lines
    cdef int s, lw, lh, old_lh, i, n, ih, iw, m, e, lwe, lhe, _do_last_line
    cdef int diff, lhh, lww, k, bare_w, bare_h, dwn = append_down, pos = 0
    cdef object line, ln, stripped, val, indices
    cdef LayoutLine _line
    cdef LayoutWord last_word
    uw = text_size[0] if text_size[0] is not None else -1
    uh = text_size[1] if text_size[1] is not None else -1
    if not text:
        return size[0], size[1], False

    if not h:
        h = ypad * 2
    new_lines = text.split('\n')
    n = len(new_lines)

    # no width specified, find max width. For height, if not specified,
    # do everything, otherwise stop when reached specified height
    if uw == -1:
        s = 0
        k = n
        pos = len(lines)  # always include first line, start w/ no lines added
        # there's a last line to which first (last) new line must be appended
        if pos:
            if dwn:
                _line = lines[-1]
                val = new_lines[0]
                s = 1
            else:
                _line = lines[0]
                val = new_lines[-1]
                k = n - 1
            if strip:
                if not _line.w:  # prev width is zero, strip leading
                    val = val.lstrip()
                # ends this line so right strip
                if dwn and n > 1 or not dwn and pos > 1:
                    val = val.rstrip()
            lw, lh = get_extents(val)

            # when adding to existing line, don't check uh
            if len(val):
                _line.words.append(LayoutWord(options, lw, lh, val))
            old_lh = _line.h
            _line.w += lw
            _line.h = max(int(lh * line_height), _line.h)
            w = max(w, _line.w + 2 * xpad)
            h += _line.h - old_lh

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
                if dwn and i < n - 1 or not dwn and i > s:
                    line = line.strip()
                else:
                    line = line.lstrip()
            lw, lh = get_extents(line)
            lhh = int(lh * line_height)
            if uh != -1 and h + lhh > uh and pos:  # too high
                i += -1 if dwn else 1
                break
            pos += 1
            w = max(w, int(lw + 2 * xpad))
            h += lhh
            new_lines[i] = LayoutLine(0, 0, lw, lhh, 1, 0,
                            [LayoutWord(options, lw, lh, line)])

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

    # constraint width ############################################
    uw = max(0, uw - xpad * 2)  # actual w, h allowed for rendering
    bare_w, bare_h = get_extents('')
    if dwn:
        pos = -1  # don't use pos when going down b/c we append at end of lines

    # split into lines and find how many line wraps each line requires
    indices = range(n) if dwn else reversed(range(n))
    for i in indices:
        k = len(lines)
        if (max_lines > 0 and k > max_lines or uh != -1 and
            h > uh and k > 1):
            break

        if not dwn:  # new line will be appended at top, unless changed below
            pos = 0
        # for the first (last if not down) new line, append it to previous line
        if (i and dwn or not dwn and i != n - 1) or not k:
            _line = LayoutLine()
        else:
            if dwn:  # take last line
                _line = lines.pop()
            else:  # we need to append right before 1st line ends
                while pos + 1 < k and not lines[pos + 1].line_wrap:
                    pos += 1
                _line = lines.pop(pos)

        iw, ih = _line.w, _line.h  # initial size of line in case we appending
        line = new_lines[i]
        if strip:
            if i:
                line = line.lstrip()
            if i < n - 1:
                line = line.rstrip()
        k = len(line)
        if not k:  # just add empty line if empty
            _line.is_last_line = True
            _line = add_line('', bare_w, bare_h, _line, lines,
                             options, line_height, xpad, &w, &h, &iw, &ih, pos)
            continue

        # what we do is given the current text in this real line
        # (starts empty), if we can fit another word, add it. Otherwise
        # add it to a new line. But if a single word doen't fit on a
        # single line, just split the word itself into multiple lines

        # s is idx in line of start of this actual line, e is idx of
        # next space, m is idx after s that still fits on this line
        s = m = e = 0
        while s != k:
            # find next space or end, if end don't keep checking
            if e != k:
                e = line.find(' ', m + 1)
                if e is -1:
                    e = k

            lwe, lhe = get_extents(line[s:e])  # does next word fit?
            if lwe + iw > uw:  # too wide
                _do_last_line = 0
                if s != m:
                    # theres already some text, commit and go next line
                    # make sure there are no trailing spaces on prev line,
                    # may occur if spaces is followed by word not fitting
                    ln = line[s:m]
                    if strip and ln[-1] == ' ':
                        ln = ln.rstrip()
                        if ln:
                            lww, lhh = get_extents(ln)
                            _line = add_line(ln, lww, lhh, _line, lines,
                                options, line_height, xpad, &w, &h, &iw, &ih,
                                pos)
                            _line.line_wrap = 1
                            if not dwn:
                                pos += 1
                        else:
                            _do_last_line = iw
                    else:
                        _line = add_line(line[s:m], lw, lh, _line, lines,
                        options, line_height, xpad, &w, &h, &iw, &ih, pos)
                        _line.line_wrap = 1
                        if not dwn:
                            pos += 1
                    s = m
                elif iw:
                    _do_last_line = 1

                if _do_last_line:
                    ''' still need to check if the line ended in spaces
                    from before (e.g. line was broken with diff opts, some
                    ending in spaces) so walk back the words of this line
                    until it doesn't end in space. Still, nothing else can
                    be appended to this line anymore.
                    '''
                    while (_line.words and (_line.words[-1].text.endswith(' ')
                           or _line.words[-1].text == '')):
                        last_word = _line.words.pop()

                        if last_word.text == '':  # empty str, pop it
                            _line.w -= last_word.lw  # likely 0
                            continue

                        stripped = last_word.text.rstrip()  # ends with space
                        # subtract ending space length
                        diff = ((len(last_word.text) - len(stripped)) *
                                last_word.options['space_width'])
                        _line.w = max(0, _line.w - diff)  # line w
                        _line.words.append(LayoutWord(   # re-add last word
                        last_word.options, max(0, last_word.w - diff),
                        last_word.h, stripped))
                    # now add the line to lines
                    if dwn:
                        lines.append(_line)
                    else:
                        lines.insert(pos, _line)
                        pos += 1
                    h += _line.h - ih
                    w = max(w, _line.w + 2 * xpad)
                    iw = ih = 0
                    _line = LayoutLine()
                    _line.line_wrap = 1

                # try to fit word on new line, if it doesn't fit we'll
                # have to break the word into as many lines needed
                if strip:
                    s = e - len(line[s:e].lstrip())
                if s == e:  # if it was only a stripped space, move on
                    m = s
                    continue

                # now break single word into as many lines needed
                m = s
                while s != e:
                    # does remainder fit in single line?
                    lwe, lhe = get_extents(line[s:e])
                    if lwe + iw <= uw:
                        m = e
                        break
                    # if not, fit as much as possible into this line
                    while (m != e and
                           get_extents(line[s:m + 1])[0] + iw <= uw):
                        m += 1
                    # not enough room for even single char, skip it
                    if m == s:
                        s += 1
                    else:
                        _line.is_last_line = m == k  # is last line?
                        lww, lhh = get_extents(line[s:m])
                        _line = add_line(line[s:m], lww, lhh, _line, lines,
                            options, line_height, xpad, &w, &h, &iw, &ih, pos)
                        _line.line_wrap = 1
                        if not dwn:
                            pos += 1
                        s = m
                    m = s
                m = s  # done with long word, go back to normal

            else:   # the word fits
                # don't allow leading spaces on empty lines
                if strip and m == s and line[s:e] == ' ' and not iw:
                    s = m = e
                    continue
                m = e

            if m == k:  # we're done
                if s != k:
                    _line.is_last_line = True  # line end
                    _line = add_line(line[s:], lwe, lhe, _line, lines, options,
                                     line_height, xpad, &w, &h, &iw, &ih, pos)
                break
            lw, lh = lwe, lhe  # save current lw/lh, then fit more in line

    val = dwn and i != n - 1 or not dwn and i
    # ensure the number of lines is not more than the user asked
    # above, we might have gone a few lines over
    if max_lines > 0 and len(lines) > max_lines:
        val = True
        if dwn:
            del lines[max_lines:]
        else:
            del lines[:max(0, len(lines) - max_lines)]
    # now make sure we don't have lines outside specified height
    k = len(lines)
    if k > 1 and uh != -1 and h > uh:
        val = True
        if dwn:
            h = ypad * 2 + lines[0].h
            i = 1  # ith line may not fit anymore, 0:i lines do fit
            while i < k and h + lines[i].h <= uh:
                h += lines[i].h
                i += 1
            del lines[i:]
        else:
            h = ypad * 2 + lines[-1].h
            i = k - 2  # ith line may not fit anymore, i+1:end lines do fit
            while i >= 0 and h + lines[i].h <= uh:
                h += lines[i].h
                i -= 1
            del lines[:i + 1]

    return w, h, val
