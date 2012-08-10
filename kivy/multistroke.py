'''
Multistroke gesture recognition
===============================

.. versionadded::
    1.3.0

.. warning::
    This module is highly experimental - use with care.

"The $N Multistroke Recognizer" by Lisa Anthony and Jacob O. Wobbrock
  http://depts.washington.edu/aimgroup/proj/dollar/ndollar.html

"Protractor: A fast and accurate gesture recognizer" by Yang Li
  http://yangl.org/pdf/protractor-chi2010.pdf

Conceptual Overview
-------------------

:class:`Recognizer` is the search/database API similar to GestureDatabase.
It maintains a set of Multistroke objects and searches for user input among
them (technically, it matches Template objects in `Multistroke.templates`)

:class:`GestureSearch` tracks the result of a `Recgonizer.recognize` call. It
can be used to interact with the running recognizer task, for example forcing
it to stop or getting the results so far.

:class:`Multistroke` represents a gesture template in the database. When you
instantiate it, you provide a list of stroke paths that are used to generate
the `templates` collection of unistroke permutations, see below.

:class:`Template` represents a unistroke path. It's (typically) instantiated
by Multistroke during template generation, and not by the programmer directly.

:class:`Candidate` represents a set of strokes as a candidate (user input).
It precomputes the data required for matching against a Template (with both
algorithms).

Fake multistroke recognition
----------------------------

Both $1 (on which $N is built) and Protractor are unistroke recognizers. The
big improvement is that $N automatically generates unistroke permutations from
a given multistroke gesture inputted by the developer/user/template designer
instead of having to input every possible stroke order. For example, with
an N, you would need::

    | -> | | -> |\|
    | ->  \| -> |\|
    \ -> |\  -> |\| (etc)

All possible unistroke permutations are generated from the input strokes.
Make sure you read this for info about the limitations of this approach::

    http://depts.washington.edu/aimgroup/proj/dollar/limits/index.html

With correct template design it's still possible to obtain good results for
many gestures. You can delete unwanted permutations after they are generated,
and then export the gesture to storage for later use. This will not affect
how the Candidate is combined, but it does reduce the risk of an incorrect
match.

Algorithm scoring
-----------------

The $1 algorithm returns a normalized score from 0-1, where 1 is a perfect
match. This is not the case with Protractor, it returns a score that is
1.0/distance. This can lead to very high scores (perfect match is 1/.0001**2)

It should be possible to normalize the score from Protractor, but I have
not researched the details. One possible approach (that I have not tried)::

    def score_hack(dist):
        return dist / math.pi

Lazy data preparation
---------------------

This feature allows you to mix and match templates with different path lengths
and evaluate them against one candidate that is also lazily prepared (equal
path length for template/candidate is a prerequisite for both algorithms).

Lazy preparation is driven by the `Template.numpoints` setting, which is
normally copied from `Multistroke.numpoints`. You can add Multistroke objects
with any .numpoints setting to the Recognizer, and at match time, both the
candidate and template vectors are generated when needed.

This feature is useful for prototyping and template design applications, but
in general you should keep all your templates at the same NUMPOINTS (or on
very few variations) suitable to the algorithm(s) used.

n=16 is optimal for Protractor (default)
n=96 is optimal for $1

Usage example
-------------
You can bind to events on the :class:`Recognizer` instance to track all calls
to recognize(). `res.status` in the callback can be used to determine if the
search was completed, stopped by the user etc::

    from kivy.multistroke import Recognizer, Vector

    gdb = Recognizer()

    # Setup some callback functions to show the output
    def search_start(gdb, res):
        print "A search is starting with %d tasks" % (res.tasks)

    def search_stop(gdb, res):
        # This will call max() on the result dictonary, so it's best to store
        # it instead of calling it 3 times consecutively
        best = res.best
        print "Search ended (%s). Best is %s (score %f, distance %f)" % (
            res.status, best['name'], best['score'], best['dist'] )

    # Now bind callbacks to track all search operations:
    gdb.bind(on_search_start=search_start)
    gdb.bind(on_search_complete=search_stop)

    # The format below is referred to as `strokes`, a list of stroke paths.
    # Note that each path is two points, ie a straight line; if you plot them
    # it looks like a T.
    gdb.add_gesture('T', [
        [Vector(30, 7), Vector(103, 7)],
        [Vector(66, 7), Vector(66, 87)]])

    # And you can find shapes that are similar; this will trigger both of
    # the callbacks.
    gdb.recognize([
        [Vector(45, 8), Vector(110, 12)],
        [Vector(88, 9), Vector(85, 95)]])

On the next :class:`kivy.clock.Clock` tick, the matching process starts (and,
in this case, completes). The above program outputs::

    A search is starting with 1 tasks
    Search ended (complete). Best is T (score 0.770060, distance 0.229940)

Note that you can also use the result from the `recognize` function ::

    # Same as above, but keep track of progress using 'result'
    result = gdb.recognize([
        [Vector(45, 8), Vector(110, 12)],
        [Vector(88, 9), Vector(85, 95)]])

    result.bind(on_progress=my_other_callback)
    print result.progress # = 0

    # [ assuming a kivy.clock.Clock.tick() here ]

    # All 3 callbacks now executed.

    print result.progress # = 1
'''

__all__ = ('Recognizer', 'GestureSearch', 'Multistroke', 'Template', 'Candidate')

import pickle
import base64
import zlib
import re
from collections import deque
from math import sqrt, pi, radians, acos, atan, atan2, pow, floor
from math import sin as math_sin, cos as math_cos
from cStringIO import StringIO
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ListProperty

# Default number of gesture matches per frame
# FIXME: relevant number
DEFAULT_GPF = 10

# for both algorithms
SQUARESIZE = 250.0
ONEDTHRESHOLD = 0.25
ORIGIN = Vector(0, 0)

# only for golden section search:
PHI = 0.5 * (-1.0 + sqrt(5.0))
HALFDIAGONAL = 0.5 * sqrt(SQUARESIZE ** 2 + SQUARESIZE ** 2)


class MultistrokeError(Exception):
    pass


# -----------------------------------------------------------------------------
# Recognizer
# -----------------------------------------------------------------------------

class Recognizer(EventDispatcher):
    ''':class:`Recognizer` provides a gesture database with facilities for
    searching using both the $1 and Protractor algorithms.

    :Events:
        `on_search_start`:
            Fired when a new search is started using this Recognizer.

        `on_search_complete`:
            Fired when a running search ends, for whatever reason.
            (use :data:`GestureSearch.status` to find out)

    :Parameters:
        `gestures`:
            An optional list of Multistroke objects to seed `self.db`.
    '''

    db = ListProperty([])

    def __init__(self, **kwargs):
        self.register_event_type('on_search_start')
        self.register_event_type('on_search_complete')
        super(Recognizer, self).__init__(**kwargs)

    def filter(self, name=None, priority=None, numpoints=None, numstrokes=None,
        orientation_dep=None, db=None, force_sort=None, **kwargs):
        '''`filter` provides a window to the Multistroke objects in self.db. It
        is used to return a subset of objects according to given criteria, ie
        metadata. This function does not perform any template matching. It
        returns a `collections.deque` object.

        `name` uses regular expression criteria to match `Multistroke.name`.
        If re.match(name, Multistroke.name) is True, the gesture is returned,
        otherwise it is skipped ::

            gdb = Recognizer()
            # Will match all names that start with a captial N
            # (ie Next, New, N, Nebraska etc, but not "n" or "next")
            gdb.filter(name='N')

            # exactly 'N'
            gdb.filter(name='N$')

            # Nebraska, teletubbies, France, fraggle, N, n, etc
            gdb.filter(name=['[Nn]', '(?i)T', '(?i)F'])

        `priority` limits results to certain `Multistroke.priority` values.
        If specified as an integer, only templates with a lower priority are
        returned. Can also be specified as a list for min and max::

           gdb.filter(priority=50) # max 50
           gdb.filter(priority=[0, 50]) # the same; max 50
           gdb.filter(priority=[50, 100]) # min 50, max 100

        In the latter, all gestures with priority 50..100 are returned. When
        this option is used, the db is sorted according to priority (unless
        `force_priority_sort` is set to False).

        Note that when a maximum priority is set, the filter will return
        immediately once a gesture with higher priority is encountered. If you
        set `priority=50` and use `force_priority_sort=False`, the filter
        will return once a gesture with priority 51+ is encountered (in the
        order they were added to Recognizer.db)

        `orientation_dep` limits matches to gestures that are orientation
        dependant (True), gestures that are fully rotation invariant (False) or
        None; attempt to match everything, regardless of template orientation
        dependance (default).

        `numstrokes` allows you to match only gestures that have a specific
        number of items in the `.strokes` attribute. Syntax is the same as
        for numpoints, see below.

        `numpoints` allows you to match only gestures that have a specific
        .numpoints setting::

            gdb.filter(numpoints=16)
            gdb.filter(numpoints=[range(80,120)])

        This will allow resampling the candidate to match any template with
        numpoints set between 80 and 119 (in the latter example).

        `force_sort` is used to override the default sorting behavior.
        Normally, Multistrokes are evaluated in priority order if `priority` is
        used. True will force evaluation in priority order, False will force
        evaluation in the order added. None will let `priority` decide.
        Default is None::

            Load the Multistrokes to self.db in priority order and set this to
            False for faster evaluation. Maybe this should be available as
            .optimize() or something? I don't know anything about the impact.

        `db` can be set if you want to filter a different list of objects
        than self.db.

        FIXME: make method static or something?
        '''
        # Wrap arguments in lists as needed. Probably wrong way to do it.
        min_p, max_p = self._get_priority(priority)
        name = self._get_list(name, 'str')
        numstrokes = self._get_list(numstrokes, 'int')
        numpoints = self._get_list(numpoints, 'int')

        # Prepare a correctly sorted tasklist
        force_on = force_sort and True
        force_off = (not force_sort) and True
        tasklist = (((priority or force_on) and not force_off)
           and sorted(db or self.db, key=lambda n: n.priority)
            or (db or self.db))

        # FIXME: I did this to avoid calling .reverse on the list later, ie for
        # popleft(). I don't really know which one is better. I considered
        # using a dict instead, but it seems equally weak if not worse. It
        # would be interesting to try SQLite.
        out = deque()

        # Now test each gesture against the candidate
        for gesture in tasklist:

            if orientation_dep is not None and \
               orientation_dep != gesture.orientation_dep:
                continue

            if numpoints and gesture.numpoints not in numpoints:
                continue

            if numstrokes and len(gesture.strokes) not in numstrokes:
                continue

            if min_p and gesture.priority < min_p:
                continue

            if max_p and gesture.priority > max_p:
                return out

            if name:
                # FIXME: Best place is the narrowest possible scope, or what??
                for f in name:
                    if re.match(f, gesture.name):
                        out.append(gesture)
                        break
            else:
                out.append(gesture)

        return out

    def add_gesture(self, name, strokes, **kwargs):
        '''Add a multitroke gesture to the database. This function instantiates
        :class:`Multistroke` with `strokes` and appends it to self.db for you.
        Note: If you already have instantiated a Multistroke object, simply use
        gdb.db.append(your_object).
        '''
        if not strokes:
            return False
        self.db.append(Multistroke(name=name, strokes=strokes, **kwargs))
        return True

    def parse_gesture(self, data):
        '''Parse data as formatted by export_gesture(). Returns a list of
        gestures (Multistroke objects).'''
        io = StringIO(zlib.decompress(base64.b64decode(data)))
        p = pickle.Unpickler(io)
        multistrokes = []
        for multistroke in p.load():
            strokes = multistroke['strokes']
            multistroke['strokes'] = [[Vector(x, y) for x, y in line] for line in strokes]
            multistrokes.append(Multistroke(**multistroke))
        return multistrokes

    # FIXME: use a try block, maybe shelve or something
    def export_gesture(self, filename=None, **kwargs):
        '''Export a list of gestures (Multistroke objects) matching optional
        `filter` arguments. Outputs a base64-encoded string that can be decoded
        to a Python list with the `parse_gesture` function or imported to
        self.db with the `import_gesture` function. If `filename` is specified,
        the output is written to disk, otherwise returned.'''
        io = StringIO()
        p = pickle.Pickler(io)
        multistrokes = []
        defaults = {'priority': 100, 'numpoints': 16, 'use_strokelen': True,
                    'orientation_dep': False, 'angle_similarity': 30.0,
                    'phi_angle_range': 45.0, 'phi_angle_precision': 2.0}
        for multistroke in self.filter(**kwargs):
            m = {'name': multistroke.name}
            for attr, value in defaults.iteritems():
                current = getattr(multistroke, attr)
                if current != value:
                    m[attr] = current
            m['strokes'] = tuple([(p.x, p.y) for p in line] for line in multistroke.strokes)
            multistrokes.append(m)
        p.dump(multistrokes)

        if filename:
            f = open(filename, 'w')
            f.write(base64.b64encode(zlib.compress(io.getvalue(), 9)))
            f.close()
        else:
            return base64.b64encode(zlib.compress(io.getvalue(), 9))

    # FIXME: match them all with protractor, and don't load exacts? or
    # just compare the data or something; seems better to do this on import
    # than on every subsequent call to recognize(). And fix it in general,
    # too.
    def import_gesture(self, data=None, filename=None, **kwargs):
        '''Import a list of gestures as formatted by export_gesture(). One
        of `data` or `filename` must be specified as the source data. This
        method supports optional `filter` arguments, if none are specified
        then all gestures in specified data are imported.'''
        if filename is not None:
            data = file(filename).read()
        elif data is None:
            raise MultistrokeError('import_gesture needs data= or filename=')

        new = self.filter(db=self.parse_gesture(data), **kwargs)
        if new:
            self.db.extend(new)

    def transfer_gesture(self, tgt, **kwargs):
        '''Transfers all Multistroke objects in the database matching
        optional `filter` arguments to another :class:`Recognizer` instance
        `tgt`'''
        if hasattr(tgt, 'db') and isinstance(tgt.db, list):
            send = self.filter(**kwargs)
            if send:
                tgt.db.append(None)
                tgt.db[-1:] = send
                return True

    def prepare_templates(self, **kwargs):
        '''This method is used to prepare Template objects stored within the
        gestures in self.db. This is useful if you want to minimize the
        punishment of lazy resampling by preparing the vectors in advance. If
        you do this before a call to `export_gesture`, you will have the
        vectors computed when you load the exported gesture back in. This
        method accepts optional `filter` arguments.

        `force_numpoints`, if specified, will prepare all templates to the
        given number of points (instead of each template's preferred n; ie
        :data:`Template.numpoints`)'''
        for gesture in self.filter(**kwargs):
            for tpl in gesture:
                n = kwargs.get('force_numpoints', tpl.numpoints)
                tpl.prepare(n)

    def recognize(self, strokes, use_protractor=True, goodscore=None,
        timeout=0, delay=0, **kwargs):
        '''Search for candidate gesture in the database. Returns a
        :class:`GestureSearch` instance or None if invalid parameters are
        given. This method accepts optional `filter` arguments.

        `strokes` is a list of strokes (a stroke is a list of Vector objects),
        or a Candidate object. Note that if you manually supply a Candidate
        that uses :data:`Candidate.skip_*` flags, you have to make sure that
        the correct arguments are set to avoid requesting vectors that have
        not been computed. For example, if you set .skip_bounded and do not
        use `orientation_dep=False` filter, it will fail when/if `recognize`
        encounters a Template with orientation_dep=True.

        `use_protractor` determines if the protractor algorithm is used
        when comparing candidate to template. If False, the $1 golden section
        search algorithm is used.

        `timeout` specifies a timeout, in seconds, for when the search is
        aborted and the results so far returned. This option applies only when
        `gpf` is not 0. Default value is 0, meaning all gestures in the
        database will be processed, no matter how long it takes.

        `goodscore` sets a score so good, if the candidate scores it
        against a template, the search is immediately halted and the match(es)
        returned. 1.0 is a perfect match (unobtainable, unless you use the
        template as candidate). Default is None (disabled). When this option is
        used, the matching is performed according to gesture priority.

        .. warning::

            Scores differ depending on what algorithm is used and cannot always
            be ranked against each other. If use_protractor is False, it is
            safe to specify `goodscore` between 0..1 (1 is perfect match),
            otherwise the score is from 0..N; a score of 100 is *very* good,
            and typically only acheived on a very simple template.

        `force_numpoints` forces all templates (and candidate) to be prepared
        to a certain n. This is useful for example if you are evaluating
        templates for optimal n (you don't generally want to do this).

        `max_gpf` specifies the maximum number of gestures (Multistroke
        objects) that can be processed per frame. When exceeded, will cause
        the search to halt and resume work at the next frame. Setting to 0 will
        complete the search immediately (and block the UI).

        `force_priority_sort` can be used to set the `filter` `force_sort`
        option (normally, it is forced to True if `goodscore` is used)

        `delay` sets an optional delay between each run of the recognizer loop.
        Normally, a run is scheduled for the next frame until the tasklist is
        empty. If you set this, there will be a delay between each run of the
        specified number of seconds. Default is 0.
        '''
        GPF = kwargs.get('max_gpf', DEFAULT_GPF)

        # Obtain a list of Multistroke objects matching filter arguments
        force_ps = kwargs.get('force_priority_sort', None)
        force_ps = force_ps is None and (goodscore and True) or force_ps
        tasklist = self.filter(force_sort=force_ps, **kwargs)

        # Initialize the candidate and result objects
        cand = self._candidate(strokes, use_protractor, **kwargs)
        result = GestureSearch(cand, len(tasklist))

        # This is done to inform caller if they bind to on_complete and there
        # is nothing to do; perhaps should just return None?
        if not tasklist:
            result.status = 'complete'
            self.dispatch('on_search_complete', result)

            def result_hack(dt):
                result.dispatch('on_complete')
            Clock.schedule_once(result_hack)
            return result

        # This callback is scheduled once per frame until completed
        def _recognize_tick(dt):
            start_gc = result._completed
            stop_now = False

            # FIXME: impact of this? looks messy in 'while'
            def _criteria():
                return (tasklist and not result._break_flag) and \
                       (not GPF or result._completed - start_gc < GPF)

            while not stop_now and _criteria():

                if timeout and Clock.get_time() - result._start_time >= timeout:
                    result.status = 'timeout'
                    stop_now = True
                    break

                # Get the best distance and number of matching operations done
                gesture = tasklist.popleft()
                tpl, d, res, mos = gesture.match_candidate(
                    cand, use_protractor, **kwargs)

                if tpl is not None:
                    score = result._add_result(gesture, d, tpl, res,
                        use_protractor)

                    if goodscore is not None and score >= goodscore:
                        result.status = 'goodscore'
                        stop_now = True

                result._match_ops += mos
                result._completed += 1
                result.dispatch('on_progress')

            # The loop has ended. Prepare to dispatch 'complete'
            def _dispatch():
                result.dispatch('on_complete')
                self.dispatch('on_search_complete', result)
                return False

            # Dispatch or reschedule another run
            if not tasklist:
                result.status = 'complete'
                return _dispatch()
            elif result._break_flag:
                result.status = 'stop'
                return _dispatch()
            elif stop_now:
                return _dispatch()
            else:
                Clock.schedule_once(_recognize_tick, delay)
                return True
        # End _recognize_tick()

        self.dispatch('on_search_start', result)
        if not GPF:
            _recognize_tick(0)
        else:
            Clock.schedule_once(_recognize_tick, 0)

        return result

    def _candidate(self, strokes, use_protractor, **kwargs):
        # recognize() helper function, do not use directly. Set up a
        # Candidate object from arguments. Either use a specified object
        # or make a new one from strokes and apply safe skip_* settings to
        # use less resources.
        if isinstance(strokes, Candidate):
            return strokes

        if not isinstance(strokes, list) or not len(strokes) or \
           not isinstance(strokes[0], list):
            raise MultistrokeError('recognize() needs strokes= ' \
                                   'list or Candidate')

        cand = Candidate(strokes)
        if use_protractor:
            cand.skip_phi = True
        else:
            cand.skip_protractor = True

        o_filter = kwargs.get('orientation', None)
        if o_filter == False:
            cand.skip_bounded = True
        elif o_filter == True:
            cand.skip_invariant = True

        return cand

    # FIXME: better way?
    def _get_priority(self, p):
        if isinstance(p, list):
            return (int(p[0]), int(p[1]))
        elif p is not None:
            return (None, int(p))
        else:
            return (None, None)

    # FIXME: better way?
    def _get_list(self, l, type):
        if l.__class__.__name__ == type:
            return [l]
        elif isinstance(l, list):
            return l
        else:
            return None

    # Default event handlers
    def on_search_start(self, result):
        pass

    def on_search_complete(self, result):
        pass


# -----------------------------------------------------------------------------
# GestureSearch
# -----------------------------------------------------------------------------

class GestureSearch(EventDispatcher):
    '''Represents an ongoing (or completed) search operation. Instantiated and
    returned by the :meth:`Recognizer.recognize` method when it is called. The
    `results` attribute is a dictionary that is  updated as the recognition
    operation progresses.

    :Status values:
        `search`:
            Currently working
        `stop`:
            Was stopped by the user (:meth:`stop` called)
        `timeout`:
            A timeout occured (specified as `timeout=` to recognize())
        `goodscore`:
            The search was stopped early because a gesture with a high enough
            score was found (specified as `goodscore=` to recognize())
        `complete`:
            The search is complete (all gestures matching filters were tested)

    :Events:
        `on_progress`:
            Fired for every gesture that is processed
        `on_result`:
            Fired when a new result is added, and it is the first match
            for the `name` so far, or a consecutive match with better score.
        `on_complete`:
            Fired when the search is completed, for whatever reason.
            (use `GestureSearch.status` to find out)

    :Parameters:
        `candidate`:
            :class:`Candidate` object that is being evaluated
        `tasks`:
            Total number of gestures in tasklist (to test against)
    '''
    def __init__(self, candidate, tasks):
        self.status = 'search'
        self.candidate = candidate
        self.results = {}
        self.tasks = tasks
        self._start_time = Clock.get_time()
        self._match_ops = 0
        self._completed = 0
        self._break_flag = False

        # fired by recognize()
        self.register_event_type('on_complete')
        self.register_event_type('on_progress')

        # fired locally
        self.register_event_type('on_result')
        super(GestureSearch, self).__init__()

    @property
    def progress(self):
        '''Returns the progress as a float, 0 is 0% done, 1 is 100%'''
        if not self.tasks:
            return 1
        return self._completed / float(self.tasks)

    @property
    def best(self):
        '''Return the best match found by recognize() so far. It returns a
        dictionary with three keys, 'name', 'dist' and 'score' representing
        the template's name, distance (from candidate path) and the
        computed score value. The latter two depends on which algorithm is
        used.'''
        results = self.results  # to avoid too many self. lookups
        if not results:
            return {'name': None, 'dist': None, 'score': 0}
        b = max(results, key=lambda r: results[r]['score'])
        return {
            'name':  results[b]['name'],
            'dist':  results[b]['dist'],
            'score': results[b]['score']
        }

    def stop(self):
        '''Raises a stop flag that is checked by the search process. It will
        be stopped on the next clock tick (if it is still running).'''
        self._break_flag = True

    def _add_result(self, gesture, dist, tpl, res, use_protractor):
        '''Add a result; used by the recognize() function'''
        if tpl in res:
            n = gesture.templates[tpl].name
        else:
            return 0

        if n not in self.results or dist < self.results[n]['dist']:
            self.results[n] = {
                'name': n,
                'dist': dist,
                'gesture': gesture,
                'best_template': tpl,
                'template_results': res
            }

            def score_distance(d):
                return use_protractor \
                    and (1.0 / (d or .0001 ** 2)) \
                     or 1.0 - d / HALFDIAGONAL

            # Score the best distance; store in 'dist'
            self.results[n]['score'] = score_distance(dist)
            self.dispatch('on_result', self.results[n])
            return self.results[n]['score']
        return 0

    def on_complete(self):
        pass

    def on_progress(self):
        pass

    def on_result(self, result):
        pass


# -----------------------------------------------------------------------------
# Multistroke
# -----------------------------------------------------------------------------

class Multistroke(object):
    ''':class:`Multistroke` represents a gesture. It maintains a set of
    `strokes` and generates unistroke (ie :class:`Template`) permutations that
    are used for evaluating candidates against this gesture later.

    :Parameters:
        `name`:
            Identifies the name of the gesture - it is returned to you in the
            results of a :meth:`Recognizer.recognize` search. You can have any
            number of Multistroke objects with the same name; many definitions
            of one gesture. The same name is given to all the generated
            unistroke permutations. Required, no default.
        `strokes`:
            A list of paths that represents the gesture. A path is a list of
            Vector objects::

                gesture = Multistroke('tpl', strokes=[
                  [Vector(x1, y1), Vector(x2, y2), ...... ], # stroke 1
                  [Vector(), Vector(), Vector(), Vector() ]  # stroke 2
                  #, [stroke 3], [stroke 4], ...
                ])

            For template matching purposes, all the strokes are combined to a
            single list (unistroke). You should still specify the strokes
            individually, and set `use_strokelen` True (whenever possible).

            Once you do this, unistroke permutations are immediately generated
            and stored in `self.templates` for later, unless you set the
            `permute` flag to False.
        `priority`:
            Determines when :func:`Recognizer.recognize` will attempt to match
            this template, lower priorities are evaluated first (if `goodscore`
            or a priority `filter` is used). You should use lower priority on
            gestures that are more likely to match. For example, set the user's
            templates at lower priority than generic ones. Default is 100.
        `numpoints`:
            Determines the number of points this gesture should be resampled to
            (for matching purposes). If you are searching using the Protractor
            algorithm, 16 is given as optimal number (default). For golden
            section search, 96 is given as optimal number.
        `use_strokelen`:
            Determines if the number of strokes (paths) in this gesture is
            required to be the same in the candidate (user input) gesture
            during matching. If this is False, candidates will always be
            evaluated, disregarding the number of strokes. Default is True.
        `orientation_dep`:
            Determines if this gesture is orientation dependant. If True,
            templates are not prepared with full rotation invariance, but are
            instead restored to their original orientation. This requires the
            candidate to be drawn within +-`phi_angle_range` of the template
            (golden section search, $1 algorithm), or aligns the indicative
            orientation with the one of eight base orientations that requires
            the least rotation (Protractor). Default is False (fully rotation
            invariant) but many templates will have better results with True.
        `angle_similarity`:
            This is used by the :func:`Recognizer.recognize` function when a
            candidate is evaluated against this gesture. If the angles between
            them are too far off, the template is considered a non-match.
            Default is 30.0 (degrees)
        `phi_angle_range`:
            Used by the golden section search when evaluating a candidate
            against this template. Default is 45.0 (degrees).
            See research paper for details.
        `phi_angle_precision`
            Used by the golden section search when evaluating a candidate
            against this template. Default is 2.0 (degrees).
            See research paper for details.
        `permute`:
            If False, prevents the Template generation ($N algorithm) from
            running when instantiated. Default is True, if you set this to
            False you have to manually generate and add Template objects..
    '''
    def __init__(self, name, strokes=None, priority=100, numpoints=16,
                 use_strokelen=True, orientation_dep=False, **kwargs):
        self.name = name
        self.priority = priority
        self.numpoints = numpoints
        self.use_strokelen = use_strokelen
        self.orientation_dep = orientation_dep
        # FIXME: This is a mess should probably not be properties
        self.angle_similarity = kwargs.get('angle_similarity', 30.0)
        self.phi_angle_range = kwargs.get('phi_angle_range', 45.0)
        self.phi_angle_precision = kwargs.get('phi_angle_precision', 2.0)
        self.strokes = []

        if strokes is not None:
            self.strokes = strokes
            if kwargs.get('permute', True):
                self.permute()

    @property
    def angle_similarity_threshold(self):
        return radians(self.angle_similarity)

    @property
    def angle_range(self):
        '''Used internally by golden section search/$1'''
        return radians(self.phi_angle_range)

    @property
    def angle_precision(self):
        '''Used internally by golden section search/$1'''
        return radians(self.phi_angle_precision)

    def add_stroke(self, stroke, permute=False):
        '''Add a stroke to the self.strokes list. If `permute` is True, the
        :meth:`permute` method is called to generate new unistroke templates'''
        self.strokes.append(stroke)
        if permute:
            self.permute()

    def get_distance(self, cand, tpl, use_protractor, **kwargs):
        '''Compute the distance from this Candiate to a Template (in this
        Multistroke, usually) using one of the supported algorithms. Returns
        the Cosine distance (Protractor) or Euclidian distance ($1) between
        the stroke paths.

        `numpoints` will prepare both the Template and this Candidates path
        to n points (when neccessary), see lazy data preparation.
        '''
        n = kwargs.get('numpoints', self.numpoints)
        if use_protractor:
            # Cosine distance
            vec = cand.get_protractor_vector(n, tpl.orientation_dep)
            return optimal_cosine_distance(tpl.get_vector(n), vec)
        else:
            # Euclidian distance
            rng = self.angle_range
            prc = self.angle_precision
            pts = cand.get_phi_points(n, tpl.orientation_dep)
            return distance_at_best_angle(pts, tpl, -rng, +rng, prc, n)

    def match_candidate(self, cand, use_protractor=True, **kwargs):
        '''Match a given candidate against this Multistroke object. Will
        test against all templates and report results as a list of four
        items::

            - best matching template's index (in self.templates)
            - the computed distance from the template to the candidate path
            - a dict of {tpl_idx: distance} for all matched templates
            - a counter for the number of performed matching operations
        '''
        best_d = float('infinity')
        best_tpl = None
        mos = 0
        out = {}

        for idx, tpl in enumerate(self.templates):
            # Handle a theoretical case where a Multistroke is composed
            # manually and the orientation_dep flag is True, and it contains
            # a Template that has orientation_dep=False (or vice versa).
            # This would cause KeyError - requesing nonexistant vector.
            if cand.skip_bounded and tpl.orientation_dep:
                continue
            if cand.skip_invariant and not tpl.orientation_dep:
                continue

            if self.use_strokelen and \
               len(self.strokes) != len(cand.strokes):
                continue

            # Count as a match operation now, since the call to get_
            # angle_similarity below will force vector calculation,
            # even if it doesn't make it to get_distance
            mos += 1

            # Note: With this implementation, we always resample the
            # candidate to *any* encountered Template numpoints here, the
            # filter is only applied to Multistroke. See theoretical case
            # above; should not matter normally.
            n = kwargs.get('force_numpoints', tpl.numpoints)

            # Skip if candidate/gesture angles are too far off
            ang_sim = cand.get_angle_similarity(tpl, numpoints=n)
            if ang_sim > self.angle_similarity_threshold:
                continue

            # Get the distance between cand/tpl paths
            d = self.get_distance(cand, tpl, numpoints=n,
                     use_protractor=use_protractor)

            out[idx] = d

            if d < best_d:
                best_d = d
                best_tpl = idx

        return (best_tpl, best_d, out, mos)

    def permute(self):
        '''Generate all possible unistroke permutations from self.strokes and
        save the resulting list of Template objects in self.templates.

        Quote from http://faculty.washington.edu/wobbrock/pubs/gi-10.2.pdf ::

            We use Heap Permute [16] (p. 179) to generate all stroke orders
            in a multistroke gesture. Then, to generate stroke directions for
            each order, we treat each component stroke as a dichotomous
            [0,1] variable. There are 2^N combinations for N strokes, so we
            convert the decimal values 0 to 2^N-1, inclusive, to binary
            representations and regard each bit as indicating forward (0) or
            reverse (1). This algorithm is often used to generate truth tables
            in propositional logic.

        See section 4.1: "$N Algorithm" of the linked paper for details.
        '''
        # Seed with index of each stroke
        self._order = [i for i in xrange(0, len(self.strokes))]

        # Prepare ._orders
        self._orders = []
        self._heap_permute(len(self.strokes))
        del self._order

        # Generate unistroke permutations
        self.templates = [Template(
              self.name,
              points=permutation,
              numpoints=self.numpoints,
              orientation_dep=self.orientation_dep
        ) for permutation in self._make_unistrokes()]
        del self._orders

    def _heap_permute(self, n):
        '''Heap Permute algorithm'''
        if n == 1:
            self._orders.append(self._order[:])
        else:
            i = 0
            for i in xrange(0, n):
                self._heap_permute(n - 1)
                if n % 2 == 1:
                    tmp = self._order[0]
                    self._order[0] = self._order[n - 1]
                    self._order[n - 1] = tmp
                else:
                    tmp = self._order[i]
                    self._order[i] = self._order[n - 1]
                    self._order[n - 1] = tmp

    def _make_unistrokes(self):
        '''Create unistroke permutations from self.strokes'''
        unistrokes = []
        for r in self._orders:
            b = 0
            while b < pow(2, len(r)):  # use b's bits for directions
                unistroke = []
                for i in xrange(0, len(r)):
                    pts = self.strokes[r[i]][:]
                    if (b >> i) & 1 == 1:  # is b's bit at index i 1?
                        pts.reverse()
                    unistroke.append(None)
                    unistroke[-1:] = pts

                unistrokes.append(unistroke)
                b += 1
        return unistrokes


# -----------------------------------------------------------------------------
# Template
# -----------------------------------------------------------------------------

class Template(object):
    '''Represents a (uni)stroke path as a list of Vectors. Normally, this class
    is instantiated by Multistroke and not by the programmer directly. However,
    it is possible to manually compose Template objects. Please write module
    documentation for more information.

    :Parameters:
        `name`:
            Identifies the name of the gesture. This is normally inherited from
            the parent Multistroke object when a template is generated.
        `points`:
            A list of points that represents a unistroke path. This is normally
            one of the possible stroke order permutations from a Multistroke.
        `numpoints`:
            The number of points this template should (ideally) be resampled to
            before the matching process. This is normally 16 for Protractor and
            96 for golden section search, but you may want to experiment with
            template-specific settings.
        `orientation_dep`:
            Determines if this template is orientation dependant (True) or
            fully rotation invariant (False)
        `skip_phi`:
            If True, do not store data for golden section search
        `skip_protractor`:
            If True, will not generate or store data for Protractor

    Note that you WILL get errors if you set a skip_ flag and then attempt to
    retrieve the data.'''
    def __init__(self, name, points=None, **kwargs):
        self.name = name
        self.numpoints = kwargs.get('numpoints', 16)
        self.orientation_dep = kwargs.get('orientation_dep', False)

        self.skip_protractor = kwargs.get('skip_protractor', False)
        self.skip_phi = kwargs.get('skip_phi', False)

        self.db = {}
        self.points = []

        if points is not None:
            self.points = points

    def add_point(self, p):
        '''Add a point to the unistroke/path'''
        self.points.append(p)
        # All previously computed data is now void.
        self.db = {}

    # Used to lazily prepare the template
    def _get_db_key(self, key, numpoints=None):
        n = numpoints and numpoints or self.numpoints
        if n not in self.db:
            self.prepare(n)
        return self.db[n][key]

    def get_start_unit_vector(self, numpoints=None):
        return self._get_db_key('startv', numpoints)

    def get_vector(self, numpoints=None):
        return self._get_db_key('vector', numpoints)

    def get_points(self, numpoints=None):
        return self._get_db_key('points', numpoints)

    def prepare(self, numpoints=None):
        '''This function prepares the Template for matching given a target
        number of points (for resample). 16 is optimal for Protractor, 96 is
        optimal for golden section search. Data for both algorithms are
        prepared.'''

        if not self.points:
            raise MultistrokeError('prepare() called without self.points')

        # How many points are we resampling to?
        n = numpoints and numpoints or self.numpoints
        if not n:
            raise MultistrokeError('prepare() called with invalid numpoints')

        p = resample(self.points, n)
        radians = indicative_angle(p)
        p = rotate_by(p, -radians)
        p = scale_dim(p, SQUARESIZE, ONEDTHRESHOLD)

        if self.orientation_dep:
            p = rotate_by(p, +radians)  # restore

        p = translate_to(p, ORIGIN)

        # Now store it using the number of points in the resampled path as the
        # dict key. On the next call to get_*, it will be returned instead of
        # recomputed. Implicitly, you must reset self.db or call prepare() for
        # all the keys once you manipulate self.points.
        self.db[n] = {
          # Compute STARTANGLEINDEX as n/8:
          'startv': start_unit_vector(p, (n / 8)),
          'vector': self.skip_protractor or vectorize(p, self.orientation_dep),
          'points': self.skip_phi or p
        }


# -----------------------------------------------------------------------------
# Candidate
# -----------------------------------------------------------------------------

class Candidate(object):
    '''Represents a set of unistroke paths of user input, ie data to be matched
    against a :class:`Template` object using the $1 or Protractor algorithm. By
    default, data is precomputed and stored for both algorithms and to match
    both rotation bounded and fully invariant :class:`Template` objects.

    :Parameters:
        `strokes`:
            See :data:`Multistroke.strokes` for format example. The Candidate
            strokes are simply combined to a unistroke in the order given. The
            idea is that this will match one of the unistroke permutations in
            `Multistroke.templates`.
        `numpoints`:
            The Candidate's default N; this is only for a fallback, it is not
            normally used since n is driven by the Template we are being
            compared to. FIXME: remove?
        `skip_phi`:
            If True, do not store data for golden section search
        `skip_protractor`:
            If True, will not generate or store data for Protractor
        `skip_bounded`:
            If True, do not generate/store rotation bounded vectors
        `skip_invariant`:
            If True, do not generate/store rotation invariant vectors

    Note that you WILL get errors if you set a skip_ flag and then attempt to
    retrieve the data.'''
    def __init__(self, strokes=None, numpoints=16, **kwargs):
        self.skip_phi = kwargs.get('skip_phi', False)
        self.skip_protractor = kwargs.get('skip_protractor', False)
        self.skip_invariant = kwargs.get('skip_invariant', False)
        self.skip_bounded = kwargs.get('skip_bounded', False)

        self.numpoints = numpoints
        self.db = {}
        self.strokes = []

        if not strokes is None:
            self.strokes = strokes

    def add_stroke(self, s):
        '''Add a stroke to the search candidate'''
        self.points.append(s)
        # All previously computed data is now void.
        # FIXME: Does this make more sense?
        #self.dirty = dict((k, True) for k in self.db.keys())
        self.db = {}

    # Used to lazily prepare the candidate
    def _get_db_key(self, key, numpoints, orientation_dep):
        n = numpoints and numpoints or self.numpoints
        if n not in self.db:
            self.prepare(n)

        head = orientation_dep and 'bound_' or 'inv_'
        return self.db[n][head + key]

    def get_start_unit_vector(self, numpoints, orientation_dep):
        '''Get the start vector for this Candidate, with the path resampled to
        `numpoints` points. This is the first step in the matching process,
        common to both algorithms. It is compared to a Template object's start
        vector to determine angle similarity.'''
        return self._get_db_key('startv', numpoints, orientation_dep)

    def get_protractor_vector(self, numpoints, orientation_dep):
        '''Return vector for comparing to a Template with Protractor'''
        return self._get_db_key('vector', numpoints, orientation_dep)

    def get_phi_points(self, numpoints, orientation_dep):
        '''Return points for comparing to a Template with $1'''
        return self._get_db_key('points', numpoints, orientation_dep)

    def get_angle_similarity(self, tpl, **kwargs):
        '''Compute the angle similarity between this Candidate and a Template
        object. This step is common for both algorithms. Returns a number that
        represents the angle similarity, lower is more similar.'''
        n = kwargs.get('numpoints', self.numpoints)
        return angle_between_unit_vectors(
            self.get_start_unit_vector(n, tpl.orientation_dep),
             tpl.get_start_unit_vector(n))

    def prepare(self, numpoints=None):
        '''Prepare the Candidate vectors. self.strokes is combined to a single
        unistroke (connected end-to-end), resampled to `numpoints` points, and
        then the vectors are calculated and stored in self.db (for use by
        `get_distance` and `get_angle_similarity`)'''
        n = numpoints and numpoints or self.numpoints
        points = combine_strokes(self.strokes)
        points = resample(points, n)
        radians = indicative_angle(points)
        points = rotate_by(points, -radians)
        points = scale_dim(points, SQUARESIZE, ONEDTHRESHOLD)

        # Compute STARTANGLEINDEX as n / 8
        angidx = n / 8
        cand = {}

        # full rotation invariance
        if not self.skip_invariant:
            inv_points = translate_to(points, ORIGIN)
            cand['inv_startv'] = start_unit_vector(inv_points, angidx)

            if not self.skip_protractor:
                cand['inv_vector'] = vectorize(inv_points, False)

            if not self.skip_phi:
                cand['inv_points'] = inv_points

        # rotation bounded invariance
        if not self.skip_bounded:
            bound_points = rotate_by(points, +radians)  # restore
            bound_points = translate_to(bound_points, ORIGIN)
            cand['bound_startv'] = start_unit_vector(bound_points, angidx)

            if not self.skip_protractor:
                cand['bound_vector'] = vectorize(bound_points, True)

            if not self.skip_phi:
                cand['bound_points'] = bound_points

        self.db[n] = cand


# -----------------------------------------------------------------------------
# Helper functions from this point on. This is all directly related to the two
# recognition algorithms, and is almost 100% transcription from the JavaScript
# -----------------------------------------------------------------------------


def combine_strokes(strokes):
    '''Collapse a list of lists, ie connect multiple strokes to unistroke.'''
    return [i for sub in strokes for i in sub]


def resample(points, n):
    '''Resample a path to `n` points'''

    if not len(points) or not n:
        raise MultistrokeError('resample() called with invalid arguments')

    interval = path_length(points) / (n - 1)
    D = 0.0
    i = 1
    newpoints = [points[0]]
    workpoints = points[:]
    newpoints_len = 1
    workpoints_len = len(points)

    while i < len(workpoints):
        p1 = workpoints[i - 1]
        p2 = workpoints[i]
        d = distance(p1, p2)

        if D + d >= interval:
            qx = p1.x + ((interval - D) / d) * (p2.x - p1.x)
            qy = p1.y + ((interval - D) / d) * (p2.y - p1.y)
            q = Vector(qx, qy)
            newpoints.append(q)
            workpoints.insert(i, q)  # q is the next i
            newpoints_len += 1
            workpoints_len += 1
            D = 0.0
        else:
            D += d

        i += 1

    # rounding error; insert the last point
    if len(newpoints) < n:
        newpoints.append(points[-1])

    return newpoints


def indicative_angle(points):
    c = centroid(points)
    return atan2(c.y - points[0].y, c.x - points[0].x)


def rotate_by(points, radians):
    '''Rotate points around centroid'''
    c = centroid(points)
    cos = math_cos(radians)
    sin = math_sin(radians)
    newpoints = []

    for i in xrange(0, len(points)):
        qx = (points[i].x - c.x) * cos - (points[i].y - c.y) * sin + c.x
        qy = (points[i].x - c.x) * sin + (points[i].y - c.y) * cos + c.y
        newpoints.append(Vector(qx, qy))

    return newpoints


def scale_dim(points, size, oneDratio):
    bbox_x, bbox_y, bbox_w, bbox_h = bounding_box(points)

    # 1D or 2D gesture test
    uniformly = min(bbox_w / bbox_h, bbox_h / bbox_w) <= oneDratio

    newpoints = []
    for p in points:
        qx = uniformly and \
                p.x * (size / max(bbox_w, bbox_h)) \
             or p.x * (size / bbox_w)
        qy = uniformly and \
                p.y * (size / max(bbox_w, bbox_h)) \
             or p.y * (size / bbox_h)
        newpoints.append(Vector(qx, qy))

    return newpoints


def translate_to(points, pt):
    '''Translate points around centroid'''
    c = centroid(points)
    newpoints = []
    for p in points:
        qx = p.x + pt.x - c.x
        qy = p.y + pt.y - c.y
        newpoints.append(Vector(qx, qy))
    return newpoints


def vectorize(points, use_bounded_rotation_invariance):
    '''Helper function for the Protractor algorithm'''
    cos = 1.0
    sin = 0.0

    if use_bounded_rotation_invariance:
        ang = atan2(points[0].y, points[0].x)
        bo = (pi / 4.) * floor((ang + pi / 8.) / (pi / 4.))
        cos = math_cos(bo - ang)
        sin = math_sin(bo - ang)

    sum = 0.0
    vector = []
    vector_len = 0
    for p in points:
        newx = p.x * cos - p.y * sin
        newy = p.y * cos + p.x * sin
        vector.append(newx)
        vector.append(newy)
        vector_len += 2
        sum += newx ** 2 + newy ** 2

    magnitude = sqrt(sum)
    for i in xrange(0, vector_len):
        vector[i] /= magnitude

    return vector


def optimal_cosine_distance(v1, v2):
    '''Helper function for the Protractor algorithm'''
    a = 0.0
    b = 0.0

    for i in xrange(0, len(v1), 2):
        a += (v1[i] * v2[i]) + (v1[i + 1] * v2[i + 1])
        b += (v1[i] * v2[i + 1]) - (v1[i + 1] * v2[i])

    angle = atan(b / a)

    # If you put the below directly into math.acos(), you will get a domain
    # error when a=1.0 and angle=0.0 (ie math_cos(angle)=1.0). It seems this is
    # because float representation of 1.0*1.0 is >1.0 (ie 1.00000000...001)
    # and this is problematic for math.acos(). If you type math.acos(1.0*1.0)
    # to the interpreter, it does not happen, only with exact match at runtime
    result = a * math_cos(angle) + b * math_sin(angle)

    # FIXME: I'm sure there is a better way to do it but..
    if result >= 1:
        result = 1
    elif result <= -1:  # has not happened to me, but I leave it here.
        result = -1
    return acos(result)


def distance_at_best_angle(points, template, a, b, threshold, numpoints):
    '''
    Golden section search (original $1 algorithm). In most cases
    slower than Protractor.
    '''
    x1 = PHI * a + (1.0 - PHI) * b
    f1 = distance_at_angle(points, template, x1, numpoints)
    x2 = (1.0 - PHI) * a + PHI * b
    f2 = distance_at_angle(points, template, x2, numpoints)

    while abs(b - a) > threshold:
        if f1 < f2:
            b, x2 = x2, x1
            f2 = f1
            x1 = PHI * a + (1.0 - PHI) * b
            f1 = distance_at_angle(points, template, x1, numpoints)
        else:
            a, x1 = x1, x2
            f1 = f2
            x2 = (1.0 - PHI) * a + PHI * b
            f2 = distance_at_angle(points, template, x2, numpoints)

    return min(f1, f2)


def distance_at_angle(points, template, radians, numpoints):
    '''Golden section search (original $1 algorithm). Helper function.'''
    newpoints = rotate_by(points, radians)
    return path_distance(newpoints, template.get_points(numpoints))


def centroid(points):
    x = 0.0
    y = 0.0
    points_len = len(points)

    for i in xrange(0, points_len):
        x += points[i].x
        y += points[i].y

    x /= points_len
    y /= points_len

    return Vector(x, y)


def bounding_box(points):
    minx = float('infinity')
    miny = float('infinity')
    maxx = float('-infinity')
    maxy = float('-infinity')

    for p in points:
        if p.x < minx:
            minx = p.x
        if p.x > maxx:
            maxx = p.x
        if p.y < miny:
            miny = p.y
        if p.y > maxy:
            maxy = p.y

    return (minx, miny, maxx - minx, maxy - miny)


def path_distance(pts1, pts2):
    d = 0.0
    for i in xrange(0, len(pts1)):
        d += distance(pts1[i], pts2[i])
    return d / len(pts1)


def path_length(points):
    d = 0.0
    for i in xrange(1, len(points)):
        d += distance(points[i - 1], points[i])
    return d


def distance(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return sqrt(dx ** 2 + dy ** 2)


def start_unit_vector(points, index):
    v = Vector(points[index].x - points[0].x, points[index].y - points[0].y)
    length = sqrt(v.x ** 2 + v.y ** 2)
    return Vector(v.x / length, v.y / length)


def angle_between_unit_vectors(v1, v2):
    n = (v1.x * v2.x + v1.y * v2.y)
    # FIXME: Domain error on float representation of 1.0 (exact match)
    # (see optimal_cosine_distance)
    if n >= 1:
        return 0.0
    if n <= -1:
        return pi
    return acos(n)
