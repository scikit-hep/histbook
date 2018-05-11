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

import collections
import functools
import sys

import numpy

import histbook.expr
import histbook.stmt
import histbook.axis
import histbook.calc

class Fillable(object):
    @property
    def fields(self):
        if self._fields is None:
            table = {}
            fields = histbook.stmt.sources(self._goals, table)
            self._instructions = histbook.stmt.instructions(fields)
            self._fields = sorted(x.goal.value for x in fields)
        return self._fields

    def _fill(self, export, arrays):
        self.fields  # for the side-effect of creating self._instructions

        symbols = {}
        for index, instruction in self._instructions:
            if isinstance(instruction, histbook.stmt.Param):
                symbols[instruction.name] = arrays[instruction.extern]

            elif isinstance(instruction, histbook.stmt.Assign):
                symbols[instruction.name] = histbook.calc.calculate(instruction.expr, symbols)

            elif isinstance(instruction, histbook.stmt.Export):
                export(instruction.expr, symbols[instruction.name])

            elif isinstance(instruction, histbook.stmt.Delete):
                del symbols[instruction.name]

            else:
                raise AssertionError(instruction)

class Book(collections.MutableMapping, Fillable):
    def __init__(self, hists={}, **keywords):
        self._hists = collections.OrderedDict()
        for n, x in hists.items():
            self._hists[n] = x
        for n, x in keywords.items():
            self._hists[n] = x

        self._fields = None

    def __repr__(self):
        return "Book({0} histogram{1})".format(len(self), "" if len(self) == 1 else "s")

    def __str__(self):
        return "Book({" + ",\n      ".join("{0}: {1}".format(repr(n), repr(x)) for n, x in self.items()) + "})"

    def __len__(self):
        return len(self._hists)

    def __getitem__(self, name):
        return self._hists[name]

    def __setitem__(self, name, value):
        if isinstance(value, Book):
            for n, x in value.items():
                self._hists[name + "/" + n] = x
                self._fields = None
        elif isinstance(value, Hist):
            self._hists[name] = value
            self._fields = None
        else:
            raise TypeError("histogram books can only be filled with histograms or other histogram books, not {0}".format(type(value)))

    def __delitem__(self, name):
        del self._hists[name]

    def __iter__(self):
        if sys.version_info[0] < 3:
            return self._hists.iterkeys()
        else:
            return self._hists.keys()

    @property
    def _goals(self):
        return functools.reduce(set.union, (x._goals for x in self.values()))

class Hist(Fillable):
    def weight(self, expr):
        return Hist(*[x.relabel(x._original) for x in self._growable + self._fixed + self._profile], defs=self._defs, weight=expr)

    def __init__(self, *axis, **opts):
        weight = opts.pop("weight", None)
        defs = opts.pop("defs", {})
        if len(opts) > 0:
            raise TypeError("unrecognized options for Hist: {0}".format(" ".join(opts)))

        if weight is None:
            self._weightoriginal, self._weightparsed, self._weightlabel = None, None, None
            self._goals = set()
        else:
            self._weightoriginal = weight
            self._weightparsed, self._weightlabel = histbook.expr.Expr.parse(expr, defs=self._defs, returnlabel=True)
            self._goals = set([histbook.stmt.CallGraphGoal(self._weightparsed)])

        self._defs = defs
        self._growable = []
        self._fixed = []
        self._profile = []

        newaxis = []
        for old in axis:
            expr, label = histbook.expr.Expr.parse(old._expr, defs=defs, returnlabel=True)
            new = old.relabel(label)
            new._original = old._expr
            new._parsed = expr
            newaxis.append(new)
            self._goals.add(histbook.stmt.CallGraphGoal(expr))

        # each growable axis adds a level to nested dicts
        dictindex = 0
        for new in newaxis:
            if isinstance(new, histbook.axis.GrowableAxis):
                self._growable.append(new)
                new._dictindex = dictindex
                dictindex += 1

        # each fixed axis adds to the Numpy shape
        self._shape = []
        for new in newaxis:
            if isinstance(new, histbook.axis.FixedAxis):
                self._fixed.append(new)
                new._shapeindex = len(self._shape)
                self._shape.append(new.totbins)

        # sumw is the 0th entry of the last shape index
        # sumw2, if it exists, is the 1st entry of the same shape index
        if weight is None:
            self._shape.append(1)
        else:
            self._shape.append(2)

        # sumwx and sumwx2 for each profile are also in the last shape index
        for new in newaxis:
            if isinstance(x, histbook.axis.ProfileAxis):
                self._profile.append(new)
                new._sumindex = self._shape[-1]
                new._sum2index = self._shape[-1] + 1
                self._shape[-1] += 2

        self._shape = tuple(self._shape)
        self._content = None

        self._fields = None

    def __repr__(self, indent=", "):
        out = [repr(x) for x in self._axis]
        if self._weightlabel is not None:
            out.append("weight={0}".format(repr(self._weightlabel)))
        if len(self._defs) > 0:
            out.append("defs={" + ", ".join("{0}: {1}".format(repr(n), repr(str(x)) if isinstance(x, histbook.expr.Expr) else repr(x)) for n, x in self._defs.items()) + "}")
        return "Hist(" + indent.join(out) + ")"

    def __str__(self):
        return self.__repr__(",\n     ")

    @property
    def shape(self):
        return self._shape

    def fill(**arrays):
        if len(self._growable) > 0:
            raise NotImplementedError

        if self._content is None:
            self._content = numpy.zeros(self._shape, dtype=numpy.float64)

        def export(expr, result):
            for axis in self._fixed:
                if expr == axis._parsed:
                    HERE


                    
        self._fill(export, arrays)
