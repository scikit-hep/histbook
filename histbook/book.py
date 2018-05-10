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
import sys

class _Endable(object):
    def fill(self, **arrays):
        import histbook.hist
        if not isinstance(self, histbook.hist.Fillable):
            self.__class__ = type("DynamicFillable", (histbook.hist.Fillable,) + self.__class__.__bases__, {})
            self.__init__(self)
            self.fill(**arrays)

class _Profilable(object):
    def weighted(self, expr, ignorenan=True):
        return weighted(expr, ignorenan=ignorenan, defs=self._defs, prev=self)

    def prof(self, expr, ignorenan=True):
        return prof(expr, ignorenan=ignorenan, defs=self._defs, prev=self)

    def binprof(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True):
        return binprof(expr, numbins, low, high, underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=closedlow, defs=self._defs, prev=self)

    def partitionprof(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        return partitionprof(expr, edges, underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=closedlow, defs=self._defs, prev=self)

class _Chainable(_Profilable):
    def bin(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True):
        return bin(expr, numbins, low, high, underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=closedlow, defs=self._defs, prev=self)

    def intbin(self, expr, min, max, underflow=True, overflow=True):
        return intbin(expr, min, max, underflow=underflow, overflow=overflow, defs=self._defs, prev=self)

    def partition(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        return partition(expr, edges, underflow=underflow, overflow=overflow, nanflow=nanflow, closedlow=closedlow, defs=self._defs, prev=self)

    def cut(self, expr):
        return cut(expr, defs=self._defs, prev=self)

class _Scalable(_Chainable):
    def categorical(self, expr):
        return categorical(expr, defs=self._defs, prev=self)

    def sparse(self, expr, binwidth, origin=0, nanflow=True, closedlow=True):
        return sparse(expr, binwidth, origin=origin, nanflow=nanflow, closedlow=closedlow, defs=self._defs, prev=self)

class _Booking(object):
    def __repr__(self):
        x = self
        pieces = [x._repr()]
        while x._prev is not None:
            x = x._prev
            pieces.insert(0, x._repr())
        return ".".join(pieces)

    def __str__(self):
        x = self
        pieces = [x._repr()]
        while x._prev is not None:
            x = x._prev
            pieces.insert(0, x._repr())
        return "(" + "\n  .".join(pieces) + ")"

class book(_Endable, collections.MutableMapping):
    def __init__(self, **hists):
        self._hists = hists

    def __repr__(self):
        return "book({0} histograms)".format(len(self))

    def __len__(self):
        return len(self._hists)

    def __getitem__(self, name):
        return self._hists[name]

    def __setitem__(self, name, value):
        self._hists[name] = value

    def __delitem__(self, name):
        del self._hists[name]

    def __iter__(self):
        if sys.version_info[0] < 3:
            return self._hists.iterkeys()
        else:
            return self._hists.keys()

class defs(_Scalable, _Booking):
    def __init__(self, **exprs):
        self._defs = exprs
        self._prev = None

    def _repr(self):
        return "defs({0})".format(", ".join("{0}={1}".format(n, repr(x)) for n, x in self._defs.items()))

class weighted(_Endable, _Booking):
    def __init__(self, expr, ignorenan=True, defs={}, prev=None):
        self._expr = expr
        self._ignorenan = ignorenan
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr)]
        if self._ignorenan is not True:
            args.append("ignorenan={0}".format(repr(self._ignorenan)))
        return "weighted({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def ignorenan(self):
        return self._ignorenan

class prof(_Profilable, _Endable, _Booking):
    def __init__(self, expr, ignorenan=True, defs={}, prev=None):
        self._expr = expr
        self._ignorenan = ignorenan
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr)]
        if self._ignorenan is not True:
            args.append("ignorenan={0}".format(repr(self._ignorenan)))
        return "prof({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def ignorenan(self):
        return self._ignorenan

class binprof(_Profilable, _Endable, _Booking):
    def __init__(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True, defs={}, prev=None):
        self._expr = expr
        self._numbins = numbins
        self._low = low
        self._high = high
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr), repr(self._numbins), repr(self._low), repr(self._high)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "binprof({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def numbins(self):
        return self._numbins

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

class partitionprof(_Profilable, _Endable, _Booking):
    def __init__(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._edges = tuple(edges)
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr), repr(self._edges)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "partitionprof({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def edges(self):
        return self._edges

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

class bin(_Chainable, _Endable, _Booking):
    def __init__(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True, defs={}, prev=None):
        self._expr = expr
        self._numbins = numbins
        self._low = low
        self._high = high
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr), repr(self._numbins), repr(self._low), repr(self._high)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "bin({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def numbins(self):
        return self._numbins

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

class intbin(_Chainable, _Endable, _Booking):
    def __init__(self, expr, min, max, underflow=True, overflow=True, defs={}, prev=None):
        self._expr = expr
        self._min = min
        self._max = max
        self._underflow = underflow
        self._overflow = overflow
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr), repr(self._min), repr(self._max)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        return "intbin({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

class partition(_Chainable, _Endable, _Booking):
    def __init__(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._edges = tuple(edges)
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr), repr(self._edges)]
        if self._underflow is not True:
            args.append("underflow={0}".format(repr(self._underflow)))
        if self._overflow is not True:
            args.append("overflow={0}".format(repr(self._overflow)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "partition({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def edges(self):
        return self._edges

    @property
    def underflow(self):
        return self._underflow

    @property
    def overflow(self):
        return self._overflow

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

class cut(_Chainable, _Endable, _Booking):
    def __init__(self, expr, defs={}, prev=None):
        self._expr = expr
        self._defs = defs
        self._prev = prev

    def _repr(self):
        return "cut({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

class categorical(_Scalable, _Endable, _Booking):
    def __init__(self, expr, defs={}, prev=None):
        self._expr = expr
        self._defs = defs
        self._prev = prev

    def _repr(self):
        return "categorical({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

class sparse(_Scalable, _Endable, _Booking):
    def __init__(self, expr, binwidth, origin=0, nanflow=True, closedlow=True, defs={}, prev=None):
        self._expr = expr
        self._binwidth = binwidth
        self._origin = origin
        self._nanflow = nanflow
        self._closedlow = closedlow
        self._defs = defs
        self._prev = prev

    def _repr(self):
        args = [repr(self._expr), repr(self._binwidth)]
        if self._origin != 0:
            args.append("origin={0}".format(repr(self._origin)))
        if self._nanflow is not True:
            args.append("nanflow={0}".format(repr(self._nanflow)))
        if self._closedlow is not True:
            args.append("closedlow={0}".format(repr(self._closedlow)))
        return "sparse({0})".format(", ".join(args))

    @property
    def expr(self):
        return self._expr

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow
