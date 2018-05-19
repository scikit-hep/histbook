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

class BesideFacet(Facet):
    def __init__(self, axis):
        self.axis = axis
    def __repr__(self):
        return ".beside({0})".format(self.axis)

class BelowFacet(Facet):
    def __init__(self, axis):
        self.axis = axis
    def __repr__(self):
        return ".below({0})".format(self.axis)

class StepFacet(Facet):
    def __init__(self, axis, profile):
        self.axis = axis
        self.profile = profile
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        return ".step({0})".format("".join(args))

class AreaFacet(Facet):
    def __init__(self, axis, profile):
        self.axis = axis
        self.profile = profile
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        return ".area({0})".format("".join(args))

class LineFacet(Facet):
    def __init__(self, axis, profile, error):
        self.axis = axis
        self.profile = profile
        self.error = error
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        if self.error is not False:
            args.append("error={0}".format(self.error))
        return ".line({0})".format("".join(args))

class MarkerFacet(Facet):
    def __init__(self, axis, profile, error):
        self.axis = axis
        self.profile = profile
        self.error = error
    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        if self.error is not True:
            args.append("error={0}".format(self.error))
        return ".marker({0})".format("".join(args))

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

    def beside(self, axis):
        if any(isinstance(x, BesideFacet) for x in self._chain):
            raise TypeError("cannot split plots beside each other that are already split with beside (can do beside and below)")
        return FacetChain(self, BesideFacet(axis))

    def below(self, axis):
        if any(isinstance(x, BelowFacet) for x in self._chain):
            raise TypeError("cannot split plots below each other that are already split with below (can do beside and below)")
        return FacetChain(self, BelowFacet(axis))

    def _singleaxis(self, axis):
        if axis is None:
            if len(self._source._group + self._source._fixed) == 1:
                axis, = self._source._group + self._source._fixed
            else:
                raise TypeError("histogram has more than one axis; one must be specified for plotting")
        return axis

    def step(self, axis=None, profile=None):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("only area can be stacked")
        return Plotable(self, StepFacet(self._singleaxis(axis), profile))

    def area(self, axis=None, profile=None):
        return Plotable(self, AreaFacet(self._singleaxis(axis), profile))

    def line(self, axis=None, profile=None, error=False):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("only area can be stacked")
        if error and any(isinstance(x, (BesideFacet, BelowFacet)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below (Vega-Lite bug?)")
        return Plotable(self, LineFacet(self._singleaxis(axis), profile, error))

    def marker(self, axis=None, profile=None, error=True):
        if any(isinstance(x, StackFacet) for x in self._chain):
            raise TypeError("only area can be stacked")
        if error and any(isinstance(x, (BesideFacet, BelowFacet)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below (Vega-Lite bug?)")
        return Plotable(self, MarkerFacet(self._singleaxis(axis), profile, error))

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
        error = getattr(self._chain[-1], "error", False)
        profile = self._chain[-1].profile
        if profile is None:
            profiles = ()
        else:
            profiles = (profile,)

        projected = self._source.project(*(x.axis for x in self._chain))
        table = projected.table(*profiles, count=(profile is None), error=error)

        axis = projected.axis
        dep = table[table.dtype.names[0]]
        if error:
            deperr = table[table.dtype.names[1]]
        
        data = []
        def recurse(i, j, content, row):
            if j == len(axis):
                if i is None:
                    if error:
                        row = row + (0.0, 0.0)
                    else:
                        row = row + (0.0,)
                else:
                    if error:
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
                                recurse(i, j + 1, x, row + (n.low + 1e-10*(axis[j].high - axis[j].low),))
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

        if isinstance(self._chain[-1], StepFacet):
            mark = {"type": "line", "interpolate": "step-before"}

        elif isinstance(self._chain[-1], AreaFacet):
            mark = {"type": "area", "interpolate": "step-before"}

        elif isinstance(self._chain[-1], LineFacet):
            mark = {"type": "line", "interpolate": "step-before"}

        elif isinstance(self._chain[-1], MarkerFacet):
            mark = {"type": "marker", "interpolate": "step-before"}

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

class beside(Combination):
    def vegalite(self):
        raise NotImplementedError

class below(Combination):
    def vegalite(self):
        raise NotImplementedError
