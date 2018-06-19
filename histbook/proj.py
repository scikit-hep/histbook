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

import math
import numbers

import numpy

import histbook.axis
import histbook.expr

class AxisTuple(tuple):
    """An ordered sequence of :py:class:`Axis <histbook.axis.Axis>` returned by :py:meth:`Hist.axis <histbook.hist.Hist.axis>`."""
    def __getitem__(self, item):
        """Get an axis by algebraic expression (string) or index position (integer)."""
        if isinstance(item, (numbers.Integral, numpy.integer)):
            return super(AxisTuple, self).__getitem__(item)
        else:
            expr = histbook.expr.Expr.parse(item, defs=self._defs)
            for axis in self:
                if expr == axis._parsed:
                    return axis
            raise IndexError("no such axis: {0}".format(repr(str(expr))))

    def _findbyclass(self, expr, cls, kwargs):
        expr = histbook.expr.Expr.parse(expr, defs=self._defs)
        for axis in self:
            if isinstance(axis, cls) and axis._parsed == expr and all(hasattr(axis, n) and getattr(axis, n) == x for n, x in kwargs.items()):
                return axis
        raise IndexError("no such axis: {0}({1}{2})".format(cls.__name__, repr(str(expr)), "".join(", {0}={1}".format(n, kwargs[n]) for n in sorted(kwargs))))

    def groupby(self, expr, **kwargs):
        """Get a :py:class:`groupby <histbook.axis.groupby>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.groupby, kwargs)

    def groupbin(self, expr, **kwargs):
        """Get a :py:class:`groupbin <histbook.axis.groupbin>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.groupbin, kwargs)

    def bin(self, expr, **kwargs):
        """Get a :py:class:`bin <histbook.axis.bin>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.bin, kwargs)

    def intbin(self, expr, **kwargs):
        """Get a :py:class:`intbin <histbook.axis.intbin>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.intbin, kwargs)

    def split(self, expr, **kwargs):
        """Get a :py:class:`split <histbook.axis.split>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.split, kwargs)

    def cut(self, expr, **kwargs):
        """Get a :py:class:`cut <histbook.axis.cut>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.cut, kwargs)

    def profile(self, expr, **kwargs):
        """Get a :py:class:`profile <histbook.axis.profile>` axis by algebraic expression (string) and any provided arguments."""
        return self._findbyclass(expr, histbook.axis.profile, kwargs)

class Projectable(object):
    """Mix-in for :py:class:`Hist <histbook.hist.Hist>` methods that provide selection, projection, and rebinning."""
    @property
    def axis(self):
        """The axes that define a histogram's binning of space."""
        out = AxisTuple(self._group + self._fixed + self._profile)
        out._defs = self._defs
        return out

    def rebin(self, axis, edges):
        """
        Reduce the number of bins by combining existing bins at a specified set of ``edges``.

        Parameters
        ----------
        axis : :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (string), or index position (integer)
            the axis to rebin

        edges : iterable of numbers
            new bin edges; must be a subset of existing bin edges

        Returns
        -------
        :py:class:`Hist <histbook.hist.Hist>`
            a rebinned histogram.
        """
        if not isinstance(axis, histbook.axis.Axis):
            expr = histbook.expr.Expr.parse(axis, defs=self._defs)
            for x in self._group + self._fixed:
                if isinstance(x, histbook.axis._RebinSplit) and expr == x._parsed:
                    axis = x
                    break

        for index, x in enumerate(self._group + self._fixed):
            if isinstance(x, histbook.axis._RebinSplit) and axis == x:
                axis = x
                break
        else:
            raise IndexError("no such rebinnable axis: {0}".format(axis))

        if isinstance(axis, histbook.axis.GroupAxis):
            newaxis, newcontent = axis._rebinsplit(edges, self._content, index)
        else:
            newaxis, newcontent = axis._rebinsplit(edges, self._content, index - len(self._group))

        outaxis = [newaxis if i == index else x for i, x in enumerate(self._group + self._fixed + self._profile)]
        out = self.__class__(*outaxis, weight=self._weightoriginal, filter=self._filteroriginal, defs=dict(self._defs), attachment=dict(self._attachment))
        out._content = newcontent
        return out

    def rebinby(self, axis, factor):
        """
        Reduce the number of bins by an approximate ``factor`` by combining existing bins.

        Parameters
        ----------
        axis : :py:class:`Axis <histbook.axis.Axis>`, algebraic expression (string), or index position (integer)
            the axis to rebin

        factor : positive integer
            number of bins to combine into a single bin (inexact if the number of bins in ``axis`` is not an exact multiple of ``factor``)

        Returns
        -------
        :py:class:`Hist <histbook.hist.Hist>`
            a rebinned histogram.
        """
        if not isinstance(factor, (numbers.Integral, numpy.integer)) or factor <= 0:
            raise TypeError("factor must be a positive integer")

        if not isinstance(axis, histbook.axis.Axis):
            expr = histbook.expr.Expr.parse(axis, defs=self._defs)
            for x in self._group + self._fixed:
                if isinstance(x, histbook.axis._RebinFactor) and expr == x._parsed:
                    axis = x
                    break

        for index, x in enumerate(self._group + self._fixed):
            if isinstance(x, histbook.axis._RebinFactor) and axis == x:
                axis = x
                break
        else:
            raise IndexError("no such rebinnable axis: {0}".format(axis))

        if isinstance(axis, histbook.axis.GroupAxis):
            newaxis, newcontent = axis._rebinsplit(factor, self._content, index)
        else:
            newaxis, newcontent = axis._rebinsplit(factor, self._content, index - len(self._group))

        outaxis = [newaxis if i == index else x for i, x in enumerate(self._group + self._fixed + self._profile)]
        out = self.__class__(*outaxis, weight=self._weightoriginal, filter=self._filteroriginal, defs=dict(self._defs), attachment=dict(self._attachment))
        out._content = newcontent
        return out

    def drop(self, *profile):
        """
        Remove one or more :py:class:`profile <histbook.axis.profile>` axes.

        Parameters
        ----------
        *profile : :py:class:`profile <histbook.axis.profile>`, algebraic expression (string), or index position (integer)
            the axis or axes to drop

        Returns
        -------
        :py:class:`Hist <histbook.hist.Hist>`
            a histogram without the selected ``profiles``.
        """
        if len(profile) == 0:
            raise IndexError("no profile axis given")
        profile = [x if isinstance(x, histbook.axis.Axis) else self.axis.profile(x) for x in profile]
        for prof in profile:
            if prof not in self._profile:
                raise IndexError("no such profile axis: {0}".format(prof))
        
        axis = []
        index = []
        for i, prof in enumerate(self._profile):
            if prof not in profile:
                axis.append(prof)
                index.append(i)

        index.append(self._sumwindex)
        if self._weightoriginal is not None:
            index.append(self._sumw2index)

        slc = (slice(None),) * (len(self._shape) - 1) + (index,)

        def dropcontent(content):
            if isinstance(content, dict):
                return dict((n, dropcontent(x)) for n, x in content.items())
            else:
                return content[slc]

        out = self.__class__(*(self._group + self._fixed + tuple(axis)), weight=self._weightoriginal, filter=self._filteroriginal, defs=dict(self._defs), attachment=dict(self._attachment))
        if self._content is not None:
            out._content = dropcontent(self._content)
        return out

    def project(self, *axis):
        """
        Project onto a given set of :py:class:`axis <histbook.axis.Axis>`.

        Parameters
        ----------
        *axis : :py:class:`Axis <histbook.axis.axis>`, algebraic expression (string), or index position (integer)
            the axis or axes to keep (all :py:class:`profile <histbook.axis.profile>` axes are kept)

        Returns
        -------
        :py:class:`Hist <histbook.hist.Hist>`
            a histogram projected onto the selected axis or axes.
        """
        allaxis = self._group + self._fixed

        axis = [x if isinstance(x, histbook.axis.Axis) else self.axis[x] for x in axis]
        for x in axis:
            if x not in allaxis:
                raise IndexError("no such axis: {0}".format(x))

        def projarray(content):
            return numpy.sum(content, tuple(i for i, x in enumerate(self._fixed) if x not in axis))

        def addany(left, right):
            if isinstance(left, dict) and isinstance(right, dict):
                out = dict((n, addany(x, right[n]) if n in right else x) for n, x in left.items())
                for n, x in right.items():
                    if n not in left:
                        out[n] = x
                return out
            else:
                return left + right

        def addall(values):
            assert len(values) != 0
            left = values[:len(values) // 2]
            right = values[len(values) // 2:]
            if len(left) == 0:
                return right
            elif len(right) == 0:
                return left
            elif len(left) == 1 and len(right) == 1:
                return addany(left[0], right[0])
            else:
                return addall([addall(left)] + [addall(right)])
            
        def projcontent(j, content):
            if j < len(self._group):
                if allaxis[j] in axis:
                    return dict((n, projcontent(j + 1, x)) for n, x in content.items())
                else:
                    return addall([projcontent(j + 1, x) for x in content.values()])
            else:
                return projarray(content)

        outaxis = [x for x in allaxis if x in axis] + [x for x in self._profile]
        out = self.__class__(*outaxis, weight=self._weightoriginal, filter=self._filteroriginal, defs=dict(self._defs), attachment=dict(self._attachment))
        if self._content is not None:
            out._content = projcontent(0, self._content)
        return out

    def select(self, expr, tolerance=1e-12):
        """
        Eliminate bins by selecting data with a boolean ``expr``.

        Parameters
        ----------
        expr : algebraic expression (string)
            boolean expression of data to keep; selection thresholds must align with bin edges with the right inequality (e.g. ``<`` vs ``<=``)

        tolerance : small positive number
            absolute difference between selection threshold and bin edge to qualify as a match

        Returns
        -------
        :py:class:`Hist <histbook.hist.Hist>`
            a histogram with data removed (fewer bins)
        """
        expr = histbook.expr.Expr.parse(expr, defs=self._defs)

        if isinstance(expr, histbook.expr.LogicalAnd):
            out = None
            for arg in expr.args:
                if out is None:
                    out = self._select(arg, tolerance)
                else:
                    out = out._select(arg, tolerance)
            return out

        else:
            return self._select(expr, tolerance)

    def _select(self, expr, tolerance):
        if not isinstance(expr, (histbook.expr.Relation, histbook.expr.Logical, histbook.expr.Predicate, histbook.expr.Name)):
            raise TypeError("select expression must be boolean, not {0}".format(repr(str(expr))))

        def asconst(expr):
            if isinstance(expr, histbook.expr.Const):
                return expr

            elif isinstance(expr, histbook.expr.Name) and expr.value in histbook.expr.Expr.maybeconstants:
                return histbook.expr.Const(histbook.expr.Expr.maybeconstants[expr.value])

            elif isinstance(expr, histbook.expr.PlusMinus):
                out = expr.const
                for x in expr.pos:
                    c = asconst(x)
                    if c is None:
                        return None
                    out += c.value
                for x in expr.neg:
                    c = asconst(x)
                    if c is None:
                        return None
                    out -= c.value
                return histbook.expr.Const(out)

            elif isinstance(expr, histbook.expr.TimesDiv):
                out = expr.const
                for x in expr.pos:
                    c = asconst(x)
                    if c is None:
                        return None
                    out *= c.value
                for x in expr.neg:
                    c = asconst(x)
                    if c is None:
                        return None
                    out /= c.value
                return histbook.expr.Const(out)

            else:
                return None

        def normalizeexpr(expr):
            if isinstance(expr, histbook.expr.Relation):
                cutcmp = expr.cmp
                if asconst(expr.left) is not None and asconst(expr.right) is None:
                    cutvalue, cutexpr = asconst(expr.left), expr.right
                    cutcmp = {"<": ">", "<=": ">="}.get(cutcmp, cutcmp)
                elif asconst(expr.left) is None and asconst(expr.right) is not None:
                    cutexpr, cutvalue = expr.left, asconst(expr.right)
                elif asconst(expr.left) is not None and asconst(expr.right) is not None:
                    raise TypeError("select expression must have a variable left or right hand side, not {0}".format(repr(str(expr))))
                else:
                    raise TypeError("select expression must have a constant left or right hand side, not {0}".format(repr(str(expr))))

                cutvalue = cutvalue.value   # unbox to Python

            elif isinstance(expr, histbook.expr.Predicate):
                if expr.positive:
                    cutexpr = histbook.expr.Name(expr.value)
                    cutcmp = "=="
                    cutvalue = True
                else:
                    cutexpr = histbook.expr.Name(expr.value)
                    cutcmp = "!="
                    cutvalue = True

            else:
                cutexpr = expr
                cutcmp = "=="
                cutvalue = True

            return cutexpr, cutcmp, cutvalue

        cutexpr, cutcmp, cutvalue = normalizeexpr(expr)

        allaxis = self._group + self._fixed

        def logical(cutexpr, cutcmp, cutvalue, axis, cutaxis, newaxis, cutslice, closest, closestaxis, wrongcmpaxis):
            if isinstance(axis, (histbook.axis.groupby, histbook.axis.groupbin)) and isinstance(cutexpr, histbook.expr.LogicalOr):
                good = True
                orslice = None
                for andexpr in cutexpr.args:
                    andslice = None
                    for xpr in andexpr.args:
                        xpr, cmp, value = normalizeexpr(xpr)
                        check, _, slice1, _, _, _ = logical(xpr, cmp, value, axis, cutaxis, newaxis, cutslice, closest, closestaxis, wrongcmpaxis)
                        if check is None:
                            good = False
                            break
                        elif andslice is None:
                            andslice = slice1
                        else:
                            slice2 = andslice
                            andslice = lambda x: slice1(x) and slice2(x)

                    if not good:
                        break
                    elif orslice is None:
                        orslice = andslice
                    else:
                        slice1 = andslice
                        slice2 = orslice
                        orslice = lambda x: slice1(x) or slice2(x)

                if good:
                    return axis, axis, orslice, None, None, None

            if isinstance(axis, histbook.axis.cut) and expr == axis._parsed:
                newaxis, cutslice, close, wrongcmp = axis._select("==", True, tolerance)
                if newaxis is not None:
                    return axis, newaxis, cutslice, closest, wrongcmpaxis, closestaxis

            if cutexpr == axis._parsed:
                newaxis, cutslice, close, wrongcmp = axis._select(cutcmp, cutvalue, tolerance)
                if newaxis is not None:
                    cutaxis = axis
                else:
                    if close is not None and (closest is None or abs(cutvalue - close) < abs(cutvalue - closest)):
                        closest = close
                        closestaxis = axis
                    if wrongcmp:
                        wrongcmpaxis = axis

            return cutaxis, newaxis, cutslice, closest, wrongcmpaxis, closestaxis

        cutaxis, newaxis, cutslice, closest, wrongcmpaxis, closestaxis = None, None, None, None, None, None
        for axis in allaxis:
            cutaxis, newaxis, cutslice, closest, wrongcmpaxis, closestaxis = logical(cutexpr, cutcmp, cutvalue, axis, cutaxis, newaxis, cutslice, closest, wrongcmpaxis, closestaxis)
            if cutaxis is not None:
                break
        else:
            if wrongcmpaxis is not None:
                raise ValueError("no axis can select {0} (axis {1} has the wrong inequality; low edges are {2})".format(repr(str(expr)), wrongcmpaxis, "closed" if wrongcmpaxis.closedlow else "open"))
            elif closestaxis is not None:
                raise ValueError("no axis can select {0} (axis {1} has an edge at {2})".format(repr(str(expr)), closestaxis, repr(closest)))
            else:
                raise ValueError("no axis can select {0}".format(repr(str(expr))))

        return self._selectaxis(cutaxis, newaxis, cutslice, True)

    def _selectaxis(self, cutaxis, newaxis, cutslice, dropnull):
        allaxis = self._group + self._fixed

        def cutcontent(i, content):
            if content is None:
                return None

            if isinstance(allaxis[i], (histbook.axis.groupby, histbook.axis.groupbin)):
                if allaxis[i] is cutaxis:
                    return dict((n, x) for n, x in content.items() if cutslice(n))
                else:
                    return dict((n, cutcontent(i + 1, x)) for n, x in content.items())

            else:
                slc = tuple(cutslice if j < len(allaxis) and allaxis[j] is cutaxis else slice(None) for j in range(i, len(allaxis) + 1))
                out = content[slc].copy()
                if dropnull and isinstance(newaxis, histbook.axis._nullaxis):
                    out.shape = tuple(sh for sh, sl in zip(out.shape, slc) if sl is not cutslice)
                return out

        axis = [newaxis if x is cutaxis else x for x in self._group + self._fixed + self._profile]
        if dropnull:
            axis = [x for x in axis if not isinstance(x, histbook.axis._nullaxis)]
        out = self.__class__(*axis, weight=self._weightoriginal, filter=self._filteroriginal, defs=dict(self._defs), attachment=dict(self._attachment))
        if self._content is not None:
            out._content = cutcontent(0, self._content)
        return out

    def table(self, *profile, **opts):
        """
        Return histogram data as a table of counts and, optionally, dependent variables (profiles).

        Parameters
        ----------
        *profile : :py:class:`profile <histbook.axis.profile>`
            the dependent variables to include in the table

        Keyword Arguments
        -----------------
        count : bool
            if ``True`` *(default)*, include the (possibly weighted) count of entries in each bin

        effcount : bool
            if ``True`` *(not default)*, include the effective count, which is used to convert between weighted profile errors and weighted profile spreads (equal to ``count`` for unweighted data)

        error : bool
            if ``True`` *(default)*, include "errors" on all parameters (uncertainty in the mean of the distribution the count or profile average represents)

        normalized : bool
            if ``True`` *(not default)*, scale each ``count`` and ``err(count)`` such that the sum over counts times bin widths is 1; does not affect profiles

        recarray : bool
            if ``True`` *(default)*, return results as a Numpy record array, which is rank-2 with named columns; if ``False``, return a plain Numpy array, which is rank-N for N axes and has no column labels.

        columns : bool
            if ``True`` *(not default)*, return a 2-tuple in which the second argument is a list of column labels.
        """
        count = opts.pop("count", True)
        effcount = opts.pop("effcount", False)
        error = opts.pop("error", True)
        normalized = opts.pop("normalized", False)
        recarray = opts.pop("recarray", True)
        showcolumns = opts.pop("columns", False)
        if len(opts) > 0:
            raise TypeError("unrecognized options for Hist.table: {0}".format(" ".join(opts)))

        self._prefill()

        profile = [x if isinstance(x, histbook.axis.Axis) else self.axis.profile(x) for x in profile]
        profileindex = []
        for prof in profile:
            if prof not in self._profile:
                raise IndexError("no such profile axis: {0}".format(prof))
            else:
                profileindex.append(self._profile.index(prof))

        profile = [self._profile[i] for i in profileindex]

        columns = []
        if count:
            columns.append("count()")
            if error:
                columns.append("err(count())")
        if effcount:
            columns.append("effcount()")
        for prof in profile:
            columns.append(str(prof.expr))
            if error:
                columns.append("err({0})".format(str(prof.expr)))

        if normalized:
            binwidths = numpy.full(self._shape[:-1], numpy.inf)

            groupbins = 1.0
            for axis in self._group:
                if isinstance(axis, histbook.axis.groupbin):
                    groupbins *= axis.binwidth
            binwidths[tuple(axis.finiteslice for axis in self._group + self._fixed)] = groupbins

            for i, axis in enumerate(self._fixed):
                if callable(axis.binwidth):
                    binwidth = numpy.array([axis.binwidth(k) for k in range(axis.numbins)])
                else:
                    binwidth = axis.binwidth

                binwidths[tuple(axis.finiteslice if i == j else slice(None) for j, axis in enumerate(self._fixed))] *= binwidth

        def handlearray(content):
            content = content.reshape((-1, self._shape[-1]))

            out = numpy.zeros((content.shape[0], len(columns)), dtype=content.dtype)
            outindex = 0
            
            sumw = content[:, self._sumwindex]
            if count:
                out[:, outindex] = sumw
                countindex = outindex
                outindex += 1

                if error:
                    if self._weightparsed is None:
                        out[:, outindex] = numpy.sqrt(sumw)
                    else:
                        out[:, outindex] = numpy.sqrt(content[:, self._sumw2index])
                    errorindex = outindex
                    outindex += 1

                if normalized:
                    shaped = binwidths.reshape(content.shape[:-1])
                    total = (out[:, countindex] / shaped).sum()
                    correction = total * shaped
                    out[:, countindex] /= correction
                    if error:
                        out[:, errorindex] /= correction

            if len(profile) > 0 or effcount:
                good = sumw > 0
                sumw = sumw[good]
                if self._weightparsed is None:
                    effcnt = sumw
                else:
                    effcnt = numpy.square(sumw) / content[good, self._sumw2index]

            if effcount:
                out[good, outindex] = effcnt
                outindex += 1

            for prof in profile:
                out[good, outindex] = content[good, prof._sumwxindex] / sumw
                outindex += 1
                if error:
                    out[good, outindex] = numpy.sqrt(((content[good, prof._sumwx2index] / sumw) - numpy.square(out[good, outindex - 1])) / effcnt)
                    outindex += 1

            if recarray:
                return out.view([(x, content.dtype) for x in columns]).reshape(self._shape[:-1])
            else:
                return out.reshape(self._shape[:-1] + (outindex,))

        def handle(content):
            if isinstance(content, dict):
                return dict((n, handle(x)) for n, x in content.items())
            else:
                return handlearray(content)

        out = handle(self._content)

        if showcolumns:
            return out, columns
        else:
            return out

    def fraction(self, *cut, **opts):
        """
        Return a table of the fraction of entries that pass a set of cuts in each bin.

        Parameters
        ----------
        *cut : :py:class:`profile <histbook.axis.cut>`
            the cut axis or axes to include in the table

        Keyword Arguments
        -----------------
        count : bool
            if ``True`` *(default)*, include the (possibly weighted) count of entries in each bin (denominator of the fraction)

        error : string or ``None``
            if not ``None``, include "errors" on all parameters (uncertainty in the mean of the distribution the count or fraction represents); options are ``"clopper-pearson"``, ``"normal"`` (default), ``"wilson"``, ``"agresti-coull"``, ``"feldman-cousins"``, ``"jeffrey"``, ``"bayesian-uniform"``

        level : number or iterable of numbers
            confidence level or levels at which to evaluate error; default is erf(sqrt(0.5)) or 0.6827, otherwise known as "one sigma"

        recarray : bool
            if ``True`` *(default)*, return results as a Numpy record array, which is rank-2 with named columns; if ``False``, return a plain Numpy array, which is rank-N for N axes and has no column labels.

        columns : bool
            if ``True`` *(not default)*, return a 2-tuple in which the second argument is a list of column labels.
        """
        return self._fraction(cut, opts, False)

    ### FIXME: express levels in sigmas, rather than confidence levels

    def _fraction(self, cut, opts, return_denomhist):
        count = opts.pop("count", True)
        error = opts.pop("error", "normal")
        levels = opts.pop("level", math.erf(math.sqrt(0.5)))
        if isinstance(levels, (numbers.Real, numpy.floating, numpy.integer)):
            levels = (levels,)
        recarray = opts.pop("recarray", True)
        showcolumns = opts.pop("columns", False)
        if len(opts) > 0:
            raise TypeError("unrecognized options for Hist.table: {0}".format(" ".join(opts)))

        self._prefill()

        cut = [x if isinstance(x, histbook.axis.Axis) else self.axis.cut(x) for x in cut]

        cutindex = []
        for c in cut:
            if c not in self._fixed or not isinstance(c, histbook.axis.cut):
                raise IndexError("no such cut axis: {0}".format(c))
            else:
                cutindex.append(self._fixed.index(c))
        cut = [self._fixed[i] for i in cutindex]

        noprofiles = self.drop(*self._profile)
        denomhist = noprofiles.project(*[x for x in self._group + self._fixed if x not in cut])
        cuthist = []
        for c in cut:
            proj = noprofiles.project(*[x for x in self._group + self._fixed if x is c or x not in cut])
            for cutaxis in proj._fixed:
                if isinstance(cutaxis, histbook.axis.cut) and c._parsed == cutaxis._parsed:
                    break
            else:
                raise AssertionError(proj._fixed)
            cuthist.append(proj._selectaxis(cutaxis, histbook.axis._nullaxis(), slice(1, 2), False))

        columns = []
        if count:
            columns.append("count()")
        for c in cut:
            columns.append(str(c.expr))
            if error:
                for level in levels:
                    if level == math.erf(math.sqrt(0.5)):
                        columns.append("err({0})".format(str(c.expr)))
                    else:
                        columns.append("err({0}, {1:3g})".format(str(c.expr), level))

        def level2sigmas(level):
            try:
                from scipy.special import erfinv
            except ImportError:
                a3 = math.pi / 12.0
                a5 = math.pi**2 * 7.0/480.0
                a7 = math.pi**3 * 127.0/40320.0
                a9 = math.pi**4 * 4369.0/5806080.0
                a11 = math.pi**5 * 34807.0/182476800.0
                return 0.5*math.sqrt(math.pi)*(level + a3*level**3 + a5*level**5 + a7*level**7 + a9*level**9 + a11*level**11)
            else:
                return float(erfinv(level) * math.sqrt(2))

        def handlearray(denomcontent, cutcontent):
            denomcontent = denomcontent.reshape((-1, denomhist._shape[-1]))

            out = numpy.zeros((denomcontent.shape[0], len(columns)), dtype=numpy.float64)
            outindex = 0

            sumw = denomcontent[:, denomhist._sumwindex]
            if count:
                out[:, outindex] = sumw
                outindex += 1

            good = sumw > 0
            denom = sumw[good]
            # if denomhist._weightoriginal is not None:
            #     denomw2 = denomcontent[good, denomhist._sumw2index]

            for i in range(len(cut)):
                cc = cutcontent[i].reshape((-1, cuthist[i]._shape[-1]))
                p = out[good, outindex] = cc[good, cuthist[i]._sumwindex] / denom
                outindex += 1

                if not error:
                    pass

                # https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
                # https://root.cern.ch/root/html602/src/TEfficiency.cxx.html

                elif error == "clopper-pearson":    # recommended by PDG; FIXME: should be the default
                    raise NotImplementedError

                elif error == "normal":
                    for level in levels:
                        out[good, outindex] = level2sigmas(level) * numpy.sqrt(p*(1.0 - p) / denom)
                        outindex += 1

                elif error == "wilson":
                    for level in levels:
                        z = level2sigmas(level)
                        out[good, outindex] = (p + 0.5*z**2/denom + z*numpy.sqrt(p*(1.0 - p)/denom + 0.25*z**2/numpy.square(denom))) / (1.0 + z**2/denom)
                        outindex += 1

                elif error == "agresti-coull":
                    raise NotImplementedError

                elif error == "feldman-cousins":
                    raise NotImplementedError

                elif error == "jeffrey":
                    raise NotImplementedError

                elif error == "bayesian-uniform":
                    raise NotImplementedError

            if recarray:
                return out.view([(x, numpy.dtype(numpy.float64)) for x in columns]).reshape(denomhist._shape[:-1])
            else:
                return out.reshape(denomhist._shape[:-1] + (outindex,))

        def handle(denomcontent, cutcontent):
            if isinstance(denomcontent, dict):
                return dict((n, handle(x, [cc[n] for cc in cutcontent])) for n, x in denomcontent.items())
            else:
                return handlearray(denomcontent, cutcontent)

        out = handle(denomhist._content, [x._content for x in cuthist])

        if showcolumns:
            out = out, columns

        if return_denomhist:
            return out, denomhist
        else:
            return out
