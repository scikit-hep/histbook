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

import numpy

import histbook.axis
import histbook.instr
import histbook.expr
import histbook.hist

def isspark(arrays, more):
    out = arrays.__class__.__name__ == "DataFrame" and arrays.__class__.__module__ == "pyspark.sql.dataframe"
    if out and len(more) > 0:
        raise TypeError("if arrays is a PySpark DataFrame, keyword arguments are not allowed")
    return out

def tocolumns(df, expr):
    import pyspark.sql.functions as fcns

    if isinstance(expr, histbook.expr.Const):
        return fcns.lit(expr.value)

    elif isinstance(expr, (histbook.expr.Name, histbook.expr.Predicate)):
        return df[expr.value]

    elif isinstance(expr, histbook.expr.Call):
        if expr.fcn == "abs" or expr.fcn == "fabs":
            return fcns.abs(tocolumns(df, expr.args[0]))
        elif expr.fcn == "max" or expr.fcn == "fmax":
            return fcns.greatest(*[tocolumns(df, x) for x in expr.args])
        elif expr.fcn == "min" or expr.fcn == "fmin":
            return fcns.least(*[tocolumns(df, x) for x in expr.args])
        elif expr.fcn == "arccos":
            return fcns.acos(tocolumns(df, expr.args[0]))
        elif expr.fcn == "arccosh":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "arcsin":
            return fcns.asin(tocolumns(df, expr.args[0]))
        elif expr.fcn == "arcsinh":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "arctan2":
            return fcns.atan2(tocolumns(df, expr.args[0]), tocolumns(df, expr.args[1]))
        elif expr.fcn == "arctan":
            return fcns.atan(tocolumns(df, expr.args[0]))
        elif expr.fcn == "arctanh":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "ceil":
            return fcns.ceil(tocolumns(df, expr.args[0]))
        elif expr.fcn == "copysign":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "cos":
            return fcns.cos(tocolumns(df, expr.args[0]))
        elif expr.fcn == "cosh":
            return fcns.cosh(tocolumns(df, expr.args[0]))
        elif expr.fcn == "rad2deg":
            return tocolumns(df, expr.args[0]) * (180.0 / math.pi)
        elif expr.fcn == "erfc":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "erf":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "exp":
            return fcns.exp(tocolumns(df, expr.args[0]))
        elif expr.fcn == "expm1":
            return fcns.expm1(tocolumns(df, expr.args[0]))
        elif expr.fcn == "factorial":
            return fcns.factorial(tocolumns(df, expr.args[0]))
        elif expr.fcn == "floor":
            return fcns.floor(tocolumns(df, expr.args[0]))
        elif expr.fcn == "fmod":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "gamma":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "hypot":
            return fcns.hypot(tocolumns(df, expr.args[0]), tocolumns(df, expr.args[1]))
        elif expr.fcn == "isinf":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "isnan":
            return fcns.isnan(tocolumns(df, expr.args[0]))
        elif expr.fcn == "lgamma":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "log10":
            return fcns.log10(tocolumns(df, expr.args[0]))
        elif expr.fcn == "log1p":
            return fcns.log1p(tocolumns(df, expr.args[0]))
        elif expr.fcn == "log":
            return fcns.log(tocolumns(df, expr.args[0]))
        elif expr.fcn == "pow":
            return fcns.pow(tocolumns(df, expr.args[0]), tocolumns(df, expr.args[1]))
        elif expr.fcn == "deg2rad":
            return tocolumns(df, expr.args[0]) * (math.pi / 180.0)
        elif expr.fcn == "sinh":
            return fcns.sinh(tocolumns(df, expr.args[0]))
        elif expr.fcn == "sin":
            return fcns.sin(tocolumns(df, expr.args[0]))
        elif expr.fcn == "sqrt":
            return fcns.sqrt(tocolumns(df, expr.args[0]))
        elif expr.fcn == "tanh":
            return fcns.tanh(tocolumns(df, expr.args[0]))
        elif expr.fcn == "tan":
            return fcns.tan(tocolumns(df, expr.args[0]))
        elif expr.fcn == "trunc":
            raise NotImplementedError(expr.fcn)  # FIXME (fcns.trunc is for dates)
        elif expr.fcn == "xor":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "conjugate":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "exp2":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "heaviside":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "isfinite":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "left_shift" and isinstance(expr.args[1], histbook.expr.Const):
            return fcns.shiftLeft(tocolumns(df, expr.args[0]), expr.args[1].value)
        elif expr.fcn == "log2":
            return fcns.log2(tocolumns(df, expr.args[0]))
        elif expr.fcn == "logaddexp2":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "logaddexp":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "mod" or expr.fcn == "fmod":
            return tocolumns(df, expr.args[0]) % tocolumns(df, expr.args[1])
        elif expr.fcn == "right_shift" and isinstance(expr.args[1], histbook.expr.Const):
            return fcns.shiftRight(tocolumns(df, expr.args[0]), expr.args[1].value)
        elif expr.fcn == "rint":
            return fcns.rint(tocolumns(df, expr.args[0]))
        elif expr.fcn == "sign":
            raise NotImplementedError(expr.fcn)  # FIXME
        elif expr.fcn == "where":
            return fcns.when(tocolumns(df, expr.args[0]), tocolumns(df, expr.args[1])).otherwise(tocolumns(df, expr.args[2]))
        elif expr.fcn == "numpy.equal":
            return tocolumns(df, expr.args[0]) == tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.not_equal":
            return tocolumns(df, expr.args[0]) != tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.less":
            return tocolumns(df, expr.args[0]) < tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.less_equal":
            return tocolumns(df, expr.args[0]) <= tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.isin":
            return tocolumns(df, expr.args[0]) in tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.logical_not":
            return ~tocolumns(df, expr.args[0])
        elif expr.fcn == "numpy.add":
            return tocolumns(df, expr.args[0]) + tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.subtract":
            return tocolumns(df, expr.args[0]) - tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.multiply":
            return tocolumns(df, expr.args[0]) * tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.true_divide":
            return tocolumns(df, expr.args[0]) / tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.logical_or":
            return tocolumns(df, expr.args[0]) | tocolumns(df, expr.args[1])
        elif expr.fcn == "numpy.logical_and":
            return tocolumns(df, expr.args[0]) & tocolumns(df, expr.args[1])
        else:
            raise NotImplementedError(expr.fcn)

    else:
        raise AssertionError(expr)

def fillspark(hist, df):
    import pyspark.sql.functions as fcns

    indexes = []
    for axis in hist._group + hist._fixed:
        exprcol = tocolumns(df, histbook.instr.totree(axis._parsed))

        if isinstance(axis, histbook.axis.groupby):
            indexes.append(exprcol)

        elif isinstance(axis, histbook.axis.groupbin):
            scaled = (exprcol - float(axis.origin)) * (1.0/float(axis.binwidth))
            if axis.closedlow:
                discretized = fcns.floor(scaled)
            else:
                discretized = fcns.ceil(scaled) - 1
            indexes.append(fcns.nanvl(discretized * float(axis.binwidth) + float(axis.origin), fcns.lit("NaN")))

        elif isinstance(axis, histbook.axis.bin):
            scaled = (exprcol - float(axis.low)) * (int(axis.numbins) / (float(axis.high) - float(axis.low)))
            if axis.closedlow:
                discretized = fcns.floor(scaled) + 1
            else:
                discretized = fcns.ceil(scaled)
            indexes.append(fcns.when(fcns.isnull(exprcol) | fcns.isnan(exprcol), int(axis.numbins) + 2).otherwise(fcns.greatest(fcns.lit(0), fcns.least(fcns.lit(int(axis.numbins) + 1), discretized))))

        elif isinstance(axis, histbook.axis.intbin):
            indexes.append(fcns.greatest(fcns.lit(0), fcns.least(fcns.lit(int(axis.max) - int(axis.min) + 1), fcns.round(exprcol - int(axis.min) + 1))))

        elif isinstance(axis, histbook.axis.split):
            def build(x, i):
                if i < len(axis.edges):
                    if axis.closedlow:
                        return build(x.when(exprcol < float(axis.edges[i]), i), i + 1)
                    else:
                        return build(x.when(exprcol <= float(axis.edges[i]), i), i + 1)
                else:
                    return x.otherwise(i)
            indexes.append(build(fcns.when(fcns.isnull(exprcol) | fcns.isnan(exprcol), len(axis.edges) + 1), 0))

        elif isinstance(axis, histbook.axis.cut):
            indexes.append(fcns.when(exprcol, 0).otherwise(1))

        else:
            raise AssertionError(axis)

    aliasnum = [-1]
    def alias(x):
        aliasnum[0] += 1
        return x.alias("@" + str(aliasnum[0]))

    index = alias(fcns.struct(*indexes))

    selectcols = [index]
    if hist._weightoriginal is not None:
        weightcol = tocolumns(df, histbook.instr.totree(hist._weightparsed))
    for axis in hist._profile:
        exprcol = tocolumns(df, histbook.instr.totree(axis._parsed))
        if hist._weightoriginal is None:
            selectcols.append(alias(exprcol))
            selectcols.append(alias(exprcol*exprcol))
        else:
            selectcols.append(alias(exprcol*weightcol))
            selectcols.append(alias(exprcol*exprcol*weightcol))

    if hist._weightoriginal is None:
        df2 = df.select(*selectcols)
    else:
        selectcols.append(alias(weightcol))
        selectcols.append(alias(weightcol*weightcol))
        df2 = df.select(*selectcols)

    aggs = [fcns.sum(df2[n]) for n in df2.columns[1:]]
    if hist._weightoriginal is None:
        aggs.append(fcns.count(df2[df2.columns[0]]))

    def getornew(content, key, nextaxis):
        if key in content:
            return content[key]
        elif isinstance(nextaxis, histbook.axis.GroupAxis):
            return {}
        else:
            return numpy.zeros(hist._shape, dtype=histbook.hist.COUNTTYPE)

    def recurse(index, columns, axis, content):
        if len(axis) == 0:
            content += columns

        elif isinstance(axis[0], (histbook.axis.groupby, histbook.axis.groupbin)):
            content[index[0]] = recurse(index[1:], columns, axis[1:], getornew(content, index[0], axis[1] if len(axis) > 1 else None))
            if isinstance(axis[0], histbook.axis.groupbin) and None in content:
                content["NaN"] = content[None]
                del content[None]

        elif isinstance(axis[0], (histbook.axis.bin, histbook.axis.intbin, histbook.axis.split)):
            i = index[0] - (1 if not axis[0].underflow else 0)
            if int(i) < axis[0].totbins:
                recurse(index[1:], columns, axis[1:], content[int(i)])

        elif isinstance(axis[0], histbook.axis.cut):
            recurse(index[1:], columns, axis[1:], content[0 if index[0] else 1])

        else:
            raise AssertionError(axis[0])

        return content

    query = df2.groupBy(df2[df2.columns[0]]).agg(*aggs)

    def wait():
        for row in query.collect():
            recurse(row[0], row[1:], hist._group + hist._fixed, hist._content)

    return wait
