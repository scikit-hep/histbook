#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
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

    def test_bin(self):
        for underflow in False, True:
            for overflow in False, True:
                h = Hist(bin("x", 4, -1, 1, underflow=underflow, overflow=overflow))
                if underflow:
                    self.assertEqual(h.only("x < -1").axis("x"),    bin("x", 0,   -1,   -1, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.only("x < -0.5").axis("x"),  bin("x", 1,   -1, -0.5, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.only("x < 0").axis("x"),     bin("x", 2,   -1,    0, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.only("x < 0.5").axis("x"),   bin("x", 3,   -1,  0.5, underflow=underflow,    overflow=False, nanflow=False))
                self.assertEqual(h.only("x < 1").axis("x"),     bin("x", 4,   -1,    1, underflow=underflow,    overflow=False, nanflow=False))

                self.assertEqual(h.only("x >= -1").axis("x"),   bin("x", 4,   -1,    1,     underflow=False, overflow=overflow, nanflow=False))
                self.assertEqual(h.only("x >= -0.5").axis("x"), bin("x", 3, -0.5,    1,     underflow=False, overflow=overflow, nanflow=False))
                self.assertEqual(h.only("x >= 0").axis("x"),    bin("x", 2,    0,    1,     underflow=False, overflow=overflow, nanflow=False))
                self.assertEqual(h.only("x >= 0.5").axis("x"),  bin("x", 1,  0.5,    1,     underflow=False, overflow=overflow, nanflow=False))
                if overflow:
                    self.assertEqual(h.only("x >= 1").axis("x"),    bin("x", 0,    1,    1,     underflow=False, overflow=overflow, nanflow=False))

                h = Hist(bin("x", 4, -1, 1, underflow=underflow, overflow=overflow, closedlow=False))
                if underflow:
                    self.assertEqual(h.only("x <= -1").axis("x"),   bin("x", 0,   -1,   -1, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x <= -0.5").axis("x"), bin("x", 1,   -1, -0.5, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x <= 0").axis("x"),    bin("x", 2,   -1,    0, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x <= 0.5").axis("x"),  bin("x", 3,   -1,  0.5, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x <= 1").axis("x"),    bin("x", 4,   -1,    1, underflow=underflow,    overflow=False, nanflow=False, closedlow=False))

                self.assertEqual(h.only("x > -1").axis("x"),    bin("x", 4,   -1,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x > -0.5").axis("x"),  bin("x", 3, -0.5,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x > 0").axis("x"),     bin("x", 2,    0,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                self.assertEqual(h.only("x > 0.5").axis("x"),   bin("x", 1,  0.5,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))
                if overflow:
                    self.assertEqual(h.only("x > 1").axis("x"),     bin("x", 0,    1,    1,     underflow=False, overflow=overflow, nanflow=False, closedlow=False))

        h = Hist(bin("x", 4, -1, 1))
        h._content = numpy.arange(1, 14, dtype=numpy.float64).reshape(13, 1)
