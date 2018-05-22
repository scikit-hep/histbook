#!/usr/bin/env python

# Copyright (c) 2018, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest

import numpy

from histbook.axis import *
from histbook.hist import *

class TestProj(unittest.TestCase):
    def runTest(self):
        pass

    def test_project_bin(self):
        hxy = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False),
                   bin("y", 2, 0, 2, underflow=False, overflow=False, nanflow=False))
        hx = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False))
        hy = Hist(bin("y", 2, 0, 2, underflow=False, overflow=False, nanflow=False))
        for i in range(1):
            hxy.fill(x=[0], y=[0])
            hx.fill(x=[0], y=[0])
            hy.fill(x=[0], y=[0])
        for i in range(2):
            hxy.fill(x=[0], y=[1])
            hx.fill(x=[0], y=[1])
            hy.fill(x=[0], y=[1])
        for i in range(4):
            hxy.fill(x=[1], y=[0])
            hx.fill(x=[1], y=[0])
            hy.fill(x=[1], y=[0])
        for i in range(8):
            hxy.fill(x=[1], y=[1])
            hx.fill(x=[1], y=[1])
            hy.fill(x=[1], y=[1])
        self.assertEqual(hxy._content.tolist(), [[[1], [2]], [[4], [8]]])
        self.assertEqual(hx._content.tolist(), [[3], [12]])
        self.assertEqual(hxy.project("x")._content.tolist(), [[3], [12]])
        self.assertEqual(hy._content.tolist(), [[5], [10]])
        self.assertEqual(hxy.project("y")._content.tolist(), [[5], [10]])

    def test_project_bin_weight(self):
        hxy = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False),
                   bin("y", 2, 0, 2, underflow=False, overflow=False, nanflow=False), weight="w")
        hx = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False), weight="w")
        hy = Hist(bin("y", 2, 0, 2, underflow=False, overflow=False, nanflow=False), weight="w")
        hxy.fill(x=[0, 0, 1, 1], y=[0, 1, 0, 1], w=[1, 2, 4, 8])
        hx.fill(x=[0, 0, 1, 1], y=[0, 1, 0, 1], w=[1, 2, 4, 8])
        hy.fill(x=[0, 0, 1, 1], y=[0, 1, 0, 1], w=[1, 2, 4, 8])
        self.assertEqual(hxy._content.tolist(), [[[1, 1], [2, 4]], [[4, 16], [8, 64]]])
        self.assertEqual(hx._content.tolist(), [[3, 5], [12, 80]])
        self.assertEqual(hxy.project("x")._content.tolist(), [[3, 5], [12, 80]])
        self.assertEqual(hy._content.tolist(), [[5, 17], [10, 68]])
        self.assertEqual(hxy.project("y")._content.tolist(), [[5, 17], [10, 68]])

    def test_project_bin_profile(self):
        hxy = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False),
                   bin("y", 2, 0, 2, underflow=False, overflow=False, nanflow=False), profile("p"), weight="w")
        hx = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False), profile("p"), weight="w")
        hy = Hist(bin("y", 2, 0, 2, underflow=False, overflow=False, nanflow=False), profile("p"), weight="w")
        hxy.fill(x=[0, 0, 1, 1], y=[0, 1, 0, 1], w=[1, 2, 4, 8], p=[10, 20, 40, 80])
        hx.fill(x=[0, 0, 1, 1], y=[0, 1, 0, 1], w=[1, 2, 4, 8], p=[10, 20, 40, 80])
        hy.fill(x=[0, 0, 1, 1], y=[0, 1, 0, 1], w=[1, 2, 4, 8], p=[10, 20, 40, 80])
        self.assertEqual(hxy._content.tolist(), [[[10, 100, 1, 1], [40, 800, 2, 4]], [[160, 6400, 4, 16], [640, 51200, 8, 64]]])
        self.assertEqual(hx._content.tolist(), [[50, 900, 3, 5], [800, 57600, 12, 80]])
        self.assertEqual(hxy.project("x")._content.tolist(), [[50, 900, 3, 5], [800, 57600, 12, 80]])
        self.assertEqual(hy._content.tolist(), [[170, 6500, 5, 17], [680, 52000, 10, 68]])
        self.assertEqual(hxy.project("y")._content.tolist(), [[170, 6500, 5, 17], [680, 52000, 10, 68]])

    def test_project_groupby(self):
        hcx = Hist(groupby("c"), bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False))
        hcx.fill(c=["one", "one", "one", "one", "two", "two"], x=[0, 1, 0, 1, 0, 1])
        self.assertEqual(set(hcx._content.keys()), set(["one", "two"]))
        self.assertEqual(set(hcx.project("c")._content.keys()), set(["one", "two"]))
        self.assertEqual(hcx.project("c").axis, (groupby("c"),))
        self.assertEqual(hcx.project("c")._content["one"].tolist(), [4])
        self.assertEqual(hcx.project("c")._content["two"].tolist(), [2])
        self.assertEqual(hcx.project("x")._content.tolist(), [[3], [3]])
        self.assertEqual(hcx.project("x").axis, (bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False),))

    def test_project_groupby_groupby(self):
        def tolist(obj):
            if isinstance(obj, dict):
                return dict((n, tolist(x)) for n, x in obj.items())
            else:
                return obj.tolist()

        hcdx = Hist(groupby("c"), groupby("d"), bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False))
        hcdx.fill(c=["one", "one", "two", "two"], d=["uno", "dos", "un", "deux"], x=[0, 1, 0, 1])
        self.assertEqual(tolist(hcdx._content), {"two": {"dos": [[0], [0]], "un": [[1], [0]], "deux": [[0], [1]], "uno": [[0], [0]]}, "one": {"dos": [[0], [1]], "un": [[0], [0]], "deux": [[0], [0]], "uno": [[1], [0]]}})
        self.assertEqual(tolist(hcdx.project("c")._content), {"two": [2], "one": [2]})
        self.assertEqual(tolist(hcdx.project("c", "d").project("c")._content), {"two": [2], "one": [2]})
        self.assertEqual(tolist(hcdx.project("d")._content), {"dos": [1], "un": [1], "deux": [1], "uno": [1]})
        self.assertEqual(tolist(hcdx.project("c", "d").project("d")._content), {"dos": [1], "un": [1], "deux": [1], "uno": [1]})
        self.assertEqual(tolist(hcdx.project("c", "d")._content), {"two": {"dos": [0], "un": [1], "deux": [1], "uno": [0]}, "one": {"dos": [1], "un": [0], "deux": [0], "uno": [1]}})
        self.assertEqual(tolist(hcdx.project("d", "c")._content), {"two": {"dos": [0], "un": [1], "deux": [1], "uno": [0]}, "one": {"dos": [1], "un": [0], "deux": [0], "uno": [1]}})
        self.assertEqual(tolist(hcdx.project("x")._content), [[2], [2]])
        self.assertEqual(tolist(hcdx.project("c", "x").project("x")._content), [[2], [2]])
        self.assertEqual(tolist(hcdx.project("d", "x").project("x")._content), [[2], [2]])

    def test_project_away(self):
        empty = Hist()
        empty.fill(x=[1, 2, 3])
        self.assertEqual(empty._content.tolist(), [1])

        h = Hist(bin("x", 10, 0, 10))
        h.fill(x=[1, 2, 3])
        self.assertEqual(h.project()._content.tolist(), [3])

        empty = Hist(weight="y")
        empty.fill(x=[1, 2, 3], y=[0.1, 0.1, 0.1])
        self.assertEqual(empty._content.tolist(), [0.30000000000000004, 0.030000000000000006])

        h = Hist(bin("x", 10, 0, 10), weight="y")
        h.fill(x=[1, 2, 3], y=[0.1, 0.1, 0.1])
        self.assertEqual(h.project()._content.tolist(), [0.30000000000000004, 0.030000000000000006])

        hc = Hist(groupby("c"))
        hc.fill(c=["one", "one", "two"])
        self.assertEqual(hc.project()._content.tolist(), [3])

    def test_select_bin_axis(self):
        for underflow in False, True:
            for overflow in False, True:
                h = Hist(bin("x", 4, -1, 1, underflow=underflow, overflow=overflow))
                if underflow:
                    self.assertEqual(h.select("x < -1").axis["x"], bin("x", 0,   -1,   -1, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.select("x < -0.5").axis["x"],   bin("x", 1,   -1, -0.5, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.select("x < 0").axis["x"],      bin("x", 2,   -1,    0, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.select("x < 0.5").axis["x"],    bin("x", 3,   -1,  0.5, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.select("x < 1").axis["x"],      bin("x", 4,   -1,    1, underflow=underflow,    overflow=False, nanflow=False))

                self.assertEqual(h.select("x >= -1").axis["x"],    bin("x", 4,   -1,    1,     underflow=False, overflow=overflow, nanflow=False))
                self.assertEqual(h.select("x >= -0.5").axis["x"],  bin("x", 3, -0.5,    1,     underflow=False, overflow=overflow, nanflow=False))
                self.assertEqual(h.select("x >= 0").axis["x"],     bin("x", 2,    0,    1,     underflow=False, overflow=overflow, nanflow=False))
                self.assertEqual(h.select("x >= 0.5").axis["x"],   bin("x", 1,  0.5,    1,     underflow=False, overflow=overflow, nanflow=False))
                if overflow:
                    self.assertEqual(h.select("x >= 1").axis["x"], bin("x", 0,    1,    1,     underflow=False, overflow=overflow, nanflow=False))

                h = Hist(bin("x", 4, -1, 1, underflow=underflow, overflow=overflow, closedlow=False))
                if underflow:
                    self.assertEqual(h.select("x <= -1").axis["x"], bin("x", 0,   -1,   -1, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x <= -0.5").axis["x"],   bin("x", 1,   -1, -0.5, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x <= 0").axis["x"],      bin("x", 2,   -1,    0, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x <= 0.5").axis["x"],    bin("x", 3,   -1,  0.5, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x <= 1").axis["x"],      bin("x", 4,   -1,    1, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))

                self.assertEqual(h.select("x > -1").axis["x"],      bin("x", 4,   -1,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x > -0.5").axis["x"],    bin("x", 3, -0.5,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x > 0").axis["x"],       bin("x", 2,    0,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                self.assertEqual(h.select("x > 0.5").axis["x"],     bin("x", 1,  0.5,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                if overflow:
                    self.assertEqual(h.select("x > 1").axis["x"],   bin("x", 0,    1,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))

    def test_select_bin_content(self):
        for nanflow in False, True:
            h = Hist(bin("x", 4, -1, 1, underflow=True, overflow=True, nanflow=nanflow))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x < -1")._content.tolist(), [[1]])
            self.assertEqual(h.select("x < -0.5")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x < 0")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x < 0.5")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x < 1")._content.tolist(), [[1], [2], [3], [4], [5]])
            self.assertEqual(h.select("x >= -1")._content.tolist(), [[2], [3], [4], [5], [6]])
            self.assertEqual(h.select("x >= -0.5")._content.tolist(), [[3], [4], [5], [6]])
            self.assertEqual(h.select("x >= 0")._content.tolist(), [[4], [5], [6]])
            self.assertEqual(h.select("x >= 0.5")._content.tolist(), [[5], [6]])
            self.assertEqual(h.select("x >= 1")._content.tolist(), [[6]])

            h = Hist(bin("x", 4, -1, 1, underflow=True, overflow=False, nanflow=nanflow))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x < -1")._content.tolist(), [[1]])
            self.assertEqual(h.select("x < -0.5")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x < 0")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x < 0.5")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x < 1")._content.tolist(), [[1], [2], [3], [4], [5]])
            self.assertEqual(h.select("x >= -1")._content.tolist(), [[2], [3], [4], [5]])
            self.assertEqual(h.select("x >= -0.5")._content.tolist(), [[3], [4], [5]])
            self.assertEqual(h.select("x >= 0")._content.tolist(), [[4], [5]])
            self.assertEqual(h.select("x >= 0.5")._content.tolist(), [[5]])

            h = Hist(bin("x", 4, -1, 1, underflow=False, overflow=True, nanflow=nanflow))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x < -0.5")._content.tolist(), [[1]])
            self.assertEqual(h.select("x < 0")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x < 0.5")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x < 1")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x >= -1")._content.tolist(), [[1], [2], [3], [4], [5]])
            self.assertEqual(h.select("x >= -0.5")._content.tolist(), [[2], [3], [4], [5]])
            self.assertEqual(h.select("x >= 0")._content.tolist(), [[3], [4], [5]])
            self.assertEqual(h.select("x >= 0.5")._content.tolist(), [[4], [5]])
            self.assertEqual(h.select("x >= 1")._content.tolist(), [[5]])

            h = Hist(bin("x", 4, -1, 1, underflow=False, overflow=False, nanflow=nanflow))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x < -0.5")._content.tolist(), [[1]])
            self.assertEqual(h.select("x < 0")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x < 0.5")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x < 1")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x >= -1")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x >= -0.5")._content.tolist(), [[2], [3], [4]])
            self.assertEqual(h.select("x >= 0")._content.tolist(), [[3], [4]])
            self.assertEqual(h.select("x >= 0.5")._content.tolist(), [[4]])

        for nanflow in False, True:
            h = Hist(bin("x", 4, -1, 1, underflow=True, overflow=True, nanflow=nanflow, closedlow=False))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x <= -1")._content.tolist(), [[1]])
            self.assertEqual(h.select("x <= -0.5")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x <= 0")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x <= 0.5")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x <= 1")._content.tolist(), [[1], [2], [3], [4], [5]])
            self.assertEqual(h.select("x > -1")._content.tolist(), [[2], [3], [4], [5], [6]])
            self.assertEqual(h.select("x > -0.5")._content.tolist(), [[3], [4], [5], [6]])
            self.assertEqual(h.select("x > 0")._content.tolist(), [[4], [5], [6]])
            self.assertEqual(h.select("x > 0.5")._content.tolist(), [[5], [6]])
            self.assertEqual(h.select("x > 1")._content.tolist(), [[6]])

            h = Hist(bin("x", 4, -1, 1, underflow=True, overflow=False, nanflow=nanflow, closedlow=False))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x <= -1")._content.tolist(), [[1]])
            self.assertEqual(h.select("x <= -0.5")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x <= 0")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x <= 0.5")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x <= 1")._content.tolist(), [[1], [2], [3], [4], [5]])
            self.assertEqual(h.select("x > -1")._content.tolist(), [[2], [3], [4], [5]])
            self.assertEqual(h.select("x > -0.5")._content.tolist(), [[3], [4], [5]])
            self.assertEqual(h.select("x > 0")._content.tolist(), [[4], [5]])
            self.assertEqual(h.select("x > 0.5")._content.tolist(), [[5]])

            h = Hist(bin("x", 4, -1, 1, underflow=False, overflow=True, nanflow=nanflow, closedlow=False))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x <= -0.5")._content.tolist(), [[1]])
            self.assertEqual(h.select("x <= 0")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x <= 0.5")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x <= 1")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x > -1")._content.tolist(), [[1], [2], [3], [4], [5]])
            self.assertEqual(h.select("x > -0.5")._content.tolist(), [[2], [3], [4], [5]])
            self.assertEqual(h.select("x > 0")._content.tolist(), [[3], [4], [5]])
            self.assertEqual(h.select("x > 0.5")._content.tolist(), [[4], [5]])
            self.assertEqual(h.select("x > 1")._content.tolist(), [[5]])

            h = Hist(bin("x", 4, -1, 1, underflow=False, overflow=False, nanflow=nanflow, closedlow=False))
            h._content = numpy.arange(1, h.axis["x"].totbins + 1, dtype=numpy.float64).reshape(h.axis["x"].totbins, 1)
            self.assertEqual(h.select("x <= -0.5")._content.tolist(), [[1]])
            self.assertEqual(h.select("x <= 0")._content.tolist(), [[1], [2]])
            self.assertEqual(h.select("x <= 0.5")._content.tolist(), [[1], [2], [3]])
            self.assertEqual(h.select("x <= 1")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x > -1")._content.tolist(), [[1], [2], [3], [4]])
            self.assertEqual(h.select("x > -0.5")._content.tolist(), [[2], [3], [4]])
            self.assertEqual(h.select("x > 0")._content.tolist(), [[3], [4]])
            self.assertEqual(h.select("x > 0.5")._content.tolist(), [[4]])

    def test_select_bin_bin(self):
        h = Hist(bin("x", 4, -1, 1, underflow=False, overflow=False, nanflow=False), bin("y", 4, -1, 1, underflow=False, overflow=False, nanflow=False))
        h.fill(x=[0], y=[0])
        h.fill(x=[0], y=[0])
        h.fill(x=[0], y=[0])
        h.fill(x=[0], y=[0])
        h.fill(x=[0], y=[0.5])
        h.fill(x=[0], y=[0.5])
        h.fill(x=[0], y=[0.5])
        h.fill(x=[0.5], y=[0])
        h.fill(x=[0.5], y=[0])
        h.fill(x=[0.5], y=[0.5])
        self.assertEqual(h._content.tolist(), [[[0], [0], [0], [0]], [[0], [0], [0], [0]], [[0], [0], [4], [3]], [[0], [0], [2], [1]]])
        self.assertEqual(h.select("x >= 0")._content.tolist(), [[[0], [0], [4], [3]], [[0], [0], [2], [1]]])
        self.assertEqual(h.select("y >= 0")._content.tolist(), [[[0], [0]], [[0], [0]], [[4], [3]], [[2], [1]]])
        self.assertEqual(h.select("x >= 0 and y >= 0")._content.tolist(), [[[4], [3]], [[2], [1]]])
        self.assertEqual(h.select("x >= 0").select("y >= 0")._content.tolist(), [[[4], [3]], [[2], [1]]])

    def test_select_intbin(self):
        h = Hist(intbin("x", 5, 10))
        h.fill(x=range(15))
        self.assertEqual(h._content.tolist(), [[5], [1], [1], [1], [1], [1], [1], [4]])
        self.assertEqual(h.select("x < 6").axis["x"], intbin("x", 5, 5, overflow=False))
        self.assertEqual(h.select("x < 6")._content.tolist(), [[5], [1]])
        self.assertEqual(h.select("x <= 6").axis["x"], intbin("x", 5, 6, overflow=False))
        self.assertEqual(h.select("x <= 6")._content.tolist(), [[5], [1], [1]])
        self.assertEqual(h.select("x > 9").axis["x"], intbin("x", 10, 10, underflow=False))
        self.assertEqual(h.select("x > 9")._content.tolist(), [[1], [4]])
        self.assertEqual(h.select("x >= 9").axis["x"], intbin("x", 9, 10, underflow=False))
        self.assertEqual(h.select("x >= 9")._content.tolist(), [[1], [1], [4]])

        h = Hist(intbin("x", 5, 10, underflow=False, overflow=False))
        h.fill(x=range(15))
        self.assertEqual(h._content.tolist(), [[1], [1], [1], [1], [1], [1]])
        self.assertEqual(h.select("x < 6").axis["x"], intbin("x", 5, 5, underflow=False, overflow=False))
        self.assertEqual(h.select("x < 6")._content.tolist(), [[1]])
        self.assertEqual(h.select("x <= 6").axis["x"], intbin("x", 5, 6, underflow=False, overflow=False))
        self.assertEqual(h.select("x <= 6")._content.tolist(), [[1], [1]])
        self.assertEqual(h.select("x > 9").axis["x"], intbin("x", 10, 10, underflow=False, overflow=False))
        self.assertEqual(h.select("x > 9")._content.tolist(), [[1]])
        self.assertEqual(h.select("x >= 9").axis["x"], intbin("x", 9, 10, underflow=False, overflow=False))
        self.assertEqual(h.select("x >= 9")._content.tolist(), [[1], [1]])

    def test_select_split(self):
        h = Hist(split("x", (0, 1), underflow=True, overflow=True, closedlow=True))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[1], [2], [3], [4]])
        self.assertEqual(h.select("x < 0").axis["x"], split("x", 0, underflow=True, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x < 1").axis["x"], split("x", (0, 1), underflow=True, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x < 0")._content.tolist(), [[1]])
        self.assertEqual(h.select("x < 1")._content.tolist(), [[1], [2]])
        self.assertEqual(h.select("x >= 1").axis["x"], split("x", 1, underflow=False, overflow=True, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x >= 0").axis["x"], split("x", (0, 1), underflow=False, overflow=True, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x >= 1")._content.tolist(), [[3]])
        self.assertEqual(h.select("x >= 0")._content.tolist(), [[2], [3]])

        h = Hist(split("x", (0, 1), underflow=False, overflow=True, closedlow=True))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[2], [3], [4]])
        self.assertEqual(h.select("x < 1").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x < 1")._content.tolist(), [[2]])
        self.assertEqual(h.select("x >= 1").axis["x"], split("x", 1, underflow=False, overflow=True, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x >= 0").axis["x"], split("x", (0, 1), underflow=False, overflow=True, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x >= 1")._content.tolist(), [[3]])
        self.assertEqual(h.select("x >= 0")._content.tolist(), [[2], [3]])

        h = Hist(split("x", (0, 1), underflow=True, overflow=False, closedlow=True))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[1], [2], [4]])
        self.assertEqual(h.select("x < 0").axis["x"], split("x", 0, underflow=True, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x < 1").axis["x"], split("x", (0, 1), underflow=True, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x < 0")._content.tolist(), [[1]])
        self.assertEqual(h.select("x < 1")._content.tolist(), [[1], [2]])
        self.assertEqual(h.select("x >= 0").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x >= 0")._content.tolist(), [[2]])

        h = Hist(split("x", (0, 1), underflow=False, overflow=False, closedlow=True))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[2], [4]])
        self.assertEqual(h.select("x < 1").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x < 1")._content.tolist(), [[2]])
        self.assertEqual(h.select("x >= 0").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=True))
        self.assertEqual(h.select("x >= 0")._content.tolist(), [[2]])

        h = Hist(split("x", (0, 1), underflow=True, overflow=True, closedlow=False))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[1], [2], [3], [4]])
        self.assertEqual(h.select("x <= 0").axis["x"], split("x", 0, underflow=True, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x <= 1").axis["x"], split("x", (0, 1), underflow=True, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x <= 0")._content.tolist(), [[1]])
        self.assertEqual(h.select("x <= 1")._content.tolist(), [[1], [2]])
        self.assertEqual(h.select("x > 1").axis["x"], split("x", 1, underflow=False, overflow=True, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x > 0").axis["x"], split("x", (0, 1), underflow=False, overflow=True, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x > 1")._content.tolist(), [[3]])
        self.assertEqual(h.select("x > 0")._content.tolist(), [[2], [3]])

        h = Hist(split("x", (0, 1), underflow=False, overflow=True, closedlow=False))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[2], [3], [4]])
        self.assertEqual(h.select("x <= 1").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x <= 1")._content.tolist(), [[2]])
        self.assertEqual(h.select("x > 1").axis["x"], split("x", 1, underflow=False, overflow=True, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x > 0").axis["x"], split("x", (0, 1), underflow=False, overflow=True, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x > 1")._content.tolist(), [[3]])
        self.assertEqual(h.select("x > 0")._content.tolist(), [[2], [3]])

        h = Hist(split("x", (0, 1), underflow=True, overflow=False, closedlow=False))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[1], [2], [4]])
        self.assertEqual(h.select("x <= 0").axis["x"], split("x", 0, underflow=True, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x <= 1").axis["x"], split("x", (0, 1), underflow=True, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x <= 0")._content.tolist(), [[1]])
        self.assertEqual(h.select("x <= 1")._content.tolist(), [[1], [2]])
        self.assertEqual(h.select("x > 0").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x > 0")._content.tolist(), [[2]])

        h = Hist(split("x", (0, 1), underflow=False, overflow=False, closedlow=False))
        h.fill(x=[-1, 0.5, 0.5, 2, 2, 2, numpy.nan, numpy.nan, numpy.nan, numpy.nan])
        self.assertEqual(h._content.tolist(), [[2], [4]])
        self.assertEqual(h.select("x <= 1").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x <= 1")._content.tolist(), [[2]])
        self.assertEqual(h.select("x > 0").axis["x"], split("x", (0, 1), underflow=False, overflow=False, nanflow=False, closedlow=False))
        self.assertEqual(h.select("x > 0")._content.tolist(), [[2]])

    def test_select_cut(self):
        h = Hist(cut("p"))
        h.fill(p=[True, True, False])
        self.assertEqual(h._content.tolist(), [[1], [2]])
        self.assertEqual(h.select("p")._content.tolist(), [2])
        self.assertEqual(h.select("not p")._content.tolist(), [1])
        self.assertEqual(h.select("p")._fixed, ())
        self.assertEqual(h.select("p")._shape, (1,))
        self.assertEqual(h.select("not p")._fixed, ())
        self.assertEqual(h.select("not p")._shape, (1,))

        h = Hist(cut("x > 5"))
        h.fill(x=[8, 7, 3])
        self.assertEqual(h._content.tolist(), [[1], [2]])
        self.assertEqual(h.select("x > 5")._content.tolist(), [2])

    def test_select_groupby(self):
        h = Hist(groupby("c"))
        h.fill(c=["one", "two", "three", "two", "three", "three"])
        self.assertEqual(set(h.select("c == 'two'")._content.keys()), set(["two"]))
        self.assertEqual(set(h.select("c in {'two', 'three'}")._content.keys()), set(["two", "three"]))
        self.assertEqual(set(h.select("c > 'one'")._content.keys()), set(["two", "three"]))  # (alphabetically)
        self.assertEqual(set(h.select("c != 'two'")._content.keys()), set(["one", "three"]))
        self.assertEqual(set(h.select("not c == 'two'")._content.keys()), set(["one", "three"]))
        self.assertEqual(set(h.select("c != 'two' and c != 'three'")._content.keys()), set(["one"]))
        self.assertEqual(set(h.select("c == 'two' or c == 'three'")._content.keys()), set(["two", "three"]))

        h = Hist(groupby("c"), bin("x", 4, -1, 1, underflow=False, overflow=False, nanflow=False))
        h.fill(c=["one", "two", "three", "two", "three", "three"], x=[0, 0, 0, 0, 0, 0])
        self.assertEqual(h.select("c == 'two'")._content["two"].tolist(), [[0], [0], [2], [0]])
        self.assertEqual(h.select("c == 'two' and x >= 0")._content["two"].tolist(), [[2], [0]])
        self.assertEqual(h.select("x >= 0 and c == 'two'")._content["two"].tolist(), [[2], [0]])

    def test_select_groupbin(self):
        h = Hist(groupbin("x", 10))
        h.fill(x=[10, 15, 18, 20, 25])
        self.assertEqual(set(h._content.keys()), set([10.0, 20.0]))
        self.assertEqual(h._content[10.0].tolist(), [3])
        self.assertEqual(h._content[20.0].tolist(), [2])
        self.assertEqual(set(h.select("x < 20")._content.keys()), set([10.0]))
        self.assertEqual(h.select("x < 20")._content[10.0].tolist(), [3])
        self.assertEqual(h.select("not x >= 20")._content[10.0].tolist(), [3])

        h = Hist(groupbin("x", 10, closedlow=False))
        h.fill(x=[10, 15, 18, 20, 25])
        self.assertEqual(set(h._content.keys()), set([0.0, 10.0, 20.0]))
        self.assertEqual(h._content[0.0].tolist(), [1])
        self.assertEqual(h._content[10.0].tolist(), [3])
        self.assertEqual(h._content[20.0].tolist(), [1])
        self.assertEqual(set(h.select("x <= 20")._content.keys()), set([0.0, 10.0]))
        self.assertEqual(h.select("x <= 20")._content[0.0].tolist(), [1])
        self.assertEqual(h.select("x <= 20")._content[10.0].tolist(), [3])
        self.assertEqual(h.select("not x > 20")._content[10.0].tolist(), [3])

        h = Hist(groupbin("x", 10))
        h.fill(x=[15, 25, 25, 35, 35, 35])
        self.assertEqual(set(h._content.keys()), set([10.0, 20.0, 30.0]))
        self.assertEqual(set(h.select("x < 20 or x >= 30")._content.keys()), set([10.0, 30.0]))

    def test_rebin_split(self):
        h = Hist(split("x", (1, 2, 3)))
        h.fill(x=[0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)
        self.assertEqual(h._content.tolist(), [[1], [2], [4], [8], [16]])

        h2 = h.rebin("x", (2, 3))
        self.assertEqual(h2._content.tolist(), [[3], [4], [8], [16]])

        h3 = h.rebin("x", (1, 3))
        self.assertEqual(h3._content.tolist(), [[1], [6], [8], [16]])

        h4 = h.rebin("x", (1, 2))
        self.assertEqual(h4._content.tolist(), [[1], [2], [12], [16]])

        h5 = h.rebin("x", (1,))
        self.assertEqual(h5._content.tolist(), [[1], [14], [16]])

        h6 = h.rebin("x", (2,))
        self.assertEqual(h6._content.tolist(), [[3], [12], [16]])

        h7 = h.rebin("x", (3,))
        self.assertEqual(h7._content.tolist(), [[7], [8], [16]])

        h = Hist(split("x", (1, 2, 3), underflow=False, overflow=True))
        h.fill(x=[0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)
        self.assertEqual(h._content.tolist(), [[2], [4], [8], [16]])

        h2 = h.rebin("x", (2, 3))
        self.assertEqual(h2._content.tolist(), [[4], [8], [16]])

        h3 = h.rebin("x", (1, 3))
        self.assertEqual(h3._content.tolist(), [[6], [8], [16]])

        h4 = h.rebin("x", (1, 2))
        self.assertEqual(h4._content.tolist(), [[2], [12], [16]])

        h5 = h.rebin("x", (1,))
        self.assertEqual(h5._content.tolist(), [[14], [16]])

        h6 = h.rebin("x", (2,))
        self.assertEqual(h6._content.tolist(), [[12], [16]])

        h7 = h.rebin("x", (3,))
        self.assertEqual(h7._content.tolist(), [[8], [16]])

        h = Hist(split("x", (1, 2, 3), underflow=True, overflow=False))
        h.fill(x=[0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)
        self.assertEqual(h._content.tolist(), [[1], [2], [4], [16]])

        h2 = h.rebin("x", (2, 3))
        self.assertEqual(h2._content.tolist(), [[3], [4], [16]])

        h3 = h.rebin("x", (1, 3))
        self.assertEqual(h3._content.tolist(), [[1], [6], [16]])

        h4 = h.rebin("x", (1, 2))
        self.assertEqual(h4._content.tolist(), [[1], [2], [16]])

        h5 = h.rebin("x", (1,))
        self.assertEqual(h5._content.tolist(), [[1], [16]])

        h6 = h.rebin("x", (2,))
        self.assertEqual(h6._content.tolist(), [[3], [16]])

        h7 = h.rebin("x", (3,))
        self.assertEqual(h7._content.tolist(), [[7], [16]])

        h = Hist(split("x", (1, 2, 3), underflow=False, overflow=False))
        h.fill(x=[0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)
        self.assertEqual(h._content.tolist(), [[2], [4], [16]])

        h2 = h.rebin("x", (2, 3))
        self.assertEqual(h2._content.tolist(), [[4], [16]])

        h3 = h.rebin("x", (1, 3))
        self.assertEqual(h3._content.tolist(), [[6], [16]])

        h4 = h.rebin("x", (1, 2))
        self.assertEqual(h4._content.tolist(), [[2], [16]])

        h5 = h.rebin("x", (1,))
        self.assertEqual(h5._content.tolist(), [[16]])

        h6 = h.rebin("x", (2,))
        self.assertEqual(h6._content.tolist(), [[16]])

        h7 = h.rebin("x", (3,))
        self.assertEqual(h7._content.tolist(), [[16]])

    def test_rebin_split_bin(self):
        h = Hist(bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False), split("y", (1, 2, 3)))
        h.fill(x=[0]*(1+2+4+8+16) + [1]*(1+2+4+8+16), y=([0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)*2)
        self.assertEqual(h._content.tolist(), [[[1], [2], [4], [8], [16]], [[1], [2], [4], [8], [16]]])

        h2 = h.rebin("y", (2, 3))
        self.assertEqual(h2._content.tolist(), [[[3], [4], [8], [16]], [[3], [4], [8], [16]]])

        h3 = h.rebin("y", (1, 3))
        self.assertEqual(h3._content.tolist(), [[[1], [6], [8], [16]], [[1], [6], [8], [16]]])

        h4 = h.rebin("y", (1, 2))
        self.assertEqual(h4._content.tolist(), [[[1], [2], [12], [16]], [[1], [2], [12], [16]]])

        h5 = h.rebin("y", (1,))
        self.assertEqual(h5._content.tolist(), [[[1], [14], [16]], [[1], [14], [16]]])

        h6 = h.rebin("y", (2,))
        self.assertEqual(h6._content.tolist(), [[[3], [12], [16]], [[3], [12], [16]]])

        h7 = h.rebin("y", (3,))
        self.assertEqual(h7._content.tolist(), [[[7], [8], [16]], [[7], [8], [16]]])

        h = Hist(split("y", (1, 2, 3)), bin("x", 2, 0, 2, underflow=False, overflow=False, nanflow=False))
        h.fill(x=[0]*(1+2+4+8+16) + [1]*(1+2+4+8+16), y=([0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)*2)
        self.assertEqual(h._content.tolist(), [[[1], [1]], [[2], [2]], [[4], [4]], [[8], [8]], [[16], [16]]])

        h2 = h.rebin("y", (2, 3))
        self.assertEqual(h2._content.tolist(), [[[3], [3]], [[4], [4]], [[8], [8]], [[16], [16]]])

        h3 = h.rebin("y", (1, 3))
        self.assertEqual(h3._content.tolist(), [[[1], [1]], [[6], [6]], [[8], [8]], [[16], [16]]])

        h4 = h.rebin("y", (1, 2))
        self.assertEqual(h4._content.tolist(), [[[1], [1]], [[2], [2]], [[12], [12]], [[16], [16]]])

        h5 = h.rebin("y", (1,))
        self.assertEqual(h5._content.tolist(), [[[1], [1]], [[14], [14]], [[16], [16]]])

        h6 = h.rebin("y", (2,))
        self.assertEqual(h6._content.tolist(), [[[3], [3]], [[12], [12]], [[16], [16]]])

        h7 = h.rebin("y", (3,))
        self.assertEqual(h7._content.tolist(), [[[7], [7]], [[8], [8]], [[16], [16]]])

    def test_rebin_split_groupby(self):
        def tolist(obj):
            if isinstance(obj, dict):
                return dict((n, tolist(x)) for n, x in obj.items())
            else:
                return obj.tolist()

        h = Hist(groupby("c"), split("x", (1, 2, 3)))
        h.fill(c=["one"]*(1+2+4+8+16) + ["two"]*(1+2+4+8+16), x=([0] + [1]*2 + [2]*4 + [3]*8 + [numpy.nan]*16)*2)
        self.assertEqual(tolist(h._content), {"one": [[1], [2], [4], [8], [16]], "two": [[1], [2], [4], [8], [16]]})

        h2 = h.rebin("x", (2, 3))
        self.assertEqual(tolist(h2._content), {"one": [[3], [4], [8], [16]], "two": [[3], [4], [8], [16]]})

        h3 = h.rebin("x", (1, 3))
        self.assertEqual(tolist(h3._content), {"one": [[1], [6], [8], [16]], "two": [[1], [6], [8], [16]]})

        h4 = h.rebin("x", (1, 2))
        self.assertEqual(tolist(h4._content), {"one": [[1], [2], [12], [16]], "two": [[1], [2], [12], [16]]})

        h5 = h.rebin("x", (1,))
        self.assertEqual(tolist(h5._content), {"one": [[1], [14], [16]], "two": [[1], [14], [16]]})

        h6 = h.rebin("x", (2,))
        self.assertEqual(tolist(h6._content), {"one": [[3], [12], [16]], "two": [[3], [12], [16]]})

        h7 = h.rebin("x", (3,))
        self.assertEqual(tolist(h7._content), {"one": [[7], [8], [16]], "two": [[7], [8], [16]]})
