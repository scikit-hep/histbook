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

import numbers

import numpy

import histbook.axis
import histbook.expr

class AxisTuple(tuple):
    def __getitem__(self, item):
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
            if isinstance(axis, cls) and all(hasattr(axis, n) and getattr(axis, n) == x for n, x in kwargs.items()):
                return axis
        raise IndexError("no such axis: {0}({1}{2})".format(cls.__name__, repr(str(expr)), "".join(", {0}={1}".format(n, kwargs[n]) for n in sorted(kwargs))))

    def groupby(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.groupby, kwargs)

    def groupbin(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.groupbin, kwargs)

    def bin(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.bin, kwargs)

    def intbin(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.intbin, kwargs)

    def split(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.split, kwargs)

    def cut(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.cut, kwargs)

    def profile(self, expr, **kwargs):
        return self._findbyclass(expr, histbook.axis.profile, kwargs)

class Projectable(object):
    @property
    def axis(self):
        out = AxisTuple(self._group + self._fixed + self._profile)
        out._defs = self._defs
        return out

    def rebin(self, axis, to):
        raise NotImplementedError

    def project(self, *axis):
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

        outaxis = [x.relabel(x._original) for x in allaxis if x in axis] + [x.relabel(x._original) for x in self._profile]
        out = self.__class__(*outaxis, weight=self._weight, defs=self._defs)
        if self._content is not None:
            out._content = projcontent(0, self._content)
        return out

    def select(self, expr, tolerance=1e-12):
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

        def normalizeexpr(expr):
            if isinstance(expr, histbook.expr.Relation):
                cutcmp = expr.cmp
                if isinstance(expr.left, histbook.expr.Const):
                    cutvalue, cutexpr = expr.left, expr.right
                    cutcmp = {"<": ">", "<=": ">="}.get(cutcmp, cutcmp)
                else:
                    cutexpr, cutvalue = expr.left, expr.right

                if not isinstance(cutvalue, histbook.expr.Const):
                    raise TypeError("select expression must have a constant left or right hand side, not {0}".format(repr(str(expr))))
                if isinstance(cutexpr, histbook.expr.Const):
                    raise TypeError("select expression must have a variable left or right hand side, not {0}".format(repr(str(expr))))

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
                if isinstance(newaxis, histbook.axis._nullaxis):
                    out.shape = tuple(sh for sh, sl in zip(out.shape, slc) if sl is not cutslice)
                return out

        axis = [newaxis if x is cutaxis else x.relabel(x._original) for x in self._group + self._fixed + self._profile]
        axis = [x for x in axis if not isinstance(x, histbook.axis._nullaxis)]
        out = self.__class__(*axis, weight=self._weight, defs=self._defs)
        if self._content is not None:
            out._content = cutcontent(0, self._content)
        return out

    def table(self, *profile, **opts):
        count = opts.pop("count", True)
        effcount = opts.pop("effcount", False)
        error = opts.pop("error", True)
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

        def handlearray(content):
            content = content.reshape((-1, self._shape[-1]))

            out = numpy.zeros((content.shape[0], len(columns)), dtype=content.dtype)
            outindex = 0

            sumw = content[:, self._sumwindex]
            if count:
                out[:, outindex] = sumw
                outindex += 1
                if error:
                    if self._weightparsed is None:
                        out[:, outindex] = numpy.sqrt(sumw)
                    else:
                        out[:, outindex] = numpy.sqrt(content[:, self._sumw2index])
                    outindex += 1

            if len(profile) > 0 or effcount:
                good = numpy.nonzero(sumw)
                sumw = sumw[good]
                if self._weightparsed is None:
                    effcnt = sumw
                else:
                    effcnt = numpy.square(sumw) / content[:, self._sumw2index]

            if effcount:
                out[good, outindex] = effcnt
                outindex += 1

            for prof in profile:
                out[good, outindex] = content[good, prof._sumwxindex] / sumw
                outindex += 1
                if error:
                    out[good, outindex] = numpy.sqrt(((content[good, prof._sumwx2index] / sumw) - numpy.square(out[good, outindex - 1])) / effcnt)
                    outindex += 1

            return out.view([(x, content.dtype) for x in columns]).reshape(self._shape[:-1])

        def handle(content):
            if isinstance(content, dict):
                return dict((n, handle(x)) for n, x in content.items())
            else:
                return handlearray(content)

        return handle(self._content)
