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

from __future__ import absolute_import

import numbers

import numpy

import histbook.axis

class Channel(object):
    """Abstract class for graphical channels in a Vega-Lite plot."""

    def __init__(self, axis):
        self.axis = axis

class OverlayChannel(Channel):
    """Represents an overlayed axis in a Vega-Lite plot."""

    def __repr__(self):
        return ".overlay({0})".format(self.axis)

class StackChannel(Channel):
    """Represents a stacked axis in a Vega-Lite plot."""

    def __init__(self, axis, order):
        super(StackChannel, self).__init__(axis)
        self.order = order

    def __repr__(self):
        if self.order is None:
            return ".stack({0})".format(self.axis)
        else:
            return ".stack({0}, order={1})".format(self.axis, repr(self.order))

class BesideChannel(Channel):
    """Represents a side-by-side axis in a Vega-Lite plot."""

    def __repr__(self):
        return ".beside({0})".format(self.axis)

class BelowChannel(Channel):
    """Represents an above-and-below axis in a Vega-Lite plot."""

    def __repr__(self):
        return ".below({0})".format(self.axis)

class Terminal1dChannel(Channel):
    """Abstract class for the last graphical channel in a 1d Vega-Lite plot."""

    def __init__(self, axis, profile, error, normalized, width, height, title, config, xscale, yscale, colorscale, shapescale):
        self.axis = axis
        self.profile = profile
        self.error = error
        self.normalized = normalized
        self.width = width
        self.height = height
        self.title = title
        self.config = config
        self.xscale = xscale
        self.yscale = yscale
        self.colorscale = colorscale
        self.shapescale = shapescale

    def __repr__(self):
        args = [repr(self.axis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        if (not isinstance(self, MarkerChannel) and self.error is not False) or (isinstance(self, MarkerChannel) and self.error is not True):
            args.append("error={0}".format(self.error))
        if self.normalized is not False:
            args.append("normalized={0}".format(self.normalized))
        if self.width is not None:
            args.append("width={0}".format(repr(self.width)))
        if self.height is not None:
            args.append("height={0}".format(repr(self.height)))
        if self.title is not None:
            args.append("title={0}".format(repr(self.title)))
        if self.config is not None:
            args.append("config={0}".format(repr(self.config)))
        if self.xscale is not None:
            args.append("xscale={0}".format(repr(self.xscale)))
        if self.yscale is not None:
            args.append("yscale={0}".format(repr(self.yscale)))
        if self.colorscale is not None:
            args.append("colorscale={0}".format(repr(self.colorscale)))
        if self.shapescale is not None:
            args.append("shapescale={0}".format(repr(self.shapescale)))
        return ".{0}({1})".format(self._method, "".join(args))

class BarChannel(Terminal1dChannel):
    """Represents a bar axis in a Vega-Lite plot."""
    _method = "bar"

class StepChannel(Terminal1dChannel):
    """Represents a step axis in a Vega-Lite plot."""
    _method = "step"

class AreaChannel(Terminal1dChannel):
    """Represents an area axis in a Vega-Lite plot."""
    _method = "area"

class LineChannel(Terminal1dChannel):
    """Represents a line axis in a Vega-Lite plot."""
    _method = "line"

class MarkerChannel(Terminal1dChannel):
    """Represents a marker axis in a Vega-Lite plot."""
    _method = "marker"

class Terminal2dChannel(Channel):
    """Abstract class for the last graphical channel in a 2d Vega-Lite plot."""

    def __init__(self, xaxis, yaxis, profile, width, height, title, config, xscale, yscale, colorscale):
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.profile = profile
        self.width = width
        self.height = height
        self.title = title
        self.config = config
        self.xscale = xscale
        self.yscale = yscale
        self.colorscale = colorscale

    def __repr__(self):
        args = [repr(self.xaxis), repr(self.yaxis)]
        if self.profile is not None:
            args.append("profile={0}".format(self.profile))
        if self.width is not None:
            args.append("width={0}".format(repr(self.width)))
        if self.height is not None:
            args.append("height={0}".format(repr(self.height)))
        if self.title is not None:
            args.append("title={0}".format(repr(self.title)))
        if self.config is not None:
            args.append("config={0}".format(repr(self.config)))
        if self.xscale is not None:
            args.append("xscale={0}".format(repr(self.xscale)))
        if self.yscale is not None:
            args.append("yscale={0}".format(repr(self.yscale)))
        if self.colorscale is not None:
            args.append("colorscale={0}".format(repr(self.colorscale)))
        return ".{0}({1})".format(self._method, "".join(args))

class HeatmapChannel(Terminal2dChannel):
    """Represents a heatmap in a Vega-Lite plot."""
    _method = "heatmap"

class PlottingChain(object):
    """Mix-in for :py:class:`Hist <histbook.hist.Hist>` (as the first in a plotting chain) and :py:class:`Channels <histbook.vega.Channel>` in a plotting chain."""

    def __init__(self, source, item):
        if isinstance(source, PlottingChain):
            self._source = source._source
            self._chain = source._chain + (item,)
        else:
            self._source = source
            self._chain = (item,)

    def __repr__(self):
        return "".join(repr(x) for x in (self._source,) + self._chain)

    def __str__(self, indent="\n     ", paren=True):
        return ("(" if paren else "") + indent.join(repr(x) for x in (self._source,) + self._chain) + (")" if paren else "")

    def _singleaxis(self, axis):
        if axis is None:
            if len(self._source._group + self._source._fixed) == 1:
                axis, = self._source._group + self._source._fixed
            else:
                raise TypeError("histogram has more than one axis; one must be specified for plotting")
        return axis

    def _asaxis(self, axis):
        if axis is None:
            return None
        elif isinstance(axis, histbook.axis.Axis):
            return axis
        else:
            return self._source.axis[axis]

    def overlay(self, axis):
        """
        Display bins in ``axis`` overlaid on each other in different colors.

        Parameters
        ----------
        axis : :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay

        Returns
        -------
        :py:class:`PlottingChain <histbook.vega.PlottingChain>`
        """
        if any(isinstance(x, OverlayChannel) for x in self._chain):
            raise TypeError("cannot overlay an overlay")
        return PlottingChain(self, OverlayChannel(self._asaxis(axis)))

    def stack(self, axis, order=None):
        """
        Display bins in ``axis`` stacked on one another in an area plot.

        Parameters
        ----------
        axis : :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay

        order : iterable of strings
            stacking order of bins

        Returns
        -------
        :py:class:`PlottingChain <histbook.vega.PlottingChain>`
        """
        if any(isinstance(x, StackChannel) for x in self._chain):
            raise TypeError("cannot stack a stack")
        return PlottingChain(self, StackChannel(self._asaxis(axis), order))

    def beside(self, axis):
        """
        Display bins in ``axis`` next to each other horizontally.

        Parameters
        ----------
        axis : :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay

        Returns
        -------
        :py:class:`PlottingChain <histbook.vega.PlottingChain>`
        """
        if any(isinstance(x, BesideChannel) for x in self._chain):
            raise TypeError("cannot split plots beside each other that are already split with beside (can do beside and below)")
        return PlottingChain(self, BesideChannel(self._asaxis(axis)))

    def below(self, axis):
        """
        Display bins in ``axis`` next to each other vertically.

        Parameters
        ----------
        axis : :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay

        Returns
        -------
        :py:class:`PlottingChain <histbook.vega.PlottingChain>`
        """
        if any(isinstance(x, BelowChannel) for x in self._chain):
            raise TypeError("cannot split plots below each other that are already split with below (can do beside and below)")
        return PlottingChain(self, BelowChannel(self._asaxis(axis)))

    def bar(self, axis=None, profile=None, error=False, normalized=False, width=None, height=None, title=None, config=None, xscale=None, yscale=None, colorscale=None, shapescale=None):
        """
        Display bins in ``axis`` (if not the only axis) as bars on the horizontal axis.

        Parameters
        ----------
        axis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay; if ``None`` *(default)*, use the only axis in this :py:class:`Hist <histbook.hist.Hist>`

        profile : ``None``, :py:class:`profile <histbook.axis.profile>`, algebraic expression (lambda or string) or index position (integer)
            if ``None`` *(default)*, display bin counts; otherwise, display profile means (and errors on the mean)

        error : bool
            if ``True``, overlay error bars

        normalized : bool
            if ``True``, normalize the histogram

        width, height, title, config, xscale, yscale, colorscale, shapescale : ``None`` or JSON
            graphical directives to pass to Vega-Lite

        Returns
        -------
        :py:class:`Plotable1d <histbook.vega.Plotable1d>`
        """
        if error and any(isinstance(x, (BesideChannel, BelowChannel)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below")
        return Plotable1d(self, BarChannel(self._asaxis(self._singleaxis(axis)), self._asaxis(profile), error, normalized, width, height, title, config, xscale, yscale, colorscale, shapescale))

    def step(self, axis=None, profile=None, error=False, normalized=False, width=None, height=None, title=None, config=None, xscale=None, yscale=None, colorscale=None, shapescale=None):
        """
        Display bins in ``axis`` (if not the only axis) as steps on the horizontal axis.

        Parameters
        ----------
        axis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay; if ``None`` *(default)*, use the only axis in this :py:class:`Hist <histbook.hist.Hist>`

        profile : ``None``, :py:class:`profile <histbook.axis.profile>`, algebraic expression (lambda or string) or index position (integer)
            if ``None`` *(default)*, display bin counts; otherwise, display profile means (and errors on the mean)

        error : bool
            if ``True``, overlay error bars

        normalized : bool
            if ``True``, normalize the histogram

        width, height, title, config, xscale, yscale, colorscale, shapescale : ``None`` or JSON
            graphical directives to pass to Vega-Lite

        Returns
        -------
        :py:class:`Plotable1d <histbook.vega.Plotable1d>`
        """
        if any(isinstance(x, StackChannel) for x in self._chain):
            raise TypeError("only area and bar can be stacked")
        if error and any(isinstance(x, (BesideChannel, BelowChannel)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below")
        return Plotable1d(self, StepChannel(self._asaxis(self._singleaxis(axis)), self._asaxis(profile), error, normalized, width, height, title, config, xscale, yscale, colorscale, shapescale))

    def area(self, axis=None, profile=None, error=False, normalized=False, width=None, height=None, title=None, config=None, xscale=None, yscale=None, colorscale=None, shapescale=None):
        """
        Display bins in ``axis`` (if not the only axis) as areas on the horizontal axis.

        Parameters
        ----------
        axis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay; if ``None`` *(default)*, use the only axis in this :py:class:`Hist <histbook.hist.Hist>`

        profile : ``None``, :py:class:`profile <histbook.axis.profile>`, algebraic expression (lambda or string) or index position (integer)
            if ``None`` *(default)*, display bin counts; otherwise, display profile means (and errors on the mean)

        error : bool
            if ``True``, overlay error bars

        normalized : bool
            if ``True``, normalize the histogram

        width, height, title, config, xscale, yscale, colorscale, shapescale : ``None`` or JSON
            graphical directives to pass to Vega-Lite

        Returns
        -------
        :py:class:`Plotable1d <histbook.vega.Plotable1d>`
        """
        if error and any(isinstance(x, (BesideChannel, BelowChannel)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below")
        return Plotable1d(self, AreaChannel(self._asaxis(self._singleaxis(axis)), self._asaxis(profile), error, normalized, width, height, title, config, xscale, yscale, colorscale, shapescale))

    def line(self, axis=None, profile=None, error=False, normalized=False, width=None, height=None, title=None, config=None, xscale=None, yscale=None, colorscale=None, shapescale=None):
        """
        Display bins in ``axis`` (if not the only axis) as lines on the horizontal axis.

        Parameters
        ----------
        axis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay; if ``None`` *(default)*, use the only axis in this :py:class:`Hist <histbook.hist.Hist>`

        profile : ``None``, :py:class:`profile <histbook.axis.profile>`, algebraic expression (lambda or string) or index position (integer)
            if ``None`` *(default)*, display bin counts; otherwise, display profile means (and errors on the mean)

        error : bool
            if ``True``, overlay error bars

        normalized : bool
            if ``True``, normalize the histogram

        width, height, title, config, xscale, yscale, colorscale, shapescale : ``None`` or JSON
            graphical directives to pass to Vega-Lite

        Returns
        -------
        :py:class:`Plotable1d <histbook.vega.Plotable1d>`
        """
        if any(isinstance(x, StackChannel) for x in self._chain):
            raise TypeError("only area and bar can be stacked")
        if error and any(isinstance(x, (BesideChannel, BelowChannel)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below")
        return Plotable1d(self, LineChannel(self._asaxis(self._singleaxis(axis)), self._asaxis(profile), error, normalized, width, height, title, config, xscale, yscale, colorscale, shapescale))

    def marker(self, axis=None, profile=None, error=True, normalized=False, width=None, height=None, title=None, config=None, xscale=None, yscale=None, colorscale=None, shapescale=None):
        """
        Display bins in ``axis`` (if not the only axis) as markers on the horizontal axis.

        Parameters
        ----------
        axis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the axis to overlay; if ``None`` *(default)*, use the only axis in this :py:class:`Hist <histbook.hist.Hist>`

        profile : ``None``, :py:class:`profile <histbook.axis.profile>`, algebraic expression (lambda or string) or index position (integer)
            if ``None`` *(default)*, display bin counts; otherwise, display profile means (and errors on the mean)

        error : bool
            if ``True``, overlay error bars

        normalized : bool
            if ``True``, normalize the histogram

        width, height, title, config, xscale, yscale, colorscale, shapescale : ``None`` or JSON
            graphical directives to pass to Vega-Lite

        Returns
        -------
        :py:class:`Plotable1d <histbook.vega.Plotable1d>`
        """
        if any(isinstance(x, StackChannel) for x in self._chain):
            raise TypeError("only area and bar can be stacked")
        if error and any(isinstance(x, (BesideChannel, BelowChannel)) for x in self._chain):
            raise NotImplementedError("error bars are currently incompatible with splitting beside or below")
        return Plotable1d(self, MarkerChannel(self._asaxis(self._singleaxis(axis)), self._asaxis(profile), error, normalized, width, height, title, config, xscale, yscale, colorscale, shapescale))

    def heatmap(self, xaxis=None, yaxis=None, profile=None, width=None, height=None, title=None, config=None, xscale=None, yscale=None, colorscale=None):
        """
        Display bins in ``xaxis`` and ``yaxis`` (if not the only two axes) as a heatmap.

        Parameters
        ----------
        xaxis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the horizontal axis to overlay; if ``None`` *(default)*, use the first of the only two axes in this :py:class:`Hist <histbook.hist.Hist>`

        yaxis : ``None``, :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (lambda or string), or index position (integer)
            the vertical axis to overlay; if ``None`` *(default)*, use the second of the only two axes in this :py:class:`Hist <histbook.hist.Hist>`

        profile : ``None``, :py:class:`profile <histbook.axis.profile>`, algebraic expression (lambda or string) or index position (integer)
            if ``None`` *(default)*, display bin counts; otherwise, display profile means (and errors on the mean)

        width, height, title, config, xscale, yscale, colorscale : ``None`` or JSON
            graphical directives to pass to Vega-Lite

        Returns
        -------
        :py:class:`Plotable2d <histbook.vega.Plotable2d>`
        """
        if any(isinstance(x, OverlayChannel) for x in self._chain):
            raise TypeError("two dimensional plots can't be overlaid")
        if any(isinstance(x, StackChannel) for x in self._chain):
            raise TypeError("two dimensional plots can't be stacked")

        if xaxis is None and yaxis is None:
            if len(self._source._group + self._source._fixed) == 2:
                xaxis, yaxis = self._source._group + self._source._fixed
            else:
                raise TypeError("histogram doesn't have exactly two axes; an x and y must be specified for plotting")
        elif xaxis is None or yaxis is None:
            raise TypeError("xaxis and yaxis must both be None or neither be None")

        return Plotable2d(self, HeatmapChannel(self._asaxis(xaxis), self._asaxis(yaxis), self._asaxis(profile), width, height, title, config, xscale, yscale, colorscale))

class PlotableFrontends(object):
    def to(self, fcn):
        """Call ``fcn`` on the Vega-Lite JSON for this plot."""
        return fcn(self.vegalite())

    def ipyvega(self):
        """Draw this plot inline in a Jupyter notebook (not lab) using the vega library."""
        import vega
        return self.to(vega.VegaLite)

    def vegascope(self, canvas=None):
        """Draw this plot in a (possibly remote) browser using the VegaScope library."""
        import vegascope
        if canvas is None:
            if not hasattr(vegascope, "canvas"):
                vegascope.canvas = vegascope.LocalCanvas()
            canvas = vegascope.canvas
        return self.to(canvas)

    def altair(self, validate=True):
        """Return an altair.Chart of this plot using the Altair library."""
        import altair
        return self.to(lambda x: altair.Chart.from_dict(x, validate=validate))

    def _repr_mimebundle_(self, include=None, exclude=None, **kwargs):
        return {"application/vnd.vegalite.v2+json": self.vegalite()}

class Plotable1d(PlotableFrontends):
    """Mix-in for :py:class:`Channels <histbook.vega.Channel>` and :py:class:`Combinations <histbook.vega.Combination>` that can be plotted."""

    def __init__(self, source, item):
        if isinstance(source, PlottingChain):
            self._source = source._source
            self._chain = source._chain + (item,)
        else:
            self._source = source
            self._chain = (item,)

    def __repr__(self):
        return "".join(repr(x) for x in (self._source,) + self._chain)

    def __str__(self, indent="\n     ", paren=True):
        return ("(" if paren else "") + indent.join(repr(x) for x in (self._source,) + self._chain) + (")" if paren else "")

    @property
    def _last(self):
        return self._chain[-1]

    def _data(self, prefix, varname):
        error = self._last.error
        baseline = isinstance(self._last, (StepChannel, AreaChannel))

        if isinstance(self._last.axis, (histbook.axis.bin, histbook.axis.intbin, histbook.axis.split)):
            if isinstance(self._last, BarChannel):
                xtype = "ordinal"
            else:
                xtype = "quantitative"
        else:
            xtype = "nominal"

        profile = self._last.profile
        if profile is None:
            profiles = ()
        else:
            profiles = (profile,)

        projected = self._source.project(*(x.axis for x in self._chain))

        table = projected.table(*profiles, count=(profile is None), error=error, normalized=self._last.normalized, recarray=False)

        projectedorder = [x for x in projected.axis if not isinstance(x, histbook.axis.ProfileAxis)]
        lastj = projectedorder.index(self._last.axis)

        data = []
        domains = {}
        if error and baseline:
            shifts = {}

        def recurse(j, content, row, base):
            if j == len(projectedorder):
                if base:
                    row = row + ((0.0, 0.0) if error else (0.0,))
                else:
                    row = row + tuple(float(x) for x in content)

                datum = dict(prefix + tuple(zip([varname + str(i) for i in range(len(row))], row)))
                if datum[varname + str(j)] > 0 or (self._last.yscale != "log" and not (isinstance(self._last.yscale, dict) and self._last.yscale.get("type", None) == "log")):
                    data.append(datum)

            else:
                axis = projectedorder[j]
                if axis not in domains:
                    domains[axis] = set()
                domains[axis].update(axis.keys(content))

                if isinstance(axis, histbook.axis.intbin):
                    axis = axis.bin()

                for i, (n, x) in enumerate(axis.items(content)):
                    if isinstance(n, histbook.axis.Interval):
                        if j == lastj and xtype == "quantitative":
                            if numpy.isfinite(n.low) and numpy.isfinite(n.high):
                                low = n.low
                                if baseline and isinstance(axis, (histbook.axis.bin, histbook.axis.split)) and n.low == axis.low:
                                    recurse(j + 1, x, row + (n.low,), True)
                                    low += 1e-10*(axis.high - axis.low)
                                elif not baseline and isinstance(axis, (histbook.axis.bin, histbook.axis.split)):
                                    low = 0.5*(n.low + n.high)

                                recurse(j + 1, x, row + (low,), base)

                                if error and baseline:
                                    shifts[low] = 0.5*(n.low + n.high)

                                if baseline and isinstance(axis, (histbook.axis.bin, histbook.axis.split)) and n.high == axis.high:
                                    recurse(j + 1, x, row + (n.high,), True)

                        else:
                            recurse(j + 1, x, row + (str(n),), base)

                    elif isinstance(n, (bool, numpy.bool_, numpy.bool)):
                        recurse(j + 1, x, row + ("pass" if n else "fail",), base)

                    else:
                        recurse(j + 1, x, row + (str(n),), base)

        recurse(0, table, (), False)
        if error and baseline:
            for x in data:
                x[varname + str(lastj) + "c"] = shifts.get(x[varname + str(lastj)], x[varname + str(lastj)])

        return projectedorder, data, domains

    def _vegalite(self, axis, domains, varname):
        error = self._last.error
        baseline = isinstance(self._last, (StepChannel, AreaChannel))
        if isinstance(self._last.axis, (histbook.axis.bin, histbook.axis.intbin, histbook.axis.split)):
            if isinstance(self._last, BarChannel):
                xtype = "ordinal"
            else:
                xtype = "quantitative"
        else:
            xtype = "nominal"

        if isinstance(self._last, BarChannel):
            mark = "bar"
        elif isinstance(self._last, StepChannel):
            if xtype == "nominal":
                mark = "bar"
            else:
                mark = {"type": "line", "interpolate": "step-before"}
        elif isinstance(self._last, AreaChannel):
            if xtype == "nominal":
                mark = "bar"
            else:
                mark = {"type": "area", "interpolate": "step-before"}
        elif isinstance(self._last, LineChannel):
            mark = {"type": "line"}
        elif isinstance(self._last, MarkerChannel):
            mark = {"type": "point"}
        else:
            raise AssertionError(self._last)

        # FIXME: let the user override this with explicit xtitle, ytitle parameters
        xtitle = self._last.axis.expr
        if self._last.profile is None:
            if self._last.normalized:
                ytitle = "probability per bin"
            else:
                ytitle = "entries per bin"
        else:
            ytitle = self._last.profile.expr

        transform = []
        def makeorder(i, var, values):
            if len(values) == 1:
                return "if(datum.{0} === {1}, {2}, {3})".format(var, repr(values[0]), i, i + 1)
            elif len(values) > 1:
                return "if(datum.{0} === {1}, {2}, {3})".format(var, repr(values[0]), i, makeorder(i + 1, var, values[1:]))
            else:
                raise AssertionError(values)

        encoding = {"x": {"field": varname + str(axis.index(self._last.axis)), "type": xtype, "scale": {"zero": False}, "axis": {"title": xtitle}},
                    "y": {"field": varname + str(len(axis)), "type": "quantitative", "axis": {"title": ytitle}}}
        for channel in self._chain[:-1]:
            if isinstance(channel, OverlayChannel):
                overlayorder = [str(x) for x in sorted(domains[channel.axis])]
                encoding["color"] = {"field": varname + str(axis.index(channel.axis)), "type": "nominal", "legend": {"title": channel.axis.expr}, "scale": {"domain": overlayorder}}

            elif isinstance(channel, StackChannel):
                if channel.order is None:
                    stackorder = [str(x) for x in sorted(domains[channel.axis])]
                else:
                    stackorder = channel.order
                encoding["color"] = {"field": varname + str(axis.index(channel.axis)), "type": "nominal", "legend": {"title": channel.axis.expr}, "scale": {"domain": list(reversed(stackorder))}}
                encoding["y"]["aggregate"] = "sum"
                encoding["order"] = {"field": "stackorder", "type": "nominal"}
                transform.append({"calculate": makeorder(0, varname + str(axis.index(channel.axis)), stackorder), "as": "stackorder"})

            elif isinstance(channel, BesideChannel):
                # FIXME: sorting doesn't work??? https://github.com/vega/vega-lite/issues/2176
                encoding["column"] = {"field": varname + str(axis.index(channel.axis)), "type": "nominal", "header": {"title": channel.axis.expr}}

            elif isinstance(channel, BelowChannel):
                # FIXME: sorting doesn't work??? https://github.com/vega/vega-lite/issues/2176
                encoding["row"] = {"field": varname + str(axis.index(channel.axis)), "type": "nominal", "header": {"title": channel.axis.expr}}

            else:
                raise AssertionError(channel)

        if self._last.xscale is not None and "x" in encoding:
            if isinstance(self._last.xscale, dict):
                encoding["x"]["scale"] = self._last.xscale
            else:
                encoding["x"]["scale"] = {"type": self._last.xscale}
        if self._last.yscale is not None and "y" in encoding:
            if isinstance(self._last.yscale, dict):
                encoding["y"]["scale"] = self._last.yscale
            else:
                encoding["y"]["scale"] = {"type": self._last.yscale}
        if self._last.colorscale is not None and "color" in encoding:
            if isinstance(self._last.colorscale, dict):
                encoding["color"]["scale"] = self._last.colorscale
            else:
                encoding["color"]["scale"] = {"type": self._last.colorscale}
        if self._last.shapescale is not None and "shape" in encoding:
            if isinstance(self._last.shapescale, dict):
                encoding["shape"]["scale"] = self._last.shapescale
            else:
                encoding["shape"]["scale"] = {"type": self._last.shapescale}

        if not error:
            return [mark], [encoding], [transform]

        else:
            if error and baseline:
                errx = varname + str(axis.index(self._last.axis)) + "c"
            else:
                errx = varname + str(axis.index(self._last.axis))

            encoding2 = {"x": {"field": errx, "type": "quantitative"},
                         "y": {"field": "error-down", "type": "quantitative"},
                         "y2": {"field": "error-up", "type": "quantitative"}}

            transform2 = [{"calculate": "datum.{0} - datum.{1}".format(varname + str(len(axis)), varname + str(len(axis) + 1)), "as": "error-down"},
                          {"calculate": "datum.{0} + datum.{1}".format(varname + str(len(axis)), varname + str(len(axis) + 1)), "as": "error-up"}]

            return [mark, "rule"], [encoding, encoding2], [transform, transform2]
        
    def vegalite(self):
        """Return the Vega-Lite JSON for this plot."""

        axis, data, domains = self._data((), "a")
        marks, encodings, transforms = self._vegalite(axis, domains, "a")

        if len(marks) == 1:
            return self._options({"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
                                  "data": {"values": data},
                                  "mark": marks[0],
                                  "encoding": encodings[0],
                                  "transform": transforms[0]})

        else:
            return self._options({"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
                                  "data": {"values": data},
                                  "layer": [{"mark": m, "encoding": e, "transform": t} for m, e, t in zip(marks, encodings, transforms)]})

    def _options(self, out, config=True):
        if self._last.width is not None:
            out["width"] = self._last.width
        if self._last.height is not None:
            out["height"] = self._last.height
        if self._last.title is not None:
            out["title"] = self._last.title
        if config and self._last.config is not None:
            out["config"] = self._last.config
        return out

class Plotable2d(PlotableFrontends):
    """Mix-in for :py:class:`Channels <histbook.vega.Channel>` and :py:class:`Combinations <histbook.vega.Combination>` that can be plotted."""

    def __init__(self, source, item):
        if isinstance(source, PlottingChain):
            self._source = source._source
            self._chain = source._chain + (item,)
        else:
            self._source = source
            self._chain = (item,)

    def __repr__(self):
        return "".join(repr(x) for x in (self._source,) + self._chain)

    def __str__(self, indent="\n     ", paren=True):
        return ("(" if paren else "") + indent.join(repr(x) for x in (self._source,) + self._chain) + (")" if paren else "")

    @property
    def _last(self):
        return self._chain[-1]

    def _data(self, prefix, varname):
        profile = self._last.profile
        if profile is None:
            profiles = ()
        else:
            profiles = (profile,)

        projected = self._source.project(*([x.axis for x in self._chain[:-1]] + [self._last.xaxis, self._last.yaxis]))
        table = projected.table(*profiles, count=(profile is None), error=False, recarray=False)

        projectedorder = [x for x in projected.axis if not isinstance(x, histbook.axis.ProfileAxis)]
        lastj = (projectedorder.index(self._last.xaxis), projectedorder.index(self._last.yaxis))
        
        data = []
        domains = {}

        def recurse(j, content, row):
            if j == len(projectedorder):
                row = row + tuple(float(x) for x in content)

                datum = dict(prefix + tuple(zip([varname + str(i) for i in range(len(row))], row)))
                # FIXME: protect against logarithmic x and y axes
                data.append(datum)

            else:
                axis = projectedorder[j]
                if axis not in domains:
                    domains[axis] = set()
                domains[axis].update(axis.keys(content))

                if isinstance(axis, histbook.axis.intbin):
                    axis = axis.bin()

                for i, (n, x) in enumerate(axis.items(content)):
                    if isinstance(n, histbook.axis.Interval):
                        if j in lastj:
                            if numpy.isfinite(n.low) and numpy.isfinite(n.high):
                                recurse(j + 1, x, row + (0.5*(n.low + n.high),))
                        else:
                            recurse(j + 1, x, row + (str(n),))

                    elif isinstance(n, (bool, numpy.bool_, numpy.bool)):
                        recurse(j + 1, x, row + ("pass" if n else "fail",))

                    else:
                        recurse(j + 1, x, row + (str(n),))

        recurse(0, table, ())
        return projectedorder, data, domains

    def _vegalite(self, axis, domains, varname):
        if isinstance(self._last.xaxis, histbook.axis.bin):
            xtype = "quantitative"
            xbin = {"extent": [self._last.xaxis.low, self._last.xaxis.high], "minstep": self._last.xaxis.binwidth, "maxbins": self._last.xaxis.numbins + 1, "nice": False}
        elif isinstance(self._last.xaxis, histbook.axis.intbin):
            xtype = "quantitative"
            xbin = {"extent": [self._last.xaxis.min - 0.5, self._last.xaxis.max + 0.5], "minstep": self._last.xaxis.binwidth, "maxbins": self._last.xaxis.numbins + 1, "nice": False}
        elif isinstance(self._last.xaxis, histbook.axis.split):
            raise NotImplementedError("Vega-Lite doesn't support heatmaps of explicit axis splitting (yet?)")
        else:
            xtype = "nominal"
            xbin = False

        if isinstance(self._last.yaxis, histbook.axis.bin):
            ytype = "quantitative"
            ybin = {"extent": [self._last.yaxis.low, self._last.yaxis.high], "minstep": self._last.yaxis.binwidth, "maxbins": self._last.yaxis.numbins + 1, "nice": False}
        elif isinstance(self._last.yaxis, histbook.axis.intbin):
            ytype = "quantitative"
            ybin = {"extent": [self._last.yaxis.min - 0.5, self._last.yaxis.may + 0.5], "minstep": self._last.yaxis.binwidth, "maxbins": self._last.yaxis.numbins + 1, "nice": False}
        elif isinstance(self._last.yaxis, histbook.axis.split):
            raise NotImplementedError("Vega-Lite doesn't support heatmaps of explicit axis splitting (yet?)")
        else:
            ytype = "nominal"
            ybin = False

        # FIXME: let the user override this with explicit xtitle, ytitle, colortitle parameters
        xtitle = self._last.xaxis.expr
        ytitle = self._last.yaxis.expr
        if self._last.profile is None:
            colortitle = "entries per bin"
            colorzero = True
        else:
            colortitle = self._last.profile.expr
            colorzero = False

        encoding = {"x": {"field": varname + str(axis.index(self._last.xaxis)), "type": xtype, "scale": {"zero": False}, "axis": {"title": xtitle}, "bin": xbin},
                    "y": {"field": varname + str(axis.index(self._last.yaxis)), "type": ytype, "scale": {"zero": False}, "axis": {"title": ytitle}, "bin": ybin},
                    "color": {"field": varname + str(len(axis)), "type": "quantitative", "legend": {"title": colortitle}, "scale": {"zero": colorzero}}}
        for channel in self._chain[:-1]:
            if isinstance(channel, BesideChannel):
                # FIXME: sorting doesn't work??? https://github.com/vega/vega-lite/issues/2176
                encoding["column"] = {"field": varname + str(axis.index(channel.axis)), "type": "nominal", "header": {"title": channel.axis.expr}}

            elif isinstance(channel, BelowChannel):
                # FIXME: sorting doesn't work??? https://github.com/vega/vega-lite/issues/2176
                encoding["row"] = {"field": varname + str(axis.index(channel.axis)), "type": "nominal", "header": {"title": channel.axis.expr}}

            else:
                raise AssertionError(channel)

        if self._last.xscale is not None and "x" in encoding:
            if isinstance(self._last.xscale, dict):
                encoding["x"]["scale"] = self._last.xscale
            else:
                encoding["x"]["scale"] = {"type": self._last.xscale}
        if self._last.yscale is not None and "y" in encoding:
            if isinstance(self._last.yscale, dict):
                encoding["y"]["scale"] = self._last.yscale
            else:
                encoding["y"]["scale"] = {"type": self._last.yscale}
        if self._last.colorscale is not None and "color" in encoding:
            if isinstance(self._last.colorscale, dict):
                encoding["color"]["scale"] = self._last.colorscale
            else:
                encoding["color"]["scale"] = {"type": self._last.colorscale}

        return ["rect"], [encoding], [[]]

    def vegalite(self):
        """Return the Vega-Lite JSON for this plot."""

        axis, data, domains = self._data((), "a")
        marks, encodings, transforms = self._vegalite(axis, domains, "a")

        return self._options({"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
                              "data": {"values": data},
                              "mark": marks[0],
                              "encoding": encodings[0],
                              "transform": transforms[0]})

    def _options(self, out, config=True):
        if self._last.width is not None:
            out["width"] = self._last.width
        if self._last.height is not None:
            out["height"] = self._last.height
        if self._last.title is not None:
            out["title"] = self._last.title
        if config and self._last.config is not None:
            out["config"] = self._last.config
        return out

class Combination(PlotableFrontends):
    """Abstract class for :py:class:`Plotable1ds <histbook.vega.Plotable1d>` that have been combined as an overlay or side-by-side plots."""

    def __init__(self, plotables, types, opts):
        self._plotables = []
        for arg in plotables:           # first level: for varargs
            try:
                iter(arg)
            except:
                arg = [arg]
            for plotable in arg:        # second level: for iterators
                if not isinstance(plotable, types):
                    raise TypeError("only Plotable1ds can be combined with {0}".format(self.__class__.__name__))
                self._plotables.append(plotable)

        self.config = opts.pop("config", None)
        if len(opts) > 0:
            raise TypeError("unrecognized options for {0}: {1}".format(self.__class__.__name__, " ".join(opts)))

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(repr(x) for x in self._plotables))

    def __str__(self, indent="\n    ", paren=False):
        return "{0}({1})".format(self.__class__.__name__, "".join(indent + x.__str__(indent + "    ", False) for x in self._plotables))

    def _varname(self, i):
        out = []
        i += 1
        while i > 0:
            out.append("abcdefghijklmnopqrstuvwxyz"[i % 26])
            i //= 26
        return "".join(reversed(out))

    def _collectdata(self):
        allaxis = []
        alldata = []
        alldomains = []

        def recurse(i, plotables):
            for plotable in plotables:
                if isinstance(plotable, Combination):
                    i = recurse(i, plotable._plotables)
                else:
                    varname = self._varname(i)
                    axis, data, domains = plotable._data((("id", varname),), varname)
                    allaxis.append(axis)
                    alldata.extend(data)
                    alldomains.append(domains)
                    i += 1
            return i

        recurse(0, self._plotables)
        return allaxis, alldata, alldomains

    def _options(self, out):
        config = {}

        def recurse(node):
            if isinstance(node, Combination):
                for x in node._plotables:
                    recurse(x)
            elif node._last.config is not None:
                config.update(node._last.config)

        recurse(self)

        if self.config is not None:
            config.update(self.config)
        
        if len(config) != 0:
            out["config"] = config

        return out

class overlay(Combination):
    """:py:class:`Plotable1d <histbook.vega.Plotable1d>` overlaying two or more independently produced :py:class:`Plotable1ds <histbook.vega.Plotable1d>`."""

    def __init__(self, *plotables, **opts):
        super(overlay, self).__init__(plotables, (Plotable1d,), opts)

    def _fill(self, i, allaxis, alldomains, tofill):
        for plotable in self._plotables:
            varname = self._varname(i)
            marks, encodings, transforms = plotable._vegalite(allaxis[i], alldomains[i], varname)
            thislayer = [{"filter": {"field": "id", "equal": varname}}]

            if len(marks) == 1:
                tofill.append(plotable._options({"mark": marks[0],
                                                 "encoding": encodings[0],
                                                 "transform": transforms[0] + thislayer}, config=False))
            else:
                for m, e, t in zip(marks, encodings, transforms):
                    tofill.append(plotable._options({"mark": m, "encoding": e, "transform": t + thislayer}, config=False))
            i += 1

        return i

    def vegalite(self):
        allaxis, alldata, alldomains = self._collectdata()

        out = {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
               "data": {"values": alldata},
               "layer": []}

        self._fill(0, allaxis, alldomains, out["layer"])
        return self._options(out)

class beside(Combination):
    """:py:class:`Plotable1d <histbook.vega.Plotable1d>` displaying two or more independently produced :py:class:`Plotable1ds <histbook.vega.Plotable1d>` beside each other horizontally."""

    def __init__(self, *plotables, **opts):
        super(beside, self).__init__(plotables, (Plotable1d, Plotable2d, overlay, below), opts)
        if any(isinstance(x, BesideChannel) for x in self._plotables):
            raise TypeError("cannot place plots beside each other that are already split with beside (can do beside and below)")

    def _fill(self, i, allaxis, alldomains, tofill):
        for plotable in self._plotables:
            if isinstance(plotable, overlay):
                tofill.append({"layer": []})
                i = plotable._fill(i, allaxis, alldomains, tofill[-1]["layer"])

            elif isinstance(plotable, below):
                tofill.append({"vconcat": []})
                i = plotable._fill(i, allaxis, alldomains, tofill[-1]["vconcat"])

            else:
                varname = self._varname(i)
                marks, encodings, transforms = plotable._vegalite(allaxis[i], alldomains[i], varname)
                thislayer = [{"filter": {"field": "id", "equal": varname}}]

                if len(marks) == 1:
                    tofill.append(plotable._options({"mark": marks[0], "encoding": encodings[0], "transform": transforms[0] + thislayer}, config=False))
                else:
                    tofill.append({"layer": [plotable._options({"mark": m, "encoding": e, "transform": t}, config=False) for m, e, t in zip(marks, encodings, transforms)]})
                i += 1

        return i

    def vegalite(self):
        allaxis, alldata, alldomains = self._collectdata()

        out = {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
               "data": {"values": alldata},
               "hconcat": []}

        self._fill(0, allaxis, alldomains, out["hconcat"])
        return self._options(out)

class below(Combination):
    """:py:class:`Plotable1d <histbook.vega.Plotable1d>` displaying two or more independently produced :py:class:`Plotable1ds <histbook.vega.Plotable1d>` below each other vertically."""

    def __init__(self, *plotables, **opts):
        super(below, self).__init__(plotables, (Plotable1d, Plotable2d, overlay, beside), opts)
        if any(isinstance(x, BelowChannel) for x in self._plotables):
            raise TypeError("cannot place plots below each other that are already split with below (can do beside and below)")

    def _fill(self, i, allaxis, alldomains, tofill):
        for plotable in self._plotables:
            if isinstance(plotable, overlay):
                tofill.append({"layer": []})
                i = plotable._fill(i, allaxis, alldomains, tofill[-1]["layer"])

            elif isinstance(plotable, beside):
                tofill.append({"hconcat": []})
                i = plotable._fill(i, allaxis, alldomains, tofill[-1]["hconcat"])

            else:
                varname = self._varname(i)
                marks, encodings, transforms = plotable._vegalite(allaxis[i], alldomains[i], varname)
                thislayer = [{"filter": {"field": "id", "equal": varname}}]

                if len(marks) == 1:
                    tofill.append(plotable._options({"mark": marks[0], "encoding": encodings[0], "transform": transforms[0] + thislayer}, config=False))
                else:
                    tofill.append({"layer": [plotable._options({"mark": m, "encoding": e, "transform": t}, config=False) for m, e, t in zip(marks, encodings, transforms)]})
                i += 1

        return i

    def vegalite(self):
        allaxis, alldata, alldomains = self._collectdata()

        out = {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
               "data": {"values": alldata},
               "vconcat": []}

        self._fill(0, allaxis, alldomains, out["vconcat"])
        return self._options(out)

class grid(Combination):
    """:py:class:`Plotable1d <histbook.vega.Plotable1d>` displaying two or more independently produced :py:class:`Plotable1ds <histbook.vega.Plotable1d>` in a rectangular grid of `numcol` columns."""

    def __init__(self, numcol, *plotables, **opts):
        super(grid, self).__init__(plotables, (Plotable1d, Plotable2d, overlay), opts)
        if any(isinstance(x, BesideChannel) for x in self._plotables) or any(isinstance(x, BelowChannel) for x in self._plotables):
            raise TypeError("cannot place plots in a grid that are already split with beside or below")
        self.numcol = numcol

    def _fill(self, i, allaxis, alldomains, tofill):
        for plotable in self._plotables:
            if len(tofill[-1]["hconcat"]) >= self.numcol:
                tofill.append({"hconcat": []})

            if isinstance(plotable, overlay):
                tofill[-1]["hconcat"].append({"layer": []})
                i = plotable._fill(i, allaxis, alldomains, tofill[-1]["hconcat"][-1]["layer"])

            else:
                varname = self._varname(i)
                marks, encodings, transforms = plotable._vegalite(allaxis[i], alldomains[i], varname)
                thislayer = [{"filter": {"field": "id", "equal": varname}}]

                if len(marks) == 1:
                    tofill[-1]["hconcat"].append(plotable._options({"mark": marks[0], "encoding": encodings[0], "transform": transforms[0] + thislayer}, config=False))

                else:
                    tofill[-1]["hconcat"].append({"layer": [plotable._options({"mark": m, "encoding": e, "transform": t}, config=False) for m, e, t in zip(marks, encodings, transforms)]})

                i += 1

        return i

    def vegalite(self):
        allaxis, alldata, alldomains = self._collectdata()

        out = {"$schema": "https://vega.github.io/schema/vega-lite/v2.json",
               "data": {"values": alldata},
               "vconcat": [{"hconcat": []}]}

        self._fill(0, allaxis, alldomains, out["vconcat"])
        return self._options(out)
