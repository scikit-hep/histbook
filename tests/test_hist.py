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

class TestHist(unittest.TestCase):
    def runTest(self):
        pass

    def test_calc(self):
        h = Hist(bin("x + 0.1", 10, 0, 1))
        h.fill(x=[0.4, 0.3, 0.3, 0.5, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[0], [0], [0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [0]])

    def test_defs(self):
        h = Hist(bin("y", 10, 0, 1), defs={"y": "x + 0.1"})
        h.fill(x=[0.4, 0.3, 0.3, 0.5, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[0], [0], [0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [0]])

    def test_nofixed(self):
        h = Hist(groupby("c"))
        h.fill(c=["one", "two", "one", "one", "one"])
        self.assertEqual(h._content["one"].tolist(), [4])
        self.assertEqual(h._content["two"].tolist(), [1])

        h = Hist(groupby("c"), profile("x"))
        h.fill(c=["one", "two", "one", "one", "one"], x=[3, 2, 3, 5, 5])
        self.assertEqual(h._content["one"].tolist(), [16, 68, 4])
        self.assertEqual(h._content["two"].tolist(), [2, 4, 1])

        h = Hist(profile("x"))
        h.fill(x=[3, 3, 5, 5])
        self.assertEqual(h._content.tolist(), [16, 68, 4])

        h = Hist(weight="x")
        h.fill(x=[3, 3, 5, 5])
        self.assertEqual(h._content.tolist(), [16, 68])

        h = Hist(profile("y"), weight="x")
        h.fill(x=[2], y=[3])
        self.assertEqual(h._content.tolist(), [6, 18, 2, 4])

        h = Hist(bin("y", 1, -100, 100, underflow=False, overflow=False, nanflow=False), profile("y"), weight="x")
        h.fill(x=[2], y=[3])
        self.assertEqual(h._content.tolist(), [[6, 18, 2, 4]])

    def test_bin(self):
        h = Hist(bin("x", 10, 10, 11))
        h.fill(x=[10.4, 10.3, 10.3, 10.5, 10.4, 10.8])
        self.assertEqual(h._content.tolist(), [[0], [0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [0], [0]])

        h = Hist(bin("x", 10, 0, 1))
        h.fill(x=[0.4, 0.3, 123, 99, 0.3, numpy.nan, numpy.nan, numpy.nan, 0.5, -99, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[1], [0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [2], [3]])

        h = Hist(bin("x", 10, 0, 1, underflow=False))
        h.fill(x=[0.4, 0.3, 123, 99, 0.3, numpy.nan, numpy.nan, numpy.nan, 0.5, -99, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [2], [3]])

        h = Hist(bin("x", 10, 0, 1, overflow=False))
        h.fill(x=[0.4, 0.3, 123, 99, 0.3, numpy.nan, numpy.nan, numpy.nan, 0.5, -99, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[1], [0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [3]])

        h = Hist(bin("x", 10, 0, 1, nanflow=False))
        h.fill(x=[0.4, 0.3, 123, 99, 0.3, numpy.nan, numpy.nan, numpy.nan, 0.5, -99, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[1], [0], [0], [0], [2], [2], [1], [0], [0], [1], [0], [2]])

        h = Hist(bin("x", 10, 0, 1, underflow=False, overflow=False, nanflow=False))
        h.fill(x=[0.4, 0.3, 123, 99, 0.3, numpy.nan, numpy.nan, numpy.nan, 0.5, -99, 0.4, 0.8])
        self.assertEqual(h._content.tolist(), [[0], [0], [0], [2], [2], [1], [0], [0], [1], [0]])

        h = Hist(bin("x", 2, 0, 2))
        h.fill(x=[0.0, 0.0001, 0.0001, 0.5, 0.5, 0.5, 0.9999, 0.9999, 0.9999, 0.9999, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0001, 1.0001, 1.0001, 1.0001, 1.0001, 1.0001, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001])
        self.assertEqual(h._content.tolist(), [[0], [1 + 2 + 3 + 4], [5 + 6 + 7 + 8], [9 + 10], [0]])

        h = Hist(bin("x", 2, 0, 2, closedlow=False))
        h.fill(x=[0.0, 0.0001, 0.0001, 0.5, 0.5, 0.5, 0.9999, 0.9999, 0.9999, 0.9999, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0001, 1.0001, 1.0001, 1.0001, 1.0001, 1.0001, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 1.9999, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001, 2.0001])
        self.assertEqual(h._content.tolist(), [[1], [2 + 3 + 4 + 5], [6 + 7 + 8 + 9], [10], [0]])

    def test_bin_bin(self):
        h = Hist(bin("x", 3, 0, 3, underflow=False, overflow=False, nanflow=False), bin("y", 5, 0, 5, underflow=False, overflow=False, nanflow=False))
        h.fill(x=[1], y=[3])
        self.assertEqual(h._content.tolist(), [[[0], [0], [0], [0], [0]], [[0], [0], [0], [1], [0]], [[0], [0], [0], [0], [0]]])

    def test_bin_weight(self):
        h = Hist(bin("x", 10, 10, 11), weight="y")
        h.fill(x=[10.4, 10.3, 10.3, 10.5, 10.4, 10.8], y=[0.1, 0.1, 0.1, 0.1, 0.1, 1.0])
        self.assertEqual(h._content.tolist(), [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.2, 0.020000000000000004], [0.2, 0.020000000000000004], [0.1, 0.010000000000000002], [0.0, 0.0], [0.0, 0.0], [1.0, 1.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])

        h = Hist(bin("x", 10, 10, 11)).weight("y")
        h.fill(x=[10.4, 10.3, 10.3, 10.5, 10.4, 10.8], y=[0.1, 0.1, 0.1, 0.1, 0.1, 1.0])
        self.assertEqual(h._content.tolist(), [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.2, 0.020000000000000004], [0.2, 0.020000000000000004], [0.1, 0.010000000000000002], [0.0, 0.0], [0.0, 0.0], [1.0, 1.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])

    def test_bin_big(self):
        numpy.random.seed(12345)
        xdata = numpy.round(numpy.random.normal(0, 1, 10000), 2)
        weights = numpy.random.uniform(-2, 2, 10000)
        both = numpy.random.randint(0, 9999, 10)
        xdata[numpy.random.randint(0, 9999, 10)] = numpy.nan
        weights[numpy.random.randint(0, 9999, 10)] = numpy.nan
        xdata[both] = numpy.nan
        weights[both] = numpy.nan

        nn = ~numpy.isnan(xdata)
        nnweights = weights.copy()
        nnweights[numpy.isnan(weights)] = 0.0
        nnweights2 = nnweights**2
        
        with numpy.errstate(invalid="ignore"):
            under = numpy.count_nonzero(xdata < 0.0)
            bin0 = numpy.count_nonzero(numpy.logical_and(0.0 <= xdata, xdata < 0.1))
            bin1 = numpy.count_nonzero(numpy.logical_and(0.1 <= xdata, xdata < 0.2))
            bin2 = numpy.count_nonzero(numpy.logical_and(0.2 <= xdata, xdata < 0.3))
            bin3 = numpy.count_nonzero(numpy.logical_and(0.3 <= xdata, xdata < 0.4))
            bin4 = numpy.count_nonzero(numpy.logical_and(0.4 <= xdata, xdata < 0.5))
            bin5 = numpy.count_nonzero(numpy.logical_and(0.5 <= xdata, xdata < 0.6))
            bin6 = numpy.count_nonzero(numpy.logical_and(0.6 <= xdata, xdata < 0.7))
            bin7 = numpy.count_nonzero(numpy.logical_and(0.7 <= xdata, xdata < 0.8))
            bin8 = numpy.count_nonzero(numpy.logical_and(0.8 <= xdata, xdata < 0.9))
            bin9 = numpy.count_nonzero(numpy.logical_and(0.9 <= xdata, xdata < 1.0))
            over = numpy.count_nonzero(xdata >= 1.0)
            nan = numpy.count_nonzero(numpy.isnan(xdata))

            wunder = numpy.sum(nnweights * numpy.logical_and(nn, xdata < 0.0))
            wbin0 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.0 <= xdata, xdata < 0.1)))
            wbin1 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.1 <= xdata, xdata < 0.2)))
            wbin2 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.2 <= xdata, xdata < 0.3)))
            wbin3 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.3 <= xdata, xdata < 0.4)))
            wbin4 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.4 <= xdata, xdata < 0.5)))
            wbin5 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.5 <= xdata, xdata < 0.6)))
            wbin6 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.6 <= xdata, xdata < 0.7)))
            wbin7 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.7 <= xdata, xdata < 0.8)))
            wbin8 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.8 <= xdata, xdata < 0.9)))
            wbin9 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.9 <= xdata, xdata < 1.0)))
            wover = numpy.sum(nnweights * numpy.logical_and(nn, (xdata >= 1.0)))
            wnan = numpy.sum(nnweights * numpy.isnan(xdata))

            w2under = numpy.sum(nnweights2 * numpy.logical_and(nn, (xdata < 0.0)))
            w2bin0 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.0 <= xdata, xdata < 0.1)))
            w2bin1 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.1 <= xdata, xdata < 0.2)))
            w2bin2 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.2 <= xdata, xdata < 0.3)))
            w2bin3 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.3 <= xdata, xdata < 0.4)))
            w2bin4 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.4 <= xdata, xdata < 0.5)))
            w2bin5 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.5 <= xdata, xdata < 0.6)))
            w2bin6 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.6 <= xdata, xdata < 0.7)))
            w2bin7 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.7 <= xdata, xdata < 0.8)))
            w2bin8 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.8 <= xdata, xdata < 0.9)))
            w2bin9 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.9 <= xdata, xdata < 1.0)))
            w2over = numpy.sum(nnweights2 * numpy.logical_and(nn, (xdata >= 1.0)))
            w2nan = numpy.sum(nnweights2 * numpy.isnan(xdata))

        for underflow in False, True:
            for overflow in False, True:
                for nanflow in False, True:
                    compare = [bin0, bin1, bin2, bin3, bin4, bin5, bin6, bin7, bin8, bin9]
                    if underflow:
                        compare.insert(0, under)
                    if overflow:
                        compare.append(over)
                    if nanflow:
                        compare.append(nan)
                    # h = Hist(bin("x", 10, 0, 1, underflow=underflow, overflow=overflow, nanflow=nanflow))
                    # h.fill(x=xdata)
                    # self.assertEqual(h._content.reshape(-1).tolist(), compare)

                    compare = [[wbin0, w2bin0], [wbin1, w2bin1], [wbin2, w2bin2], [wbin3, w2bin3], [wbin4, w2bin4], [wbin5, w2bin5], [wbin6, w2bin6], [wbin7, w2bin7], [wbin8, w2bin8], [wbin9, w2bin9]]
                    if underflow:
                        compare.insert(0, [wunder, w2under])
                    if overflow:
                        compare.append([wover, w2over])
                    if nanflow:
                        compare.append([wnan, w2nan])
                    h = Hist(bin("x", 10, 0, 1, underflow=underflow, overflow=overflow, nanflow=nanflow)).weight("w")
                    h.fill(x=xdata, w=weights)
                    self.assertTrue(numpy.absolute((h._content - numpy.array(compare)).reshape(-1)).max() < 1e-10)

        with numpy.errstate(invalid="ignore"):
            under = numpy.count_nonzero(xdata <= 0.0)
            bin0 = numpy.count_nonzero(numpy.logical_and(0.0 < xdata, xdata <= 0.1))
            bin1 = numpy.count_nonzero(numpy.logical_and(0.1 < xdata, xdata <= 0.2))
            bin2 = numpy.count_nonzero(numpy.logical_and(0.2 < xdata, xdata <= 0.3))
            bin3 = numpy.count_nonzero(numpy.logical_and(0.3 < xdata, xdata <= 0.4))
            bin4 = numpy.count_nonzero(numpy.logical_and(0.4 < xdata, xdata <= 0.5))
            bin5 = numpy.count_nonzero(numpy.logical_and(0.5 < xdata, xdata <= 0.6))
            bin6 = numpy.count_nonzero(numpy.logical_and(0.6 < xdata, xdata <= 0.7))
            bin7 = numpy.count_nonzero(numpy.logical_and(0.7 < xdata, xdata <= 0.8))
            bin8 = numpy.count_nonzero(numpy.logical_and(0.8 < xdata, xdata <= 0.9))
            bin9 = numpy.count_nonzero(numpy.logical_and(0.9 < xdata, xdata <= 1.0))
            over = numpy.count_nonzero(xdata > 1.0)
            nan = numpy.count_nonzero(numpy.isnan(xdata))

            wunder = numpy.sum(nnweights * numpy.logical_and(nn, xdata <= 0.0))
            wbin0 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.0 < xdata, xdata <= 0.1)))
            wbin1 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.1 < xdata, xdata <= 0.2)))
            wbin2 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.2 < xdata, xdata <= 0.3)))
            wbin3 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.3 < xdata, xdata <= 0.4)))
            wbin4 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.4 < xdata, xdata <= 0.5)))
            wbin5 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.5 < xdata, xdata <= 0.6)))
            wbin6 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.6 < xdata, xdata <= 0.7)))
            wbin7 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.7 < xdata, xdata <= 0.8)))
            wbin8 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.8 < xdata, xdata <= 0.9)))
            wbin9 = numpy.sum(nnweights * numpy.logical_and(nn, numpy.logical_and(0.9 < xdata, xdata <= 1.0)))
            wover = numpy.sum(nnweights * numpy.logical_and(nn, (xdata > 1.0)))
            wnan = numpy.sum(nnweights * numpy.isnan(xdata))

            w2under = numpy.sum(nnweights2 * numpy.logical_and(nn, (xdata <= 0.0)))
            w2bin0 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.0 < xdata, xdata <= 0.1)))
            w2bin1 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.1 < xdata, xdata <= 0.2)))
            w2bin2 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.2 < xdata, xdata <= 0.3)))
            w2bin3 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.3 < xdata, xdata <= 0.4)))
            w2bin4 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.4 < xdata, xdata <= 0.5)))
            w2bin5 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.5 < xdata, xdata <= 0.6)))
            w2bin6 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.6 < xdata, xdata <= 0.7)))
            w2bin7 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.7 < xdata, xdata <= 0.8)))
            w2bin8 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.8 < xdata, xdata <= 0.9)))
            w2bin9 = numpy.sum(nnweights2 * numpy.logical_and(nn, numpy.logical_and(0.9 < xdata, xdata <= 1.0)))
            w2over = numpy.sum(nnweights2 * numpy.logical_and(nn, (xdata > 1.0)))
            w2nan = numpy.sum(nnweights2 * numpy.isnan(xdata))

        for underflow in False, True:
            for overflow in False, True:
                for nanflow in False, True:
                    compare = [bin0, bin1, bin2, bin3, bin4, bin5, bin6, bin7, bin8, bin9]
                    if underflow:
                        compare.insert(0, under)
                    if overflow:
                        compare.append(over)
                    if nanflow:
                        compare.append(nan)
                    h = Hist(bin("x", 10, 0, 1, underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=False))
                    h.fill(x=xdata)
                    self.assertEqual(h._content.reshape(-1).tolist(), compare)

                    compare = [[wbin0, w2bin0], [wbin1, w2bin1], [wbin2, w2bin2], [wbin3, w2bin3], [wbin4, w2bin4], [wbin5, w2bin5], [wbin6, w2bin6], [wbin7, w2bin7], [wbin8, w2bin8], [wbin9, w2bin9]]
                    if underflow:
                        compare.insert(0, [wunder, w2under])
                    if overflow:
                        compare.append([wover, w2over])
                    if nanflow:
                        compare.append([wnan, w2nan])
                    h = Hist(bin("x", 10, 0, 1, underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=False)).weight("w")
                    h.fill(x=xdata, w=weights)
                    self.assertTrue(numpy.absolute((h._content - numpy.array(compare)).reshape(-1)).max() < 1e-10)

    def test_intbin(self):
        h = Hist(intbin("x", 0, 10, underflow=True, overflow=True))
        h.fill(x=range(-5, 15))
        self.assertEqual(h._content.tolist(), [[5], [1], [1], [1], [1], [1], [1], [1], [1], [1], [1], [1], [4]])

        h = Hist(intbin("x", 0, 10, underflow=True, overflow=False))
        h.fill(x=range(-5, 15))
        self.assertEqual(h._content.tolist(), [[5], [1], [1], [1], [1], [1], [1], [1], [1], [1], [1], [1]])

        h = Hist(intbin("x", 0, 10, underflow=False, overflow=True))
        h.fill(x=range(-5, 15))
        self.assertEqual(h._content.tolist(), [[1], [1], [1], [1], [1], [1], [1], [1], [1], [1], [1], [4]])

        h = Hist(intbin("x", 0, 10, underflow=False, overflow=False))
        h.fill(x=range(-5, 15))
        self.assertEqual(h._content.tolist(), [[1], [1], [1], [1], [1], [1], [1], [1], [1], [1], [1]])

    def test_split(self):
        h = Hist(split("x", 3))
        h.fill(x=[0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(h._content.tolist(), [[3], [4], [0]])

        h = Hist(split("x", 3))
        h.fill(x=[0, 1, 2, 3, 4, 5, numpy.nan])
        self.assertEqual(h._content.tolist(), [[3], [3], [1]])

        h = Hist(split("x", (2.5, 3.5)))
        h.fill(x=[0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(h._content.tolist(), [[3], [1], [3], [0]])

        h = Hist(split("x", (2.5, 3.5, 5.0)))
        h.fill(x=[0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(h._content.tolist(), [[3], [1], [1], [2], [0]])

        h = Hist(split("x", (2.5, 3.5, 5.0), closedlow=False))
        h.fill(x=[0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(h._content.tolist(), [[3], [1], [2], [1], [0]])

        under = [[2]]
        over = [[4]]
        nan = [[1]]
        for underflow in (False, True):
            for overflow in (False, True):
                for nanflow in (False, True):
                    if underflow or overflow or nanflow:
                        h = Hist(split("x", 3, underflow=underflow, overflow=overflow, nanflow=nanflow))
                        h.fill(x=[numpy.nan, 1, 2, 3, 4, 5, 6])
                        self.assertEqual(h._content.tolist(), (under if underflow else []) + (over if overflow else []) + (nan if nanflow else []))

        under = [[2]]
        over = [[1]]
        nan = [[1]]
        for underflow in (False, True):
            for overflow in (False, True):
                for nanflow in (False, True):
                    h = Hist(split("x", (2.5, 3.5, 5.0), underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=False))
                    h.fill(x=[numpy.nan, 1, 2, 3, 4, 5, 6])
                    self.assertEqual(h._content.tolist(), (under if underflow else []) + [[1], [2]] + (over if overflow else []) + (nan if nanflow else []))

    def test_cut(self):
        h = Hist(cut("p"))
        h.fill(p=[False, True, True])
        self.assertEqual(h._content.tolist(), [[1], [2]])

        h = Hist(cut("x > 3"))
        h.fill(x=[1, 2, 3, 4, 5])
        self.assertEqual(h._content.tolist(), [[3], [2]])

        h = Hist(cut("x > 3 and p"))
        h.fill(x=[1, 2, 3, 4, 5], p=[True, False, True, False, True])
        self.assertEqual(h._content.tolist(), [[4], [1]])

        h = Hist(cut("x > 3 and y % 2 == 0"))
        h.fill(x=[1, 2, 3, 4, 5], y=[0, 1, 2, 3, 4])
        self.assertEqual(h._content.tolist(), [[4], [1]])

        h = Hist(cut("x > 3 and y % 2 == 0"), split("x", 3.5))
        h.fill(x=[1, 2, 3, 4, 5], y=[0, 1, 2, 3, 4])
        self.assertEqual(h._content.tolist(), [[[3], [1], [0]], [[0], [1], [0]]])

    def test_profile(self):
        h = Hist(bin("x", 10, 10, 11), profile("y"))
        h.fill(x=[10.4, 10.3, 10.3, 10.5, 10.4, 10.8], y=[0.1, 0.1, 0.1, 0.1, 0.1, 1.0])
        self.assertEqual(h._content.tolist(), [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.2, 0.020000000000000004, 2.0], [0.2, 0.020000000000000004, 2.0], [0.1, 0.010000000000000002, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])

        h = Hist(bin("x", 10, 10, 11), profile("y"), profile("2*y"))
        h.fill(x=[10.4, 10.3, 10.3, 10.5, 10.4, 10.8], y=[0.1, 0.1, 0.1, 0.1, 0.1, 1.0])
        self.assertEqual(h._content.tolist(), [[0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0], [0.2, 0.020000000000000004, 0.4, 0.08000000000000002, 2.0], [0.2, 0.020000000000000004, 0.4, 0.08000000000000002, 2.0], [0.1, 0.010000000000000002, 0.2, 0.04000000000000001, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 2.0, 4.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0]])

    def test_groupby(self):
        h = Hist(groupby("c"), bin("x", 3, 1.0, 4.0, underflow=False, overflow=False, nanflow=False))
        h.fill(c=["one", "two", "three", "two", "one", "one", "one"], x=[1, 2, 3, 2, 1, 1, 3])
        self.assertEqual(h._content["one"].tolist(), [[3], [0], [1]])
        self.assertEqual(h._content["two"].tolist(), [[0], [2], [0]])
        self.assertEqual(h._content["three"].tolist(), [[0], [0], [1]])

    def test_groupby_groupby(self):
        h = Hist(groupby("c1"), groupby("c2"), bin("x", 1, 1.0, 2.0, underflow=False, overflow=False, nanflow=False))
        h.fill(c1=["one", "two", "one", "two"], c2=["uno", "uno", "dos", "dos"], x=[1, 1, 1, 1])
        self.assertEqual(h._content["one"]["uno"].tolist(), [[1]])
        self.assertEqual(h._content["two"]["uno"].tolist(), [[1]])
        self.assertEqual(h._content["one"]["dos"].tolist(), [[1]])
        self.assertEqual(h._content["two"]["dos"].tolist(), [[1]])

    def test_groupbin(self):
        h = Hist(groupbin("x", 10.0), bin("y", 4, 1.0, 5.0, underflow=False, overflow=False, nanflow=False))
        h.fill(x=[0, 10, 15, 20], y=[1, 2, 3, 4])
        self.assertEqual(h._content[0.0].tolist(),  [[1], [0], [0], [0]])
        self.assertEqual(h._content[10.0].tolist(), [[0], [1], [1], [0]])
        self.assertEqual(h._content[20.0].tolist(), [[0], [0], [0], [1]])

        h = Hist(groupbin("x", 10.0, origin=1.0), bin("y", 4, 1.0, 5.0, underflow=False, overflow=False, nanflow=False))
        h.fill(x=[0, 10, 15, 20], y=[1, 2, 3, 4])
        self.assertEqual(h._content[-9.0].tolist(), [[1], [0], [0], [0]])
        self.assertEqual(h._content[1.0].tolist(),  [[0], [1], [0], [0]])
        self.assertEqual(h._content[11.0].tolist(), [[0], [0], [1], [1]])

    def test_groupby_groupbin(self):
        h = Hist(bin("y", 4, 1.0, 5.0, underflow=False, overflow=False, nanflow=False), groupby("c"), groupbin("x", 10.0))
        h.fill(c=["one", "one", "two", "two"], x=[0, 10, 15, 20], y=[1, 2, 3, 4])
        self.assertEqual(h._content["one"][0.0].tolist(),  [[1], [0], [0], [0]])
        self.assertEqual(h._content["one"][10.0].tolist(), [[0], [1], [0], [0]])
        self.assertEqual(h._content["two"][10.0].tolist(), [[0], [0], [1], [0]])
        self.assertEqual(h._content["two"][20.0].tolist(), [[0], [0], [0], [1]])

        h = Hist(groupbin("x", 10.0), bin("y", 4, 1.0, 5.0, underflow=False, overflow=False, nanflow=False), groupby("c"))
        h.fill(c=["one", "one", "two", "two"], x=[0, 10, 15, 20], y=[1, 2, 3, 4])
        self.assertEqual(h._content[0.0]["one"].tolist(),  [[1], [0], [0], [0]])
        self.assertEqual(h._content[10.0]["one"].tolist(), [[0], [1], [0], [0]])
        self.assertEqual(h._content[10.0]["two"].tolist(), [[0], [0], [1], [0]])
        self.assertEqual(h._content[20.0]["two"].tolist(), [[0], [0], [0], [1]])

    def test_book(self):
        b = Book()
        b["one"] = Hist(bin("x", 2, 0, 3, underflow=False, overflow=False, nanflow=False))
        b["two"] = Hist(split("x", 1.5, nanflow=False))
        b.fill(x=[1, 1, 1, 2, 2])
        self.assertEqual(b["one"]._content.tolist(), [[3], [2]])
        self.assertEqual(b["two"]._content.tolist(), [[3], [2]])

        b = Book()
        b["one"] = Hist(bin("x", 2, 0, 3, underflow=False, overflow=False, nanflow=False))
        b["two"] = Hist(split("y", 1.5, nanflow=False))
        b.fill(x=[1, 1, 1, 2, 2], y=[1, 1, 1, 2, 2])
        self.assertEqual(b["one"]._content.tolist(), [[3], [2]])
        self.assertEqual(b["two"]._content.tolist(), [[3], [2]])
