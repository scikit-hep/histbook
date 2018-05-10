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

class TotalBins(object):
    def __init__(self, totalbins, variable):
        self.totalbins = totalbins
        self.variable = variable

    @staticmethod
    def _tosize(self, totalbins):
        total, unit = totalbins * 8, "bytes"
        if total > 2048:
            total /= 1024.0
            unit = "kB"
            if total > 2048:
                total /= 1024.0
                unit = "MB"
                if total > 2048:
                    total /= 1024.0
                    unit = "GB"
                    if total > 2048:
                        total /= 1024.0
                        unit = "TB"
        return total, unit

    def __repr__(self):
        total, unit = TotalBins._tosize(self.totalbins)
        return "{0} bins ({1:.4g} {2}){3}".format(self.totalbins, total, unit, "".join(" * num(" + repr(x) + ")" for x in self.variable))

    def __int__(self):
        return self.totalbins

class SumOfTotalBins(object):
    def __init__(self, totalbins):
        self.totalbins = totalbins

    def __repr__(self):
        totalbins = int(self)
        total, unit = TotalBins._tosize(totalbins)

        if any(x.variable != () for x in self.totalbins):
            return "{0} bins ({1:.4g {2}}) at least".format(totalbins, total, unit)
        else:
            return "{0} bins ({1:.4g {2}})".format(totalbins, total, unit)

    def __int__(self):
        return sum(int(x) for x in self.totalbins)

class _Endable(object):
    @property
    def totalbins(self):
        return TotalBins(*self._totalbins())

    def fill(self, **arrays):
        import histbook.hist
        if not isinstance(self, histbook.hist.Fillable):
            self.__class__ = type("DynamicFillable", self.__class__.__bases__ + (histbook.hist.Fillable,), {})
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

    @property
    def totalbins(self):
        return SumOfTotalBins([x.totalbins for x in self._hists.values()])

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

    def _totalbins(self):
        if self._prev is None:
            return 2, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return 2*totalbins, variable

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

    def _totalbins(self):
        if self._prev is None:
            return 3, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return 3*totalbins, variable

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

    def _totalbins(self):
        num = self._numbins
        if self._underflow: num += 1
        if self._overflow: num += 1
        if self._nanflow: num += 1
        if self._prev is None:
            return 3*num, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return 3*num*totalbins, variable

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

    def _totalbins(self):
        num = len(self._edges) - 1
        if self._underflow: num += 1
        if self._overflow: num += 1
        if self._nanflow: num += 1
        if self._prev is None:
            return 3*num, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return 3*num*totalbins, variable

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

    def _totalbins(self):
        num = self._numbins
        if self._underflow: num += 1
        if self._overflow: num += 1
        if self._nanflow: num += 1
        if self._prev is None:
            return num, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return num*totalbins, variable

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

    def _totalbins(self):
        num = self._max - self._min + 1
        if self._underflow: num += 1
        if self._overflow: num += 1
        if self._prev is None:
            return num, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return num*totalbins, variable

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

    def _totalbins(self):
        num = len(self._edges) - 1
        if self._underflow: num += 1
        if self._overflow: num += 1
        if self._nanflow: num += 1
        if self._prev is None:
            return num, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return num*totalbins, variable

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

    def _totalbins(self):
        if self._prev is None:
            return 2, ()
        else:
            totalbins, variable = self._prev._totalbins()
            return 2*totalbins, variable

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

    def _totalbins(self):
        if self._prev is None:
            return 1, (self._expr,)
        else:
            totalbins, variable = self._prev._totalbins()
            return 1*totalbins, variable + (self._expr,)

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

    def _totalbins(self):
        if self._prev is None:
            return 1, (self._expr,)
        else:
            totalbins, variable = self._prev._totalbins()
            return 1*totalbins, variable + (self._expr,)
