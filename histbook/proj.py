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

class Projectable(object):
    @property
    def axis(self):
        out = AxisTuple(self._group + self._fixed + self._profile)
        out._defs = self._defs
        return out

    def rebin(self, axis, to):
        raise NotImplementedError

    def project(self, *axis):
        allaxis = self._group + self._fixed + self._profile

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

        outaxis = [x.relabel(x._original) for x in allaxis if x in axis]
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
                return content[tuple(cutslice if j < len(allaxis) and allaxis[j] is cutaxis else slice(None) for j in range(i, len(allaxis) + 1))].copy()

        axis = [newaxis if x is cutaxis else x.relabel(x._original) for x in self._group + self._fixed + self._profile]
        axis = [x for x in axis if not isinstance(x, histbook.axis._nullaxis)]
        out = self.__class__(*axis, weight=self._weight, defs=self._defs)
        if self._content is not None:
            out._content = cutcontent(0, self._content)
        return out
