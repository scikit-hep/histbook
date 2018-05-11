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

import numpy

class Axis(object): pass
class GrowableAxis(Axis): pass
class FixedAxis(Axis): pass
class ProfileAxis(Axis): pass

INDEXTYPE = numpy.int32

class categorical(GrowableAxis):
    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return "categorical({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

    def relabel(self, label):
        return categorical(label)

class sparse(GrowableAxis):
    def __init__(self, expr, binwidth, origin=0, nanflow=True, closedlow=True):
        self._expr = expr
        self._binwidth = binwidth
        self._origin = origin
        self._nanflow = nanflow
        self._closedlow = closedlow

    def __repr__(self):
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
    def binwidth(self):
        return self._binwidth

    @property
    def origin(self):
        return self._origin

    @property
    def nanflow(self):
        return self._nanflow

    @property
    def closedlow(self):
        return self._closedlow

    def relabel(self, label):
        return sparse(label, self._binwidth, origin=self._origin, nanflow=self._nanflow, closedlow=self._closedlow)

class bin(FixedAxis):
    def __init__(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._numbins = numbins
        self._low = low
        self._high = high
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow

    def __repr__(self):
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

    def relabel(self, label):
        return bin(label, self._numbins, self._low, self._high, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)

    @property
    def totbins(self):
        return self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + (1 if self._nanflow else 0)

    def index(self, values):
        out = numpy.ma.empty(values.shape, dtype=INDEXTYPE)

        if self._closedlow:
            underflow = (values < self._low)
            overflow = (values >= self._high)
            nanflow = numpy.isnan(values)

            inrange = numpy.bitwise_or(underflow, overflow)
            numpy.bitwise_or(inrange, nanflow, inrange)
            numpy.logical_not(inrange, inrange)

            out[inrange] = numpy.floor((values[inrange] - self._low) * (self._numbins / (self._high - self._low)))

        else:
            underflow = (values <= self._low)
            overflow = (values > self._high)
            nanflow = numpy.isnan(values)

            inrange = numpy.bitwise_or(underflow, overflow)
            numpy.bitwise_or(inrange, nanflow, inrange)
            numpy.logical_not(inrange, inrange)

            out[inrange] = numpy.ceil((values[inrange] - self._low) * (self._numbins / (self._high - self._low))) - 1

        index = self._numbins
        if self._underflow:
            out[underflow] = index
            index += 1
        else:
            out[underflow] = numpy.ma.masked

        if self._overflow:
            out[overflow] = index
            index += 1
        else:
            out[overflow] = numpy.ma.masked

        if self._nanflow:
            out[nanflow] = index
            index += 1
        else:
            out[nanflow] = numpy.ma.masked

        return out

class intbin(FixedAxis):
    def __init__(self, expr, min, max, underflow=True, overflow=True):
        self._expr = expr
        self._min = min
        self._max = max
        self._underflow = underflow
        self._overflow = overflow

    def __repr__(self):
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

    def relabel(self, label):
        return intbin(label, self._min, self._max, underflow=self._underflow, overflow=self._overflow)

    @property
    def numbins(self):
        return self._max - self._min + 1

    @property
    def totbins(self):
        return self.numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0)

    def index(self, values):
        out = numpy.ma.empty(values.shape, dtype=INDEXTYPE)

        underflow = (values < self._min)
        overflow = (values > self._max)
        inrange = numpy.bitwise_or(underflow, overflow)
        numpy.logical_not(inrange, inrange)

        out[inrange] = values[inrange] - self._min

        index = self.numbins
        if self._underflow:
            out[underflow] = index
            index += 1
        else:
            out[underflow] = numpy.ma.masked

        if self._overflow:
            out[overflow] = index
            index += 1
        else:
            out[overflow] = numpy.ma.masked

        return out

class partition(FixedAxis):
    def __init__(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._edges = tuple(sorted(edges))
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow

    def __repr__(self):
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
        return self._closedlo

    def relabel(self, label):
        return partition(label, self._edges, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)

    @property
    def numbins(self):
        return len(self._edges) - 1

    @property
    def totbins(self):
        return self.numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + (1 if self._nanflow else 0)

    def index(self, values):
        out = numpy.ma.empty(values.shape, dtype=INDEXTYPE)

        # FIXME: maybe do this better with numpy.digitize

        nanflow = numpy.isnan(values)
        sel = numpy.logical_not(nanflow)
        valinrange, outinrange = values[sel], out[sel]

        index = 0
        if self._closedlow:
            sel = valinrange[valinrange < self._edges[0]]
            if self._underflow:
                outinrange[sel] = index
                index += 1
            else:
                outinrange[sel] = numpy.ma.masked
            numpy.logical_not(sel, sel)
            valinrange, outinrange = valinrange[sel], outinrange[sel]

            for high in self._edges[1:]:
                sel = valinrange[valinrange < high]
                outinrange[sel] = index
                index += 1
                numpy.logical_not(sel, sel)
                valinrange, outinrange = valinrange[sel], outinrange[sel]

        else:
            sel = valinrange[valinrange <= self._edges[0]]
            if self._underflow:
                outinrange[sel] = index
                index += 1
            else:
                outinrange[sel] = numpy.ma.masked
            numpy.logical_not(sel, sel)
            valinrange, outinrange = valinrange[sel], outinrange[sel]

            for high in self._edges[1:]:
                sel = valinrange[valinrange <= high]
                outinrange[sel] = index
                index += 1
                numpy.logical_not(sel, sel)
                valinrange, outinrange = valinrange[sel], outinrange[sel]

        if self._overflow:
            outinrange[sel] = index
            index += 1
        else:
            outinrange[sel] = numpy.ma.masked

        if self._nanflow:
            out[nanflow] = index
            index += 1
        else:
            out[nanflow] = numpy.ma.masked

        return out
            
class cut(FixedAxis):
    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return "cut({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

    def relabel(self, label):
        return cut(label)

    @property
    def numbins(self):
        return 2

    @property
    def totbins(self):
        return self.numbins

    def index(self, values):
        assert values.dtype == numpy.dtype(numpy.bool_) or values.dtype == numpy.dtype(numpy.bool)
        out = numpy.ma.zeros(values.shape, dtype=INDEXTYPE)
        out[values] = 1
        return out

class prof(ProfileAxis):
    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return "prof({0})".format(repr(self._expr))

    @property
    def expr(self):
        return self._expr

    def relabel(self, label):
        return prof(label)

    @property
    def numbins(self):
        return 1

    @property
    def totbins(self):
        return self.numbins

class binprof(ProfileAxis):
    def __init__(self, expr, numbins, low, high, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._numbins = numbins
        self._low = low
        self._high = high
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow

    def __repr__(self):
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

    def relabel(self, label):
        return binprof(label, self._numbins, self._low, self._high, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)

    @property
    def totbins(self):
        return self._numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + (1 if self._nanflow else 0)

class partitionprof(ProfileAxis):
    def __init__(self, expr, edges, underflow=True, overflow=True, nanflow=True, closedlow=True):
        self._expr = expr
        self._edges = tuple(sorted(edges))
        self._underflow = underflow
        self._overflow = overflow
        self._nanflow = nanflow
        self._closedlow = closedlow

    def __repr__(self):
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

    def relabel(self, label):
        return partitionprof(label, self._edges, underflow=self._underflow, overflow=self._overflow, nanflow=self._nanflow, closedlow=self._closedlow)

    @property
    def numbins(self):
        return len(self._edges) - 1

    @property
    def totbins(self):
        return self.numbins + (1 if self._underflow else 0) + (1 if self._overflow else 0) + (1 if self._nanflow else 0)
