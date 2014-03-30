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

    def __cinit__(self, int x, int y, int w, int h, int is_last_line,
                  list words):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_last_line = is_last_line
        self.words = words


cdef inline LayoutLine add_line(text, int lw, int lh, LayoutLine _line,
                                list lines, dict options, int line_height,
                                int *w, int *h, int *iw, int *ih):
        ''' Adds to the current _line the text, increases that line's w/h
        by required amount, increases global h by required amount and
        returns new empty line and global w, h.
        '''
        _line.words.append(LayoutWord(options, lw, lh, text))
        _line.h = max(int(lh * line_height), ih[0])
        _line.w += lw
        # if we're appending to existing line, ih is last line height
        h[0] = h[0] + _line.h - ih[0]
        ih[0] = iw[0] = 0  # after first new line, it's always zero
        w[0] = max(w[0], _line.w)
        lines.append(_line)
        return LayoutLine(0, 0, 0, 0, False, [])

def layout_text(object text, list lines, tuple size, dict options,
                      object get_extents, pos_cache=None):
    '''if start of line and space, if trip it's removed
    the last line, unless it ends with a new line won't be stripped on
    right
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
    '''

    cdef int uw, uh
    cdef int xpad = options['padding_x'], ypad = options['padding_y']
    cdef int max_lines = int(options.get('max_lines', 0))
    cdef int line_height = options['line_height']
    cdef int strip = options['strip'] or options['halign'][-1] == 'y'
    cdef int w = size[0], h = size[1]  # width and height of the texture so far
    cdef list new_lines
    cdef int s, lw, lh, old_lh, i, n, ih, iw, m, e, lwe, lhe, _do_last_line
    cdef int diff, lhh, lww, k, bare_w, bare_h
    cdef object line, ln, stripped, val
    cdef LayoutLine _line
    cdef LayoutWord last_word
    val = options['text_size']
    uw = val[0] if val[0] is not None else -1
    uh = val[1] if val[1] is not None else -1
    if not text:
        return size

    if not h:
        h = ypad * 2
    new_lines = text.split('\n')
    n = len(new_lines)

    # no width specified, find max width. For height, if not specified,
    # do everything, otherwise stop when reached specified height
    if uw == -1:
        s = 0
        # there's a last line to which the first new line must be appended
        if lines:
            s = 1
            _line = lines[-1]
            val = new_lines[0]
            if strip:
                if not _line.w:  # prev width is zero, strip leading
                    val = val.lstrip()
                if n > 1:  # ends this line so right strip
                    val = val.rstrip()
            lw, lh = get_extents(val)

            # when adding to existing line, don't check uh
            _line.words.append(LayoutWord(options, lw, lh, val))
            old_lh = _line.h
            _line.w += lw
            _line.h = max(int(lh * line_height), _line.h)
            w = max(w, _line.w)
            h += _line.h - old_lh

        # now do the remaining lines
        for i in range(s, n):
            k = len(lines)
            # always compute first line, even if it won't be displayed
            if (max_lines > 0 and k + i + 1 - s > max_lines or
                uh != -1 and h > uh and i):
                i -= 1
                break
            line = new_lines[i]
            # the last line is only stripped from left
            if strip:
                if i < n - 1:
                    line = line.strip()
                else:
                    line = line.lstrip()
            lw, lh = get_extents(line)
            lhh = int(lh * line_height)
            if uh != -1 and h + lhh > uh and i:  # too high
                i -= 1
                break
            w = max(w, int(lw + 2 * xpad))
            h += lhh
            new_lines[i] = LayoutLine(0, 0, lw, lhh, True,
                            [LayoutWord(options, lw, lh, line)])
        lines.extend(new_lines[s:i + 1])
        return w, h

    # constraint width ############################################
    uw = max(0, uw - xpad * 2)  # actual w, h allowed for rendering
    bare_w, bare_h = get_extents('')

    # split into lines and find how many real lines each line requires
    for i in range(n):
        k = len(lines)
        if (max_lines > 0 and k > max_lines or uh != -1 and
            h > uh and k > 1):
            break

        # for the first new line, we have to append to last passed in line
        if i or not k:
            _line = LayoutLine(0, 0, 0, 0, False, [])
        else:
            _line = lines.pop()
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
                             options, line_height, &w, &h, &iw, &ih)
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
                                options, line_height, &w, &h, &iw, &ih)
                        else:
                            _do_last_line = iw
                    else:
                        _line = add_line(line[s:m], lw, lh, _line,
                        lines, options, line_height, &w, &h, &iw, &ih)
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
                    lines.append(_line)
                    h += _line.h - ih
                    w = max(w, _line.w)
                    iw = ih = 0
                    _line = LayoutLine(0, 0, 0, 0, False, [])

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
                            options, line_height, &w, &h, &iw, &ih)
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
                                     line_height, &w, &h, &iw, &ih)
                break
            lw, lh = lwe, lhe  # save current lw/lh, then fit more in line

    # ensure the number of lines is not more than the user asked
    # above, we might have gone a few lines over
    if max_lines > 0:
        del lines[max_lines:]
    # now make sure we don't have lines outside specified height
    k = len(lines)
    if uh != -1 and h > uh:
        h, i = ypad * 2, 0
        while i < k and h + lines[i].h <= uh:
            h += lines[i].h
            i += 1
        del lines[max(1, i):]

    w += xpad * 2
    return w, h
