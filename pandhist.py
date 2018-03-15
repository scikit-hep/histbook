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

import numpy
import pandas

def _irrbinintervals(edges, closed):
    if len(edges) == 0:
        raise ValueError("at least one bin edge must be provided")
    if closed != "left" and closed != "right":
        raise ValueError("closed must be 'left' for [low, high) or 'right' for (low, high]")
    underflow = pandas.Interval(float("-inf"), edges[0], closed)
    overflow  = pandas.Interval(edges[-1], float("inf"), closed)
    return [underflow] + [pandas.Interval(a, b, closed=closed) for a, b in zip(edges[:-1], edges[1:])] + [overflow]

def _binintervals(numbins, low, high, closed):
    if numbins <= 0:
        raise ValueError("numbins must be at least 1")
    edges = numpy.linspace(low, high, numbins + 1)
    return _irrbinintervals(edges, closed)

def bin(numbins, low, high, expression, closed="left"):
    return HistogramLayoutBinning([_binintervals(numbins, low, high, closed)], [expression])

def irrbin(edges, expression, closed="left"):
    return HistogramLayoutBinning([_irrbinintervals(edges, closed)], [expression])

def frac(expression):
    return HistogramLayoutBinning([["numer", "denom"]], [expression])

def cut(expression):
    return HistogramLayoutBinning([["pass", "fail"]], [expression])

class HistogramLayout(object):
    def __init__(self, indexes, expressions, columns):
        self.indexes = indexes
        self.expressions = expressions
        self.columns = columns

    def _newcolumn(self, column):
        if column in self.columns:
            raise ValueError("attempting to attach {0} twice".format(repr(column)))
        return HistogramLayout(self.indexes, self.expressions, self.columns + [column])

    def sumw2(self):
        return self._newcolumn("sumw2")

    def sumwx(self, expression):
        return self._newcolumn("sumwx({0})".format(expression))

    def sumwx2(self, expression):
        return self._newcolumn("sumwx2({0})".format(expression))

    def min(self, expression):
        return self._newcolumn("min({0})".format(expression))

    def max(self, expression):
        return self._newcolumn("max({0})".format(expression))

    def toDF(self):
        return pandas.DataFrame(
            index=pandas.MultiIndex.from_product(self.indexes, names=self.expressions),
            columns=self.columns,
            data=dict((x, float("inf") if x.startswith("min") else float("-inf") if x.startswith("max") else 0.0) for x in self.columns))

class HistogramLayoutBinning(HistogramLayout):
    def __init__(self, indexes, expressions):
        super(HistogramLayoutBinning, self).__init__(indexes, expressions, ["sumw"])

    def bin(self, numbins, low, high, expression, closed="left"):
        return HistogramLayoutBinning(self.indexes + [_binintervals(numbins, low, high, closed)], self.expressions + [expression])

    def irrbin(self, edges, expression, closed="left"):
        return HistogramLayoutBinning(self.indexes + [_irrbinintervals(edges, closed)], self.expressions + [expression])

    def frac(self, expression):
        return HistogramLayoutBinning(self.indexes + [["numer", "denom"]], self.expressions + [expression])

    def cut(self, expression):
        return HistogramLayoutBinning(self.indexes + [["pass", "fail"]], self.expressions + [expression])
