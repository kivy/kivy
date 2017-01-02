'''
Multistroke gesture recognizer
==============================

.. versionadded::
    1.9.0

.. warning::

    This is experimental and subject to change as long as this warning notice
    is present.

See :file:`kivy/examples/demo/multistroke/main.py` for a complete application
example.

Conceptual Overview
-------------------

This module implements the Protractor gesture recognition algorithm.

:class:`Recognizer` is the search/database API similar to
:class:`~kivy.gesture.GestureDatabase`. It maintains a list of
:class:`MultistrokeGesture` objects and allows you to search for a
user-input gestures among them.

:class:`ProgressTracker` tracks the progress of a :meth:`Recognizer.recognize`
call. It can be used to interact with the running recognizer task, for example
forcing it to stop half-way, or analyzing results as they arrive.

:class:`MultistrokeGesture` represents a gesture in the gesture database
(:attr:`Recognizer.db`). It is a container for :class:`UnistrokeTemplate`
objects, and implements the heap permute algorithm to automatically generate
all possible stroke orders (if desired).

:class:`UnistrokeTemplate` represents a single stroke path. It's typically
instantiated automatically by :class:`MultistrokeGesture`, but sometimes you
may need to create them manually.

:class:`Candidate` represents a user-input gesture that is used to search
the gesture database for matches. It is normally instantiated automatically
by calling :meth:`Recognizer.recognize`.

Usage examples
--------------

See :file:`kivy/examples/demo/multistroke/main.py` for a complete application
example.

You can bind to events on :class:`Recognizer` to track the state of all
calls to :meth:`Recognizer.recognize`. The callback function will receive an
instance of :class:`ProgressTracker` that can be used to analyze and control
various aspects of the recognition process ::

    from kivy.vector import Vector
    from kivy.multistroke import Recognizer

    gdb = Recognizer()

    def search_start(gdb, pt):
        print("A search is starting with %d tasks" % (pt.tasks))

    def search_stop(gdb, pt):
        # This will call max() on the result dictionary, so it's best to store
        # it instead of calling it 3 times consecutively
        best = pt.best
        print("Search ended (%s). Best is %s (score %f, distance %f)" % (
            pt.status, best['name'], best['score'], best['dist'] ))

    # Bind your callbacks to track all matching operations
    gdb.bind(on_search_start=search_start)
    gdb.bind(on_search_complete=search_stop)

    # The format below is referred to as `strokes`, a list of stroke paths.
    # Note that each path shown here consists of two points, ie a straight
    # line; if you plot them it looks like a T, hence the name.
    gdb.add_gesture('T', [
        [Vector(30, 7), Vector(103, 7)],
        [Vector(66, 7), Vector(66, 87)]])

    # Now you can search for the 'T' gesture using similar data (user input).
    # This will trigger both of the callbacks bound above.
    gdb.recognize([
        [Vector(45, 8), Vector(110, 12)],
        [Vector(88, 9), Vector(85, 95)]])

On the next :class:`~kivy.clock.Clock` tick, the matching process starts
(and, in this case, completes).

To track individual calls to :meth:`Recognizer.recognize`, use the return
value (also a :class:`ProgressTracker` instance) ::

    # Same as above, but keep track of progress using returned value
    progress = gdb.recognize([
        [Vector(45, 8), Vector(110, 12)],
        [Vector(88, 9), Vector(85, 95)]])

    progress.bind(on_progress=my_other_callback)
    print(progress.progress) # = 0

    # [ assuming a kivy.clock.Clock.tick() here ]

    print(result.progress) # = 1

Algorithm details
-----------------

For more information about the matching algorithm, see:

"Protractor: A fast and accurate gesture recognizer" by Yang Li
  http://yangl.org/pdf/protractor-chi2010.pdf

"$N-Protractor" by Lisa Anthony and Jacob O. Wobbrock
  http://depts.washington.edu/aimgroup/proj/dollar/ndollar-protractor.pdf

Some of the code is derived from the JavaScript implementation here:
  http://depts.washington.edu/aimgroup/proj/dollar/ndollar.html
'''

__all__ = ('Recognizer', 'ProgressTracker', 'MultistrokeGesture',
           'UnistrokeTemplate', 'Candidate')

import pickle
import base64
import zlib
from re import match as re_match
from collections import deque
from math import sqrt, pi, radians, acos, atan, atan2, pow, floor
from math import sin as math_sin, cos as math_cos
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from kivy.compat import PY2
from io import BytesIO

if not PY2:
    xrange = range

# Default number of gesture matches per frame
# FIXME: relevant number
DEFAULT_GPF = 10

# Algorithm data
SQUARESIZE = 250.0
ONEDTHRESHOLD = 0.25
ORIGIN = Vector(0, 0)


class MultistrokeError(Exception):
    pass


# -----------------------------------------------------------------------------
# Recognizer
# -----------------------------------------------------------------------------

class Recognizer(EventDispatcher):
    ''':class:`Recognizer` provides a gesture database with matching
    facilities.

    :Events:
        `on_search_start`
            Fired when a new search is started using this Recognizer.

        `on_search_complete`
            Fired when a running search ends, for whatever reason.
            (use :data:`ProgressTracker.status` to find out)

    :Properties:
        `db`
            A :class:`ListProperty` that contains the available
            :class:`MultistrokeGesture` objects.

            :attr:`db` is a
            :class:`~kivy.properties.ListProperty` and defaults to []
    '''

    db = ListProperty([])

    def __init__(self, **kwargs):
        super(Recognizer, self).__init__(**kwargs)
        self.register_event_type('on_search_start')
        self.register_event_type('on_search_complete')

    def filter(self, **kwargs):
        ''':meth:`filter` returns a subset of objects in :attr:`self.db`,
        according to given criteria. This is used by many other methods of
        the :class:`Recognizer`; the arguments below can for example be
        used when calling :meth:`Recognizer.recognize` or
        :meth:`Recognizer.export_gesture`. You normally don't need to call
        this directly.

        :Arguments:

            `name`
                Limits the returned list to gestures where
                :attr:`MultistrokeGesture.name` matches given regular
                expression(s). If re.match(name, MultistrokeGesture.name)
                tests true, the gesture is included in the returned list.
                Can be a string or an array of strings ::

                    gdb = Recognizer()

                    # Will match all names that start with a capital N
                    # (ie Next, New, N, Nebraska etc, but not "n" or "next")
                    gdb.filter(name='N')

                    # exactly 'N'
                    gdb.filter(name='N$')

                    # Nebraska, teletubbies, France, fraggle, N, n, etc
                    gdb.filter(name=['[Nn]', '(?i)T', '(?i)F'])

            `priority`
                Limits the returned list to gestures with certain
                :attr:`MultistrokeGesture.priority` values. If specified as an
                integer, only gestures with a lower priority are returned. If
                specified as a list (min/max) ::

                    # Max priority 50
                    gdb.filter(priority=50)

                    # Max priority 50 (same result as above)
                    gdb.filter(priority=[0, 50])

                    # Min priority 50, max 100
                    gdb.filter(priority=[50, 100])

                When this option is used, :attr:`Recognizer.db` is
                automatically sorted according to priority, incurring extra
                cost. You can use `force_priority_sort` to override this
                behavior if your gestures are already sorted according to
                priority.

            `orientation_sensitive`
                Limits the returned list to gestures that are
                orientation sensitive (True), gestures that are not orientation
                sensitive (False) or None (ignore template sensitivity, this is
                the default).

            `numstrokes`
                Limits the returned list to gestures that have the specified
                number of strokes (in :attr:`MultistrokeGesture.strokes`).
                Can be a single integer or a list of integers.

            `numpoints`
                Limits the returned list to gestures that have specific
                :attr:`MultistrokeGesture.numpoints` values. This is provided
                for flexibility, do not use it unless you understand what it
                does. Can be a single integer or a list of integers.

            `force_priority_sort`
                Can be used to override the default sort behavior. Normally
                :class:`MultistrokeGesture` objects are returned in priority
                order if the `priority` option is used. Setting this to True
                will return gestures sorted in priority order, False will
                return in the order gestures were added. None means decide
                automatically (the default).

                .. Note ::
                    For improved performance, you can load your gesture
                    database in priority order and set this to False when
                    calling :meth:`Recognizer.recognize`

            `db`
                Can be set if you want to filter a different list of objects
                than :attr:`Recognizer.db`. You probably don't want to do this;
                it is used internally by :meth:`import_gesture`.
        '''
        have_filters = False

        kwargs_get = kwargs.get

        name = kwargs_get('name', None)
        if name is not None:
            have_filters = True
            if not isinstance(name, list):
                name = [name]

        priority = kwargs_get('priority', None)
        min_p, max_p = None, None
        if priority is not None:
            have_filters = True
            if isinstance(priority, list):
                min_p, max_p = priority
            elif isinstance(priority, int):
                min_p, max_p = None, priority

        numstrokes = kwargs_get('numstrokes', None)
        if numstrokes is not None:
            have_filters = True
            if not isinstance(numstrokes, list):
                numstrokes = [numstrokes]

        numpoints = kwargs_get('numpoints', None)
        if numpoints is not None:
            have_filters = True
            if not isinstance(numpoints, list):
                numpoints = [numpoints]

        orientation_sens = kwargs_get('orientation_sensitive', None)
        if orientation_sens is not None:
            have_filters = True

        # Prepare a correctly sorted tasklist
        force_priority_sort = kwargs.get('force_priority_sort', None)
        force_sort_on = force_priority_sort and True
        force_sort_off = (force_priority_sort is False) and True

        db = kwargs.get('db', None) or self.db
        if (force_sort_on or priority) and not force_sort_off:
            tasklist = sorted(db, key=lambda n: n.priority)
        else:
            tasklist = db

        # Now test each gesture in the database against filter criteria
        out = deque()
        if not have_filters:
            out.extend(tasklist)
            return out

        out_append = out.append
        for gesture in tasklist:

            if (orientation_sens is not None and
                    orientation_sens != gesture.orientation_sens):
                continue

            if numpoints and gesture.numpoints not in numpoints:
                continue

            if numstrokes and len(gesture.strokes) not in numstrokes:
                continue

            if min_p is not None and gesture.priority < min_p:
                continue

            if max_p is not None and gesture.priority > max_p:
                return out

            if name:
                for f in name:
                    if re_match(f, gesture.name):
                        out_append(gesture)
                        break
            else:
                out_append(gesture)

        return out

    def add_gesture(self, name, strokes, **kwargs):
        '''Add a new gesture to the database. This will instantiate a new
        :class:`MultistrokeGesture` with `strokes` and append it to self.db.

        .. Note ::
            If you already have instantiated a :class:`MultistrokeGesture`
            object and wish to add it, append it to :attr:`Recognizer.db`
            manually.
        '''
        if not strokes:
            return False
        self.db.append(
            MultistrokeGesture(name=name, strokes=strokes, **kwargs)
        )
        return True

    def parse_gesture(self, data):
        '''Parse data formatted by export_gesture(). Returns a list of
        :class:`MultistrokeGesture` objects. This is used internally by
        :meth:`import_gesture`, you normally don't need to call this
        directly.'''
        io = BytesIO(zlib.decompress(base64.b64decode(data)))

        p = pickle.Unpickler(io)
        multistrokes = []
        ms_append = multistrokes.append
        for multistroke in p.load():
            strokes = multistroke['strokes']
            multistroke['strokes'] = [[Vector(
                x, y) for x, y in line] for line in strokes]
            ms_append(MultistrokeGesture(**multistroke))
        return multistrokes

    # FIXME: use a try block, maybe shelve or something
    def export_gesture(self, filename=None, **kwargs):
        '''Export a list of :class:`MultistrokeGesture` objects. Outputs a
        base64-encoded string that can be decoded to a Python list with
        the :meth:`parse_gesture` function or imported directly to
        :attr:`self.db` using :meth:`Recognizer.import_gesture`. If
        `filename` is specified, the output is written to disk, otherwise
        returned.

        This method accepts optional :meth:`Recognizer.filter` arguments.
        '''
        io = BytesIO()
        p = pickle.Pickler(io, protocol=0)
        multistrokes = []
        defaults = {'priority': 100, 'numpoints': 16, 'stroke_sens': True,
                    'orientation_sens': False, 'angle_similarity': 30.0}
        dkeys = defaults.keys()

        for multistroke in self.filter(**kwargs):
            m = dict(defaults)
            m = {'name': multistroke.name}
            for attr in dkeys:
                m[attr] = getattr(multistroke, attr)
            m['strokes'] = tuple([(p.x, p.y) for p in line]
                                 for line in multistroke.strokes)
            multistrokes.append(m)
        p.dump(multistrokes)

        if filename:
            f = open(filename, 'wb')
            f.write(base64.b64encode(zlib.compress(io.getvalue(), 9)))
            f.close()
        else:
            return base64.b64encode(zlib.compress(io.getvalue(), 9))

    # FIXME: match them all with protractor, and don't load exacts? or
    # just compare the data or something; seems better to do this on import
    # than on every subsequent call to recognize(). And fix it in general,
    # too.
    def import_gesture(self, data=None, filename=None, **kwargs):
        '''Import a list of gestures as formatted by :meth:`export_gesture`.
        One of `data` or `filename` must be specified.

        This method accepts optional :meth:`Recognizer.filter` arguments,
        if none are specified then all gestures in specified data are
        imported.'''
        if filename is not None:
            with open(filename, "rb") as infile:
                data = infile.read()
        elif data is None:
            raise MultistrokeError('import_gesture needs data= or filename=')

        new = self.filter(db=self.parse_gesture(data), **kwargs)
        if new:
            self.db.extend(new)

    def transfer_gesture(self, tgt, **kwargs):
        '''Transfers :class:`MultistrokeGesture` objects from
        :attr:`Recognizer.db` to another :class:`Recognizer` instance `tgt`.

        This method accepts optional :meth:`Recognizer.filter` arguments.
        '''
        if hasattr(tgt, 'db') and isinstance(tgt.db, list):
            send = self.filter(**kwargs)
            if send:
                tgt.db.append(None)
                tgt.db[-1:] = send
                return True

    def prepare_templates(self, **kwargs):
        '''This method is used to prepare :class:`UnistrokeTemplate` objects
        within the gestures in self.db. This is useful if you want to minimize
        punishment of lazy resampling by preparing all vectors in advance. If
        you do this before a call to :meth:`Recognizer.export_gesture`, you
        will have the vectors computed when you load the data later.

        This method accepts optional :meth:`Recognizer.filter` arguments.

        `force_numpoints`, if specified, will prepare all templates to the
        given number of points (instead of each template's preferred n; ie
        :data:`UnistrokeTemplate.numpoints`). You normally don't want to
        do this.'''
        for gesture in self.filter(**kwargs):
            for tpl in gesture:
                n = kwargs.get('force_numpoints', tpl.numpoints)
                tpl.prepare(n)

    def recognize(self, strokes, goodscore=None, timeout=0, delay=0, **kwargs):
        '''Search for gestures matching `strokes`. Returns a
        :class:`ProgressTracker` instance.

        This method accepts optional :meth:`Recognizer.filter` arguments.

        :Arguments:

            `strokes`
                A list of stroke paths (list of lists of
                :class:`~kivy.vector.Vector` objects) that will be matched
                against gestures in the database. Can also be a
                :class:`Candidate` instance.

                .. Warning ::

                    If you manually supply a :class:`Candidate` that has a
                    skip-flag, make sure that the correct filter arguments
                    are set. Otherwise the system will attempt to load vectors
                    that have not been computed. For example, if you set
                    `skip_bounded` and do not set `orientation_sensitive` to
                    False, it will raise an exception if an
                    orientation_sensitive :class:`UnistrokeTemplate`
                    is encountered.

            `goodscore`
                If this is set (between 0.0 - 1.0) and a gesture score is
                equal to or higher than the specified value, the search is
                immediately halted and the on_search_complete event is
                fired (+ the on_complete event of the associated
                :class:`ProgressTracker` instance). Default is None (disabled).

            `timeout`
                Specifies a timeout (in seconds) for when the search is
                aborted and the results returned. This option applies only
                when `max_gpf` is not 0. Default value is 0, meaning all
                gestures in the database will be tested, no matter how long
                it takes.

            `max_gpf`
                Specifies the maximum number of :class:`MultistrokeGesture`
                objects that can be processed per frame. When exceeded, will
                cause the search to halt and resume work in the next frame.
                Setting to 0 will complete the search immediately (and block
                the UI).

                .. Warning ::

                    This does not limit the number of
                    :class:`UnistrokeTemplate` objects matched! If a single
                    gesture has a million templates, they will all be
                    processed in a single frame with max_gpf=1!

            `delay`
                Sets an optional delay between each run of the recognizer
                loop. Normally, a run is scheduled for the next frame until
                the tasklist is exhausted. If you set this, there will be an
                additional delay between each run (specified in seconds).
                Default is 0, resume in the next frame.

            `force_numpoints`
                forces all templates (and candidate) to be prepared to a
                certain number of points. This can be useful for example if
                you are evaluating templates for optimal n (do not use this
                unless you understand what it does).
        '''
        GPF = kwargs.get('max_gpf', DEFAULT_GPF)

        # Obtain a list of MultistrokeGesture objects matching filter arguments
        tasklist = self.filter(**kwargs)

        # Initialize the candidate and result objects
        cand = self._candidate(strokes)
        result = ProgressTracker(cand, len(tasklist))

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

            while not stop_now and (tasklist and not result._break_flag) and \
                    (not GPF or (result._completed - start_gc < GPF)):

                if (timeout and
                        Clock.get_time() - result._start_time >= timeout):
                    result.status = 'timeout'
                    stop_now = True
                    break

                # Get the best distance and number of matching operations done
                gesture = tasklist.popleft()
                tpl, d, res, mos = gesture.match_candidate(
                    cand, **kwargs)

                if tpl is not None:
                    score = result._add_result(gesture, d, tpl, res)
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

    def _candidate(self, strokes, **kwargs):
        # recognize() helper function, do not use directly. Set up a
        # Candidate object from arguments. Either use a specified object
        # or make a new one from strokes and apply safe skip_* settings to
        # use less resources.
        if isinstance(strokes, Candidate):
            return strokes

        if (not isinstance(strokes, list) or not len(strokes) or not
                isinstance(strokes[0], list)):
            raise MultistrokeError('recognize() needs strokes= '
                                   'list or Candidate')

        cand = Candidate(strokes)
        o_filter = kwargs.get('orientation_sensitive', None)
        if o_filter is False:
            cand.skip_bounded = True
        elif o_filter is True:
            cand.skip_invariant = True

        return cand

    # Default event handlers
    def on_search_start(self, result):
        pass

    def on_search_complete(self, result):
        pass


# -----------------------------------------------------------------------------
# ProgressTracker
# -----------------------------------------------------------------------------

class ProgressTracker(EventDispatcher):
    '''Represents an ongoing (or completed) search operation. Instantiated and
    returned by the :meth:`Recognizer.recognize` method when it is called. The
    `results` attribute is a dictionary that is  updated as the recognition
    operation progresses.

    .. Note ::
        You do not need to instantiate this class.

    :Arguments:
        `candidate`
            :class:`Candidate` object to be evaluated
        `tasks`
            Total number of gestures in tasklist (to test against)

    :Events:
        `on_progress`
            Fired for every gesture that is processed
        `on_result`
            Fired when a new result is added, and it is the first match
            for the `name` so far, or a consecutive match with better score.
        `on_complete`
            Fired when the search is completed, for whatever reason.
            (use `ProgressTracker.status` to find out)

    :Attributes:
        `results`
            A dictionary of all results (so far). The key is the name of the
            gesture (ie :attr:`UnistrokeTemplate.name` usually inherited from
            :class:`MultistrokeGesture`). Each item in the dictionary is a
            dict with the following entries:

                `name`
                    Name of the matched template (redundant)
                `score`
                    Computed score from 1.0 (perfect match) to 0.0
                `dist`
                    Cosine distance from candidate to template (low=closer)
                `gesture`
                    The :class:`MultistrokeGesture` object that was matched
                `best_template`
                    Index of the best matching template (in
                    :attr:`MultistrokeGesture.templates`)
                `template_results`
                    List of distances for all templates. The list index
                    corresponds to a :class:`UnistrokeTemplate` index in
                    gesture.templates.

        `status`
            `search`
                Currently working
            `stop`
                Was stopped by the user (:meth:`stop` called)
            `timeout`
                A timeout occurred (specified as `timeout=` to recognize())
            `goodscore`
                The search was stopped early because a gesture with a high
                enough score was found (specified as `goodscore=` to
                recognize())
            `complete`
                The search is complete (all gestures matching filters were
                tested)
    '''
    def __init__(self, candidate, tasks, **kwargs):
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
        super(ProgressTracker, self).__init__(**kwargs)

    @property
    def progress(self):
        '''Returns the progress as a float, 0 is 0% done, 1 is 100%. This
        is a Python property.'''
        if not self.tasks:
            return 1
        return self._completed / float(self.tasks)

    @property
    def best(self):
        '''Return the best match found by recognize() so far. It returns a
        dictionary with three keys, 'name', 'dist' and 'score' representing
        the template's name, distance (from candidate path) and the
        computed score value. This is a Python property.'''
        results = self.results  # to avoid too many self. lookups
        if not results:
            return {'name': None, 'dist': None, 'score': 0}
        b = max(results, key=lambda r: results[r]['score'])
        return {
            'name': results[b]['name'],
            'dist': results[b]['dist'],
            'score': results[b]['score']
        }

    def stop(self):
        '''Raises a stop flag that is checked by the search process. It will
        be stopped on the next clock tick (if it is still running).'''
        self._break_flag = True

    def _add_result(self, gesture, dist, tpl, res):
        # Add a result; used internally by the recognize() function
        if tpl <= len(res):
            n = gesture.templates[tpl].name
        else:
            return 0.

        if n not in self.results or dist < self.results[n]['dist']:
            self.results[n] = {
                'name': n,
                'dist': dist,
                'gesture': gesture,
                'best_template': tpl,
                'template_results': res
            }

            if not dist:
                self.results[n]['score'] = 1.0
            else:
                self.results[n]['score'] = 1.0 - (dist / pi)

            self.dispatch('on_result', self.results[n])
            return self.results[n]['score']
        else:
            return 0.

    def on_complete(self):
        pass

    def on_progress(self):
        pass

    def on_result(self, result):
        pass


# -----------------------------------------------------------------------------
# MultistrokeGesture
# -----------------------------------------------------------------------------

class MultistrokeGesture(object):
    ''':class:`MultistrokeGesture` represents a gesture. It maintains a set of
    `strokes` and generates unistroke (ie :class:`UnistrokeTemplate`)
    permutations that are used for evaluating candidates against this gesture
    later.

    :Arguments:
        `name`
            Identifies the name of the gesture - it is returned to you in the
            results of a :meth:`Recognizer.recognize` search. You can have any
            number of MultistrokeGesture objects with the same name; many
            definitions of one gesture. The same name is given to all the
            generated unistroke permutations. Required, no default.
        `strokes`
            A list of paths that represents the gesture. A path is a list of
            Vector objects::

                gesture = MultistrokeGesture('my_gesture', strokes=[
                  [Vector(x1, y1), Vector(x2, y2), ...... ], # stroke 1
                  [Vector(), Vector(), Vector(), Vector() ]  # stroke 2
                  #, [stroke 3], [stroke 4], ...
                ])

            For template matching purposes, all the strokes are combined to a
            single list (unistroke). You should still specify the strokes
            individually, and set `stroke_sensitive` True (whenever possible).

            Once you do this, unistroke permutations are immediately generated
            and stored in `self.templates` for later, unless you set the
            `permute` flag to False.
        `priority`
            Determines when :func:`Recognizer.recognize` will attempt to match
            this template, lower priorities are evaluated first (only if
            a priority `filter` is used). You should use lower priority on
            gestures that are more likely to match. For example, set user
            templates at lower number than generic templates. Default is 100.
        `numpoints`
            Determines the number of points this gesture should be resampled to
            (for matching purposes). The default is 16.
        `stroke_sensitive`
            Determines if the number of strokes (paths) in this gesture is
            required to be the same in the candidate (user input) gesture
            during matching. If this is False, candidates will always be
            evaluated, disregarding the number of strokes. Default is True.
        `orientation_sensitive`
            Determines if this gesture is orientation sensitive. If True,
            aligns the indicative orientation with the one of eight base
            orientations that requires least rotation. Default is True.
        `angle_similarity`
            This is used by the :func:`Recognizer.recognize` function when a
            candidate is evaluated against this gesture. If the angles between
            them are too far off, the template is considered a non-match.
            Default is 30.0 (degrees)
        `permute`
            If False, do not use Heap Permute algorithm to generate different
            stroke orders when instantiated. If you set this to False, a
            single UnistrokeTemplate built from `strokes` is used.
    '''
    def __init__(self, name, strokes=None, **kwargs):
        self.name = name
        self.priority = kwargs.get('priority', 100)
        self.numpoints = kwargs.get('numpoints', 16)
        self.stroke_sens = kwargs.get('stroke_sensitive', True)
        self.orientation_sens = kwargs.get('orientation_sensitive', True)
        self.angle_similarity = kwargs.get('angle_similarity', 30.0)
        self.strokes = []

        if strokes is not None:
            self.strokes = strokes
            if kwargs.get('permute', True):
                self.permute()
            else:
                self.templates = [UnistrokeTemplate(name,
                                  points=[i for sub in strokes for i in sub],
                                  numpoints=self.numpoints,
                                  orientation_sensitive=self.orientation_sens)]

    def angle_similarity_threshold(self):
        return radians(self.angle_similarity)

    def add_stroke(self, stroke, permute=False):
        '''Add a stroke to the self.strokes list. If `permute` is True, the
        :meth:`permute` method is called to generate new unistroke templates'''
        self.strokes.append(stroke)
        if permute:
            self.permute()

    def get_distance(self, cand, tpl, numpoints=None):
        '''Compute the distance from this Candiate to a UnistrokeTemplate.
        Returns the Cosine distance between the stroke paths.

        `numpoints` will prepare both the UnistrokeTemplate and Candidate path
        to n points (when necessary), you probably don't want to do this.
        '''
        n = numpoints
        if n is None or n < 2:
            n = self.numpoints

        # optimal_cosine_distance() inlined here for performance
        v1 = tpl.get_vector(n)
        v2 = cand.get_protractor_vector(n, tpl.orientation_sens)

        a = 0.0
        b = 0.0

        for i in xrange(0, len(v1), 2):
            a += (v1[i] * v2[i]) + (v1[i + 1] * v2[i + 1])
            b += (v1[i] * v2[i + 1]) - (v1[i + 1] * v2[i])

        angle = atan(b / a)

        # If you put the below directly into math.acos(), you will get a domain
        # error when a=1.0 and angle=0.0 (ie math_cos(angle)=1.0). It seems to
        # be because float representation of 1.0*1.0 is >1.0 (ie 1.00000...001)
        # and this is problematic for math.acos().
        # If you try math.acos(1.0*1.0) in interpreter it does not happen,
        # only with exact match at runtime
        result = a * math_cos(angle) + b * math_sin(angle)

        # FIXME: I'm sure there is a better way to do it but..
        if result >= 1:
            result = 1
        elif result <= -1:  # has not happened to me, but I leave it here.
            result = -1
        return acos(result)

    def match_candidate(self, cand, **kwargs):
        '''Match a given candidate against this MultistrokeGesture object. Will
        test against all templates and report results as a list of four
        items:

            `index 0`
                Best matching template's index (in self.templates)
            `index 1`
                Computed distance from the template to the candidate path
            `index 2`
                List of distances for all templates. The list index
                corresponds to a :class:`UnistrokeTemplate` index in
                self.templates.
            `index 3`
                Counter for the number of performed matching operations, ie
                templates matched against the candidate
        '''
        best_d = float('infinity')
        best_tpl = None
        mos = 0
        out = []

        if (self.stroke_sens and len(self.strokes) != len(cand.strokes)):
            return (best_tpl, best_d, out, mos)

        skip_bounded = cand.skip_bounded
        skip_invariant = cand.skip_invariant
        get_distance = self.get_distance
        ang_sim_threshold = self.angle_similarity_threshold()

        for idx, tpl in enumerate(self.templates):
            # Handle a theoretical case where a MultistrokeGesture is composed
            # manually and the orientation_sensitive flag is True, and contains
            # a UnistrokeTemplate that has orientation_sensitive=False (or vice
            # versa). This would cause KeyError - requesting nonexistant vector
            if tpl.orientation_sens:
                if skip_bounded:
                    continue
            elif skip_invariant:
                continue

            # Count as a match operation now, since the call to get_
            # angle_similarity below will force vector calculation,
            # even if it doesn't make it to get_distance
            mos += 1

            # Note: With this implementation, we always resample the candidate
            # to *any* encountered UnistrokeTemplate numpoints here, the filter
            # is only applied to MultistrokeGesture. See theoretical case
            # above; should not matter normally.
            n = kwargs.get('force_numpoints', tpl.numpoints)

            # Skip if candidate/gesture angles are too far off
            ang_sim = cand.get_angle_similarity(tpl, numpoints=n)
            if ang_sim > ang_sim_threshold:
                continue

            # Get the distance between cand/tpl paths
            d = get_distance(cand, tpl, numpoints=n)
            out.append(d)

            if d < best_d:
                best_d = d
                best_tpl = idx

        return (best_tpl, best_d, out, mos)

    def permute(self):
        '''Generate all possible unistroke permutations from self.strokes and
        save the resulting list of UnistrokeTemplate objects in self.templates.

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

        .. Warning ::

            Using heap permute for gestures with more than 3 strokes
            can result in very large number of templates (a 9-stroke
            gesture = 38 million templates). If you are dealing with
            these types of gestures, you should manually compose
            all the desired stroke orders.
        '''
        # Seed with index of each stroke
        self._order = [i for i in xrange(0, len(self.strokes))]

        # Prepare ._orders
        self._orders = []
        self._heap_permute(len(self.strokes))
        del self._order

        # Generate unistroke permutations
        self.templates = [UnistrokeTemplate(
            self.name,
            points=permutation,
            numpoints=self.numpoints,
            orientation_sensitive=self.orientation_sens
        ) for permutation in self._make_unistrokes()]
        del self._orders

    def _heap_permute(self, n):
        # Heap Permute algorithm
        self_order = self._order
        if n == 1:
            self._orders.append(self_order[:])
        else:
            i = 0
            for i in xrange(0, n):
                self._heap_permute(n - 1)
                if n % 2 == 1:
                    tmp = self_order[0]
                    self_order[0] = self_order[n - 1]
                    self_order[n - 1] = tmp
                else:
                    tmp = self_order[i]
                    self_order[i] = self_order[n - 1]
                    self_order[n - 1] = tmp

    def _make_unistrokes(self):
        # Create unistroke permutations from self.strokes
        unistrokes = []
        unistrokes_append = unistrokes.append
        self_strokes = self.strokes
        for r in self._orders:
            b = 0
            while b < pow(2, len(r)):  # use b's bits for directions
                unistroke = []
                unistroke_append = unistroke.append
                for i in xrange(0, len(r)):
                    pts = self_strokes[r[i]][:]
                    if (b >> i) & 1 == 1:  # is b's bit at index i 1?
                        pts.reverse()
                    unistroke_append(None)
                    unistroke[-1:] = pts

                unistrokes_append(unistroke)
                b += 1
        return unistrokes


# -----------------------------------------------------------------------------
# UnistrokeTemplate
# -----------------------------------------------------------------------------

class UnistrokeTemplate(object):
    '''Represents a (uni)stroke path as a list of Vectors. Normally, this class
    is instantiated by MultistrokeGesture and not by the programmer directly.
    However, it is possible to manually compose UnistrokeTemplate objects.

    :Arguments:
        `name`
            Identifies the name of the gesture. This is normally inherited from
            the parent MultistrokeGesture object when a template is generated.
        `points`
            A list of points that represents a unistroke path. This is normally
            one of the possible stroke order permutations from a
            MultistrokeGesture.
        `numpoints`
            The number of points this template should (ideally) be resampled to
            before the matching process. The default is 16, but you can use a
            template-specific settings if that improves results.
        `orientation_sensitive`
            Determines if this template is orientation sensitive (True) or
            fully rotation invariant (False). The default is True.

    .. Note::
        You will get an exception if you set a skip-flag and then attempt to
        retrieve those vectors.
    '''
    def __init__(self, name, points=None, **kwargs):
        self.name = name
        self.numpoints = kwargs.get('numpoints', 16)
        self.orientation_sens = kwargs.get('orientation_sensitive', True)

        self.db = {}
        self.points = []

        if points is not None:
            self.points = points

    def add_point(self, p):
        '''Add a point to the unistroke/path. This invalidates all previously
        computed vectors.'''
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
        return self._get_db_key('startvector', numpoints)

    def get_vector(self, numpoints=None):
        return self._get_db_key('vector', numpoints)

    def get_points(self, numpoints=None):
        return self._get_db_key('points', numpoints)

    def prepare(self, numpoints=None):
        '''This function prepares the UnistrokeTemplate for matching given a
        target number of points (for resample). 16 is optimal.'''

        if not self.points:
            raise MultistrokeError('prepare() called without self.points')

        # How many points are we resampling to?
        n = numpoints or self.numpoints
        if not n or n < 2:
            raise MultistrokeError('prepare() called with invalid numpoints')

        p = resample(self.points, n)
        radians = indicative_angle(p)
        p = rotate_by(p, -radians)
        p = scale_dim(p, SQUARESIZE, ONEDTHRESHOLD)

        if self.orientation_sens:
            p = rotate_by(p, +radians)  # restore

        p = translate_to(p, ORIGIN)

        # Now store it using the number of points in the resampled path as the
        # dict key. On the next call to get_*, it will be returned instead of
        # recomputed. Implicitly, you must reset self.db or call prepare() for
        # all the keys once you manipulate self.points.
        self.db[n] = {
            # Compute STARTANGLEINDEX as n/8:
            'startvector': start_unit_vector(p, (n / 8)),
            'vector': vectorize(p, self.orientation_sens)
        }


# -----------------------------------------------------------------------------
# Candidate
# -----------------------------------------------------------------------------

class Candidate(object):
    '''Represents a set of unistroke paths of user input, ie data to be matched
    against a :class:`UnistrokeTemplate` object using the Protractor algorithm.
    By default, data is precomputed to match both rotation bounded and fully
    invariant :class:`UnistrokeTemplate` objects.

    :Arguments:
        `strokes`
            See :data:`MultistrokeGesture.strokes` for format example. The
            Candidate strokes are simply combined to a unistroke in the order
            given. The idea is that this will match one of the unistroke
            permutations in `MultistrokeGesture.templates`.
        `numpoints`
            The Candidate's default N; this is only for a fallback, it is not
            normally used since n is driven by the UnistrokeTemplate we are
            being compared to.
        `skip_bounded`
            If True, do not generate/store rotation bounded vectors
        `skip_invariant`
            If True, do not generate/store rotation invariant vectors

    Note that you WILL get errors if you set a skip-flag and then attempt to
    retrieve the data.'''
    def __init__(self, strokes=None, numpoints=16, **kwargs):
        self.skip_invariant = kwargs.get('skip_invariant', False)
        self.skip_bounded = kwargs.get('skip_bounded', False)

        self.numpoints = numpoints
        self.db = {}
        self.strokes = []

        if strokes is not None:
            self.strokes = strokes

    def add_stroke(self, stroke):
        '''Add a stroke to the candidate; this will invalidate all
        previously computed vectors'''
        self.points.append(stroke)
        self.db = {}

    # Used to lazily prepare the candidate
    def _get_db_key(self, key, numpoints, orientation_sens):
        n = numpoints and numpoints or self.numpoints
        if n not in self.db:
            self.prepare(n)

        prefix = orientation_sens and 'bound_' or 'inv_'
        return self.db[n][prefix + key]

    def get_start_unit_vector(self, numpoints, orientation_sens):
        '''(Internal use only) Get the start vector for this Candidate,
        with the path resampled to `numpoints` points. This is the first
        step in the matching process. It is compared to a
        UnistrokeTemplate object's start vector to determine angle
        similarity.'''
        return self._get_db_key('startvector', numpoints, orientation_sens)

    def get_protractor_vector(self, numpoints, orientation_sens):
        '''(Internal use only) Return vector for comparing to a
        UnistrokeTemplate with Protractor'''
        return self._get_db_key('vector', numpoints, orientation_sens)

    def get_angle_similarity(self, tpl, **kwargs):
        '''(Internal use only) Compute the angle similarity between this
        Candidate and a UnistrokeTemplate object. Returns a number that
        represents the angle similarity (lower is more similar).'''
        n = kwargs.get('numpoints', self.numpoints)

        # angle_between_unit_vectors() inlined here for performance
        v1x, v1y = self.get_start_unit_vector(n, tpl.orientation_sens)
        v2x, v2y = tpl.get_start_unit_vector(n)

        n = (v1x * v2x + v1y * v2y)
        # FIXME: Domain error on float representation of 1.0 (exact match)
        # (see comments in MultistrokeGesture.get_distance())
        if n >= 1:
            return 0.0
        if n <= -1:
            return pi
        return acos(n)

    def prepare(self, numpoints=None):
        '''Prepare the Candidate vectors. self.strokes is combined to a single
        unistroke (connected end-to-end), resampled to :attr:`numpoints`
        points, and then the vectors are calculated and stored in self.db (for
        use by `get_distance` and `get_angle_similarity`)'''
        n = numpoints and numpoints or self.numpoints

        # Inlined combine_strokes() for performance
        points = [i for sub in self.strokes for i in sub]
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
            cand['inv_startvector'] = start_unit_vector(inv_points, angidx)
            cand['inv_vector'] = vectorize(inv_points, False)

        # rotation bounded invariance
        if not self.skip_bounded:
            bound_points = rotate_by(points, +radians)  # restore
            bound_points = translate_to(bound_points, ORIGIN)
            cand['bound_startvector'] = start_unit_vector(bound_points, angidx)
            cand['bound_vector'] = vectorize(bound_points, True)

        self.db[n] = cand


# -----------------------------------------------------------------------------
# Helper functions from this point on. This is all directly related to the
# recognition algorithm, and is almost 100% transcription from the JavaScript
# -----------------------------------------------------------------------------
def resample(points, n):
    # Resample a path to `n` points
    if not len(points) or not n or n < 2:
        raise MultistrokeError('resample() called with invalid arguments')

    interval = path_length(points) / (n - 1)
    D = 0.0
    i = 1
    newpoints = [points[0]]
    workpoints = points[:]
    newpoints_len = 1
    workpoints_len = len(points)

    new_append = newpoints.append
    work_insert = workpoints.insert
    while i < len(workpoints):
        p1 = workpoints[i - 1]
        p2 = workpoints[i]
        d = distance(p1, p2)

        if D + d >= interval:
            qx = p1[0] + ((interval - D) / d) * (p2[0] - p1[0])
            qy = p1[1] + ((interval - D) / d) * (p2[1] - p1[1])
            q = Vector(qx, qy)
            new_append(q)
            work_insert(i, q)  # q is the next i
            newpoints_len += 1
            workpoints_len += 1
            D = 0.0
        else:
            D += d

        i += 1

    # rounding error; insert the last point
    if newpoints_len < n:
        new_append(points[-1])

    return newpoints


def indicative_angle(points):
    cx, cy = centroid(points)
    return atan2(cy - points[0][1], cx - points[0][0])


def rotate_by(points, radians):
    # Rotate points around centroid
    cx, cy = centroid(points)
    cos = math_cos(radians)
    sin = math_sin(radians)
    newpoints = []
    newpoints_append = newpoints.append

    for i in xrange(0, len(points)):
        qx = (points[i][0] - cx) * cos - (points[i][1] - cy) * sin + cx
        qy = (points[i][0] - cx) * sin + (points[i][1] - cy) * cos + cy
        newpoints_append(Vector(qx, qy))

    return newpoints


def scale_dim(points, size, oneDratio):
    bbox_x, bbox_y, bbox_w, bbox_h = bounding_box(points)

    if bbox_h == 0 or bbox_w == 0:
        raise MultistrokeError(
            'scale_dim() called with invalid points: h:{}, w:{}'
            .format(bbox_h, bbox_w))

    # 1D or 2D gesture test
    uniformly = min(bbox_w / bbox_h, bbox_h / bbox_w) <= oneDratio

    if uniformly:
        qx_size = size / max(bbox_w, bbox_h)
        qy_size = size / max(bbox_w, bbox_h)
    else:
        qx_size = size / bbox_w
        qy_size = size / bbox_h

    newpoints = []
    newpoints_append = newpoints.append

    for p in points:
        qx = p[0] * qx_size
        qy = p[1] * qy_size
        newpoints_append(Vector(qx, qy))

    return newpoints


def translate_to(points, pt):
    # Translate points around centroid
    cx, cy = centroid(points)
    ptx, pty = pt
    newpoints = []
    for p in points:
        qx = p[0] + ptx - cx
        qy = p[1] + pty - cy
        newpoints.append(Vector(qx, qy))
    return newpoints


def vectorize(points, use_bounded_rotation_invariance):
    # Helper function for the Protractor algorithm
    cos = 1.0
    sin = 0.0

    if use_bounded_rotation_invariance:
        ang = atan2(points[0][1], points[0][0])
        bo = (pi / 4.) * floor((ang + pi / 8.) / (pi / 4.))
        cos = math_cos(bo - ang)
        sin = math_sin(bo - ang)

    sum = 0.0
    vector = []
    vector_len = 0
    vector_append = vector.append

    for px, py in points:
        newx = px * cos - py * sin
        newy = py * cos + px * sin
        vector_append(newx)
        vector_append(newy)
        vector_len += 2
        sum += newx ** 2 + newy ** 2

    magnitude = sqrt(sum)
    for i in xrange(0, vector_len):
        vector[i] /= magnitude

    return vector


def centroid(points):
    x = 0.0
    y = 0.0
    points_len = len(points)

    for i in xrange(0, points_len):
        x += points[i][0]
        y += points[i][1]

    x /= points_len
    y /= points_len

    return Vector(x, y)


def bounding_box(points):
    minx = float('infinity')
    miny = float('infinity')
    maxx = float('-infinity')
    maxy = float('-infinity')

    for px, py in points:
        if px < minx:
            minx = px
        if px > maxx:
            maxx = px
        if py < miny:
            miny = py
        if py > maxy:
            maxy = py

    return (minx, miny, maxx - minx + 1, maxy - miny + 1)


def path_length(points):
    d = 0.0
    for i in xrange(1, len(points)):
        d += distance(points[i - 1], points[i])
    return d


def distance(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return sqrt(dx ** 2 + dy ** 2)


def start_unit_vector(points, index):
    i = int(index)
    vx, vy = points[i][0] - points[0][0], points[i][1] - points[0][1]
    length = sqrt(vx ** 2 + vy ** 2)
    return Vector(vx / length, vy / length)
