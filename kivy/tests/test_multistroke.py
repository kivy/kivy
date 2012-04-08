import unittest
import kivy.multistroke
from kivy.multistroke import GPoint, Recognizer, Multistroke

# Not exactly sure how to switch between them and run tests twice?
PERFECT_INVAR = 67108864  # depends on /.0001**2 on perfect match
PERFECT_BOUND = 1
CANDIDATE_SCORE = 6.175
T_MISS_SCORE = 1.25

best_score = 0.0
counter = 0


def best_score_cb(result):
    global best_score
    best_score = result.best['score']


def counter_cb(result):
    global counter
    counter += 1

# These are taken from the examples in JavaScript code (but made unistrokes)
TGesture = [GPoint(30, 7), GPoint(103, 7), GPoint(66, 7), GPoint(66, 87)]
NGesture = [GPoint(177, 92), GPoint(177, 2), GPoint(182, 1), GPoint(246, 95),
             GPoint(247, 87), GPoint(247, 1)]

# dataset that matches N pretty well
Ncandidate = [
    GPoint(160, 271), GPoint(160, 263), GPoint(158, 257), GPoint(156, 249),
    GPoint(146, 187), GPoint(144, 181), GPoint(144, 175), GPoint(142, 167),
    GPoint(140, 113), GPoint(140, 107), GPoint(140, 103), GPoint(140, 99),
    GPoint(140, 85),  GPoint(138, 85),  GPoint(138, 87),  GPoint(138, 89),
    GPoint(166, 151), GPoint(176, 171), GPoint(188, 189), GPoint(200, 205),
    GPoint(238, 263), GPoint(242, 269), GPoint(244, 273), GPoint(246, 277),
    GPoint(252, 289), GPoint(254, 291), GPoint(256, 291), GPoint(258, 291),
    GPoint(260, 281), GPoint(260, 275), GPoint(260, 267), GPoint(260, 255),
    GPoint(254, 189), GPoint(254, 175), GPoint(254, 161), GPoint(254, 147),
    GPoint(260, 103), GPoint(260, 101), GPoint(260, 99),  GPoint(260, 95),
    GPoint(260, 93),  GPoint(260, 91),  GPoint(260, 89)
]


class MultistrokeTestCase(unittest.TestCase):

    def setUp(self):
        global best_score
        best_score = 0
        counter = 0

        self.Tinvar = Multistroke('T', [TGesture], orientation_dep=False)
        self.Tbound = Multistroke('T', [TGesture], orientation_dep=True)
        self.Ninvar = Multistroke('N', [NGesture], orientation_dep=False)
        self.Nbound = Multistroke('N', [NGesture], orientation_dep=True)

# -----------------------------------------------------------------------------
# Recognizer scheduling
# -----------------------------------------------------------------------------
    def test_immediate(self):
        gdb = Recognizer(db=[self.Tinvar, self.Ninvar])
        r = gdb.recognize([Ncandidate], max_gpf=0, use_protractor=False)
        self.assertEqual(r._match_ops, 4)
        self.assertEqual(r._completed, 2)
        self.assertEqual(r.progress, 1)
        self.assertTrue(r.best['score'] > 0.91 and r.best['score'] < 0.92)

    def test_scheduling(self):
        global best_score
        from kivy.clock import Clock
        gdb = Recognizer(db=[self.Tinvar, self.Ninvar])
        r = gdb.recognize([Ncandidate], max_gpf=1, use_protractor=False)
        r.bind(on_complete=best_score_cb)

        # _recognize_tick is scheduled here; compares to Tinvar
        Clock.tick()
        self.assertEqual(r.progress, .5)
        self.assertEqual(best_score, .0)

        # Now complete the search operation
        Clock.tick()
        self.assertEqual(r.progress, 1)
        self.assertTrue(best_score > 0.91 and best_score < 0.92)

    def test_scheduling_limits(self):
        global best_score
        from kivy.clock import Clock
        gdb = Recognizer(db=[self.Ninvar])
        tpls = len(self.Ninvar.templates)

        best_score = 0
        gdb.db.append(self.Ninvar)
        r = gdb.recognize([Ncandidate], max_gpf=1, use_protractor=False)
        r.bind(on_complete=best_score_cb)
        self.assertEqual(r.progress, 0)
        Clock.tick()
        self.assertEqual(r.progress, 0.5)
        self.assertEqual(best_score, 0)
        Clock.tick()
        self.assertEqual(r.progress, 1)
        self.assertTrue(best_score > 0.91 and best_score < 0.92)

        best_score = 0
        gdb.db.append(self.Ninvar)
        r = gdb.recognize([Ncandidate], max_gpf=1, use_protractor=False)
        r.bind(on_complete=best_score_cb)
        self.assertEqual(r.progress, 0)
        Clock.tick()
        self.assertEqual(r.progress, 1 / 3.)

        Clock.tick()
        self.assertEqual(r.progress, 2 / 3.)
        self.assertEqual(best_score, 0)

        Clock.tick()
        self.assertEqual(r.progress, 1)
        self.assertTrue(best_score > 0.91 and best_score < 0.92)

    def test_parallel_recognize(self):
        global counter
        from kivy.clock import Clock

        counter = 0
        gdb = Recognizer()
        for i in range(9):
            gdb.add_gesture('T', [TGesture], priority=50)
        gdb.add_gesture('N', [NGesture])

        r1 = gdb.recognize([Ncandidate], max_gpf=1, use_protractor=False)
        r1.bind(on_complete=counter_cb)
        Clock.tick()  # first run scheduled here; 9 left

        r2 = gdb.recognize([Ncandidate], max_gpf=1, use_protractor=False)
        r2.bind(on_complete=counter_cb)
        Clock.tick()  # 8 left

        r3 = gdb.recognize([Ncandidate], max_gpf=1, use_protractor=False)
        r3.bind(on_complete=counter_cb)
        Clock.tick()  # 7 left

        # run some immediate searches, should not interfere.
        for i in range(5):
            n = gdb.recognize([TGesture], max_gpf=0, use_protractor=False)
            self.assertEqual(n.best['name'], 'T')
            self.assertTrue(n.best['score'] >= .99)

        for i in range(6):
            Clock.tick()
        self.assertEqual(counter, 0)
        Clock.tick()
        self.assertEqual(counter, 1)
        Clock.tick()
        self.assertEqual(counter, 2)
        Clock.tick()
        self.assertEqual(counter, 3)

    def test_timeout_case_1(self):
        global best_score
        from kivy.clock import Clock
        from time import sleep

        best_score = 0
        gdb = Recognizer(db=[self.Tbound, self.Ninvar])
        r = gdb.recognize([Ncandidate], max_gpf=1, timeout=0.1,
                          use_protractor=False)
        Clock.tick()  # matches Tbound in this tick
        self.assertEqual(best_score, 0)
        sleep(0.11)
        Clock.tick()  # should match Ninv, but times out (got T)
        self.assertEqual(r.status, 'timeout')
        self.assertEqual(r.progress, .5)
        self.assertTrue(r.best['score'] < 0.5)

    def test_timeout_case_2(self):
        global best_score
        from kivy.clock import Clock
        from time import sleep

        best_score = 0
        gdb = Recognizer(db=[self.Tbound, self.Ninvar, self.Tinvar])
        r = gdb.recognize([Ncandidate], max_gpf=1, timeout=0.2,
                          use_protractor=False)

        Clock.tick()  # matches Tbound in this tick
        self.assertEqual(best_score, 0)
        sleep(0.1)
        Clock.tick()  # matches Ninvar in this tick
        sleep(0.1)
        Clock.tick()  # should match Tinvar, but times out
        self.assertEqual(r.status, 'timeout')
        self.assertEqual(r.progress, 2 / 3.)
        self.assertTrue(r.best['score'] >= .91 and r.best['score'] <= .92)

    def test_priority_sorting(self):
        gdb = Recognizer()
        gdb.add_gesture('N', [NGesture], priority=10)
        gdb.add_gesture('T', [TGesture], priority=5)
        r = gdb.recognize([Ncandidate], goodscore=0.01, use_protractor=False,
                          max_gpf=0)
        self.assertEqual(r.best['name'], 'T')

        r = gdb.recognize([Ncandidate], goodscore=0.01, use_protractor=False,
                          force_priority_sort=False, max_gpf=0)
        self.assertEqual(r.best['name'], 'N')

# -----------------------------------------------------------------------------
# Recognizer - filter tests
# -----------------------------------------------------------------------------
    def test_name_filter(self):
        gdb = Recognizer(db=[self.Ninvar, self.Nbound])
        n = gdb.filter()
        self.assertEqual(len(n), 2)
        n = gdb.filter(name='X')
        self.assertEqual(len(n), 0)

    def test_numpoints_filter(self):
        gdb = Recognizer(db=[self.Ninvar, self.Nbound])
        n = gdb.filter(numpoints=100)
        self.assertEqual(len(n), 0)

        gdb.add_gesture('T', [TGesture], numpoints=100)
        n = gdb.filter(numpoints=100)
        self.assertEqual(len(n), 1)
        n = gdb.filter(numpoints=[100, 16])
        self.assertEqual(len(n), 3)

    def test_numstrokes_filter(self):
        gdb = Recognizer(db=[self.Ninvar, self.Nbound])
        n = gdb.filter(numstrokes=2)
        self.assertEqual(len(n), 0)

        gdb.add_gesture('T', [TGesture, TGesture])
        n = gdb.filter(numstrokes=2)
        self.assertEqual(len(n), 1)
        n = gdb.filter(numstrokes=[1, 2])
        self.assertEqual(len(n), 3)

    def test_priority_filter(self):
        gdb = Recognizer(db=[self.Ninvar, self.Nbound])
        n = gdb.filter(priority=50)
        self.assertEqual(len(n), 0)

        gdb.add_gesture('T', [TGesture], priority=51)
        n = gdb.filter(priority=50)
        self.assertEqual(len(n), 0)
        n = gdb.filter(priority=51)
        self.assertEqual(len(n), 1)

        gdb.add_gesture('T', [TGesture], priority=52)
        n = gdb.filter(priority=[0, 51])
        self.assertEqual(len(n), 1)
        n = gdb.filter(priority=[0, 52])
        self.assertEqual(len(n), 2)
        n = gdb.filter(priority=[51, 52])
        self.assertEqual(len(n), 2)
        n = gdb.filter(priority=[52, 53])
        self.assertEqual(len(n), 1)
        n = gdb.filter(priority=[53, 54])
        self.assertEqual(len(n), 0)

    def test_orientation_filter(self):
        gdb = Recognizer(db=[self.Ninvar, self.Nbound])
        n = gdb.filter(orientation_dep=True)
        self.assertEqual(len(n), 1)
        n = gdb.filter(orientation_dep=False)
        self.assertEqual(len(n), 1)
        n = gdb.filter(orientation_dep=None)
        self.assertEqual(len(n), 2)

        gdb.db.append(self.Tinvar)
        n = gdb.filter(orientation_dep=True)
        self.assertEqual(len(n), 1)
        n = gdb.filter(orientation_dep=False)
        self.assertEqual(len(n), 2)
        n = gdb.filter(orientation_dep=None)
        self.assertEqual(len(n), 3)

# -----------------------------------------------------------------------------
# misc tests
# -----------------------------------------------------------------------------
    def test_resample(self):
        r = kivy.multistroke.resample([GPoint(0, 0), GPoint(1, 1)], 11)
        self.assertEqual(len(r), 11)
        self.assertEqual(round(r[9].x, 1), 0.9)

        r = kivy.multistroke.resample(TGesture, 25)
        self.assertEqual(len(r), 25)
        self.assertEqual(round(r[12].x), 81)
        self.assertEqual(r[12].y, 7)
        self.assertEqual(TGesture[3].x, r[24].x)
        self.assertEqual(TGesture[3].y, r[24].y)

    def test_rotateby(self):
        r = kivy.multistroke.rotate_by(NGesture, 24)
        self.assertEqual(round(r[2].x, 1), 158.59999999999999)
        self.assertEqual(round(r[2].y, 1), 54.899999999999999)

    def test_transfer(self):
        gdb1 = Recognizer(db=[self.Ninvar])
        gdb2 = Recognizer()
        gdb1.transfer_gesture(gdb2, name='N')

        r = gdb2.recognize([Ncandidate], use_protractor=False, max_gpf=0)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] > 0.91 and r.best['score'] < 0.92)

    def test_export_import_case_1(self):
        gdb1 = Recognizer(db=[self.Ninvar])
        gdb2 = Recognizer()

        g = gdb1.export_gesture(name='N')
        gdb2.import_gesture(g)

        r = gdb2.recognize([Ncandidate], use_protractor=False, max_gpf=0)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] > 0.91 and r.best['score'] < 0.92)

    def test_export_import_case_2(self):
        from tempfile import mkstemp
        import os
        gdb1 = Recognizer(db=[self.Ninvar, self.Tinvar])
        gdb2 = Recognizer()
        fh, fn = mkstemp()
        os.close(fh)
        g = gdb1.export_gesture(name='N', filename=fn)

        gdb2.import_gesture(filename=fn)
        os.unlink(fn)

        self.assertEqual(len(gdb1.db), 2)
        self.assertEqual(len(gdb2.db), 1)
        r = gdb2.recognize([Ncandidate], use_protractor=False, max_gpf=0)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] > 0.91 and r.best['score'] < 0.92)

# -----------------------------------------------------------------------------
# Test golden section search; note .99 1 etc is safe scoring here
# -----------------------------------------------------------------------------
    def test_phi_invariant(self):
        gdb = Recognizer(db=[self.Tinvar, self.Ninvar])
        r = gdb.recognize([NGesture], orientation_dep=False, max_gpf=0,
                     use_protractor=False)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= .99 and r.best['score'] <= 1)

        r = gdb.recognize([NGesture], orientation_dep=True, max_gpf=0,
                     use_protractor=False)
        self.assertEqual(r.best['name'], None)
        self.assertEqual(r.best['score'], 0)

        r = gdb.recognize([Ncandidate], orientation_dep=False, max_gpf=0,
                     use_protractor=False)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= .91 and r.best['score'] <= .92)

    def test_phi_bound(self):
        gdb = Recognizer(db=[self.Tbound, self.Nbound])
        r = gdb.recognize([NGesture], orientation_dep=True, max_gpf=0,
                     use_protractor=False)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] > .99 and r.best['score'] <= 1)

        r = gdb.recognize([NGesture], orientation_dep=False, max_gpf=0,
                     use_protractor=False)
        self.assertEqual(r.best['name'], None)
        self.assertEqual(r.best['score'], 0)

        r = gdb.recognize([Ncandidate], orientation_dep=True, max_gpf=0,
                     use_protractor=False)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= .91 and r.best['score'] <= .92)

    def test_phi_orientation_filter(self):
        gdb = Recognizer(db=[self.Tbound])

        # We should now be able to match it using None or True filter
        r = gdb.recognize([TGesture], orientation_dep=None, max_gpf=0,
                          use_protractor=False)
        self.assertEqual(r.best['name'], 'T')
        self.assertTrue(r.best['score'] >= 0.99 and r.best['score'] <= 1)

        r = gdb.recognize([TGesture], orientation_dep=True, max_gpf=0,
                          use_protractor=False)
        self.assertEqual(r.best['name'], 'T')
        self.assertTrue(r.best['score'] >= 0.99 and r.best['score'] <= 1)

        # But this should fail:
        r = gdb.recognize([TGesture], orientation_dep=True, max_gpf=0,
                          use_protractor=False)
        self.assertEqual(r.best['name'], None)
        self.assertEqual(r.best['score'], 0)

        # Add the fully rotation invariant gesture:
        gdb.db.append(self.Tinvar)

        r = gdb.recognize([TGesture], orientation_dep=True, max_gpf=0,
                          use_protractor=False)
        self.assertEqual(r.best['name'], 'T')
        self.assertTrue(r.best['score'] >= 0.99 and r.best['score'] <= 1)

        # Verify the match for bounded
        r = gdb.recognize([Ncandidate], orientation_dep=False, max_gpf=0,
                          use_protractor=False)
        self.assertTrue(r.best['score'] < 0.6)

# ------------------------------------------------------------------------
# Test protractor search - .99/1 is not safe
# ------------------------------------------------------------------------
    def test_protractor_invariant(self):
        gdb = Recognizer(db=[self.Tinvar, self.Ninvar])
        r = gdb.recognize([NGesture], orientation_dep=False, max_gpf=0,
                     use_protractor=True)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= PERFECT_INVAR)

        r = gdb.recognize([NGesture], orientation_dep=True, max_gpf=0,
                     use_protractor=True)
        self.assertEqual(r.best['name'], None)
        self.assertEqual(r.best['score'], 0)

        r = gdb.recognize([Ncandidate], orientation_dep=False, max_gpf=0,
                     use_protractor=True)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= CANDIDATE_SCORE)
        self.assertTrue(r.best['score'] <= CANDIDATE_SCORE + 0.1)

    def test_protractor_bound(self):
        gdb = Recognizer(db=[self.Tbound, self.Nbound])
        r = gdb.recognize([NGesture], orientation_dep=True, max_gpf=0,
                     use_protractor=True)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= PERFECT_BOUND)

        r = gdb.recognize([NGesture], orientation_dep=False, max_gpf=0,
                     use_protractor=True)
        self.assertEqual(r.best['name'], None)
        self.assertEqual(r.best['score'], 0)

        r = gdb.recognize([Ncandidate], orientation_dep=True, max_gpf=0,
                     use_protractor=True)
        self.assertEqual(r.best['name'], 'N')
        self.assertTrue(r.best['score'] >= CANDIDATE_SCORE)
        self.assertTrue(r.best['score'] <= CANDIDATE_SCORE + 0.1)

    def test_phi_orientation_filter(self):
        gdb = Recognizer(db=[self.Tbound])

        # We should now be able to match it using None or True filter
        r = gdb.recognize([TGesture], orientation_dep=None, max_gpf=0,
                          use_protractor=True)
        self.assertEqual(r.best['name'], 'T')
        self.assertTrue(r.best['score'] >= PERFECT_BOUND)

        r = gdb.recognize([TGesture], orientation_dep=True, max_gpf=0,
                          use_protractor=True)
        self.assertEqual(r.best['name'], 'T')
        self.assertTrue(r.best['score'] >= PERFECT_BOUND)

        # But this should fail:
        r = gdb.recognize([TGesture], orientation_dep=False, max_gpf=0,
                          use_protractor=True)
        self.assertEqual(r.best['name'], None)
        self.assertEqual(r.best['score'], 0)

        # Add the fully rotation invariant gesture:
        gdb.db.append(self.Tinvar)

        r = gdb.recognize([TGesture], orientation_dep=False, max_gpf=0,
                          use_protractor=True)
        self.assertEqual(r.best['name'], 'T')
        self.assertTrue(r.best['score'] >= PERFECT_BOUND)

        # Verify the match for bounded
        r = gdb.recognize([Ncandidate], orientation_dep=False, max_gpf=0,
                          use_protractor=True)
        self.assertTrue(r.best['score'] <= T_MISS_SCORE)

if __name__ == '__main__':
    unittest.main()
