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

import numbers

import numpy

import histbook.axis

class Facet(object): pass

class OverlayFacet(Facet):
    def __init__(self, axis):
        self.axis = axis
    def __repr__(self):
        return ".overlay({0})".format(self.axis)

class StackFacet(Facet):
    def __init__(self, axis):
        self.axis = axis
    def __repr__(self):
        return ".stack({0})".format(self.axis)

class ColumnsFacet(Facet):
    def __init__(self, axis):
        self.axis = axis
    def __repr__(self):
        return ".columns({0})".format(self.axis)

class RowsFacet(Facet):
    def __init__(self, axis):
        self.axis = axis
    def __repr__(self):
        return ".rows({0})".format(self.axis)

class StepsFacet(Facet):
    def __init__(self, axis, profile):
        self.axis = axis
        self.profile = profile
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        return ".steps({0})".format("".join(args))

class AreasFacet(Facet):
    def __init__(self, axis, profile):
        self.axis = axis
        self.profile = profile
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        return ".areas({0})".format("".join(args))

class LinesFacet(Facet):
    def __init__(self, axis, profile, errors):
        self.axis = axis
        self.profile = profile
        self.errors = errors
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        if self.errors is not False:
            args.append("errors={0}".format(self.errors))
        return ".lines({0})".format("".join(args))

class PointsFacet(Facet):
    def __init__(self, axis, profile, errors):
        self.axis = axis
        self.profile = profile
        self.errors = errors
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        if self.errors is not True:
            args.append("errors={0}".format(self.errors))
        return ".points({0})".format("".join(args))

class FacetChain(object):
    def __init__(self, source, item):
        if isinstance(source, FacetChain):
            self._source = source._source
            self._chain = source._chain + (item,)
        else:
            self._source = source
            self._chain = (item,)

    def __repr__(self):
        return "".join(repr(x) for x in (self._source,) + self._chain)

    def __str__(self, indent="\n     ", paren=True):
        return ("(" if paren else "") + indent.join(repr(x) for x in (self._source,) + self._chain) + (")" if paren else "")

    def overlay(self, axis):
        if any(isinstance(x, OverlayFacet) for x in self._chain):
            raise TypeError("cannot overlay an overlay")
        return FacetChain(self, OverlayFacet(axis))

    def stack(self, axis):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("cannot stack a stack")
        return FacetChain(self, StackFacet(axis))

    def columns(self, axis):
        if any(isinstance(x, ColumnsFacet) for x in self._chain):
            raise TypeError("cannot split columns into columns")
        return FacetChain(self, ColumnsFacet(axis))

    def rows(self, axis):
        if any(isinstance(x, RowsFacet) for x in self._chain):
            raise TypeError("cannot split rows into rows")
        return FacetChain(self, RowsFacet(axis))

    def _singleaxis(self, axis):
        if axis is None:
            if len(self._source._group + self._source._fixed) == 1:
                axis, = self._source._group + self._source._fixed
            else:
                raise TypeError("histogram has more than one axis; one must be specified for plotting")
        return axis

    def steps(self, axis=None, profile=None):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("only areas can be stacked")
        return Plotable(self, StepsFacet(self._singleaxis(axis), profile))

    def areas(self, axis=None, profile=None):
        return Plotable(self, AreasFacet(self._singleaxis(axis), profile))

    def lines(self, axis=None, profile=None, errors=False):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("only areas can be stacked")
        if errors and any(isinstance(x, (ColumnsFacet, RowsFacet)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting into columns or rows (Vega-Lite bug?)")
        return Plotable(self, LinesFacet(self._singleaxis(axis), profile, errors))

    def points(self, axis=None, profile=None, errors=True):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("only areas can be stacked")
        if errors and any(isinstance(x, (ColumnsFacet, RowsFacet)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting into columns or rows (Vega-Lite bug?)")
        return Plotable(self, PointsFacet(self._singleaxis(axis), profile, errors))

class Plotable(object):
    def __init__(self, source, item):
        if isinstance(source, FacetChain):
            self._source = source._source
            self._chain = source._chain + (item,)
        else:
            self._source = source
            self._chain = (item,)

    def __repr__(self):
        return "".join(repr(x) for x in (self._source,) + self._chain)

    def __str__(self, indent="\n     ", paren=True):
        return ("(" if paren else "") + indent.join(repr(x) for x in (self._source,) + self._chain) + (")" if paren else "")

    def _varname(self, i):
        return "d" + str(i)

    def _data(self, prefix=(), baseline=False):
        errors = getattr(self._chain[-1], "errors", False)
        profile = self._chain[-1].profile
        if profile is None:
            profiles = ()
        else:
            profiles = (profile,)

        projected = self._source.project(*(x.axis for x in self._chain))
        table = projected.table(*profiles, count=(profile is None), error=errors)

        axis = projected.axis
        dep = table[table.dtype.names[0]]
        if errors:
            deperr = table[table.dtype.names[1]]
        
        data = []
        def recurse(i, j, content, row):
            if j == len(axis):
                if i is None:
                    if errors:
                        row = row + (0.0, 0.0)
                    else:
                        row = row + (0.0,)
                else:
                    if errors:
                        row = row + (dep[i], deperr[i])
                    else:
                        row = row + (dep[i],)
                data.append(dict(zip([self._varname(i) for i in range(len(row))], row)))

            else:
                for i, (n, x) in enumerate(axis[j].items(content)):
                    if isinstance(n, histbook.axis.Interval):
                        if numpy.isfinite(n.low) and numpy.isfinite(n.high):
                            if baseline and j == len(axis) - 1 and isinstance(axis[j], histbook.axis.bin) and n.low == axis[j].low:
                                recurse(None, j + 1, x, row + (n.low,))
                                recurse(i, j + 1, x, row + (n.low + 1e-12,))
                            else:
                                recurse(i, j + 1, x, row + (n.low,))

                            if baseline and j == len(axis) - 1 and isinstance(axis[j], histbook.axis.bin) and n.high == axis[j].high:
                                recurse(None, j + 1, x, row + (n.high,))

                    elif isinstance(n, (numbers.Integral, numpy.integer)):
                        recurse(i, j + 1, x, row + (n,))

                    else:
                        recurse(i, j + 1, x, row + (str(n),))

        recurse(0, 0, table, prefix)
        return axis, data

    def vegalite(self):
        axis, data = self._data(baseline=True)

        if isinstance(self._chain[-1], StepsFacet):
            mark = {"type": "line", "interpolate": "step-before"}

        elif isinstance(self._chain[-1], AreasFacet):
            mark = {"type": "area", "interpolate": "step-before"}

        elif isinstance(self._chain[-1], LinesFacet):
            mark = {"type": "line", "interpolate": "step-before"}

        elif isinstance(self._chain[-1], PointsFacet):
            mark = {"type": "points", "interpolate": "step-before"}

        else:
            raise AssertionError(self._chain[-1])

        encoding = {}
        encoding["y"] = {"field": self._varname(len(axis)), "type": "quantitative"}
        encoding["x"] = {"field": self._varname(axis.index(self._chain[-1].axis)), "type": "quantitative", "scale": {"zero": False}}

        return {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
                "data": {"values": data},
                "mark": mark,
                "encoding": encoding}

    def to(self, fcn):
        return fcn(self.vegalite())

class Combination(object):
    def __init__(self, *plotables):
        self._plotables = plotables

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(repr(x) for x in self._plotables))

    def __str__(self, indent="\n    ", paren=False):
        return "{0}({1})".format(self.__class__.__name__, "".join(indent + x.__str__(indent + "    ", False) for x in self._plotables))

    def to(self, fcn):
        return fcn(self.vegalite())

class overlay(Combination):
    def vegalite(self):
        raise NotImplementedError

class columns(Combination):
    def vegalite(self):
        raise NotImplementedError

class rows(Combination):
    def vegalite(self):
        raise NotImplementedError
