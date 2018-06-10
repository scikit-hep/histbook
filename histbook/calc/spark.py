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
    if isinstance(expr, histbook.expr.Const):
        import pyspark.sql.functions
        return pyspark.sql.functions.lit(expr.value)
    elif isinstance(expr, (histbook.expr.Name, histbook.expr.Predicate)):
        return df[expr.value]
    elif isinstance(expr, histbook.expr.Call):
        raise NotImplementedError
    else:
        raise AssertionError(expr)

df = spark.read.csv("businesses_plus.csv", header=True)
from histbook import *

def fillspark(hist, df):
    import pyspark.sql.functions as fcns
    indexes = []
    for axis in hist._group + hist._fixed:
        exprcol = tocolumns(df, histbook.instr.totree(axis._parsed))
        if isinstance(axis, histbook.axis.groupby):
            indexes.append(exprcol)
        elif isinstance(axis, histbook.axis.groupbin):
            scaled = (exprcol - float(axis.origin)) * (1.0/float(axis.binwidth))
            if bin.closedlow:
                discretized = fcns.floor(scaled) + 1
            else:
                discretized = fcns.ceil(scaled)
            indexes.append(fcns.nanvl(discretized * float(axis.binwidth) + float(axis.origin), fcns.lit("NaN")))
        elif isinstance(axis, histbook.axis.bin):
            scaled = (exprcol - float(axis.low)) * (int(axis.numbins) / (float(axis.high) - float(axis.low)))
            if bin.closedlow:
                discretized = fcns.floor(scaled) + 1
            else:
                discretized = fcns.ceil(scaled)
            indexes.append(fcns.when(fcns.isnan(exprcol), int(axis.numbins) + 2).otherwise(fcns.greatest(fcns.lit(0), fcns.least(fcns.lit(int(axis.numbins) + 1), discretized))))
        elif isinstance(axis, histbook.axis.intbin):
            indexes.append(fcns.greatest(fcns.lit(0), fcns.least(fcns.lit(int(axis.max) - int(axis.min) + 1), fcns.round(exprcol - int(axis.min) + 1))))
        elif isinstance(axis, histbook.axis.split):
            if axis.closedlow:
                def build(x, i):
                    if i == 0:
                        return build(fcns.when(exprcol < float(axis.edges[0])), i + 1)
                    elif i < len(axis.edges):
                        return build(x.when(exprcol < float(axis.edges[i])), i + 1)
                    else:
                        return x.otherwise(i)
            else:
                def build(x, i):
                    if i < len(axis.edges):
                        return build(x.when(exprcol <= float(axis.edges[i])), i + 1)
                    else:
                        return x.otherwise(i)
            indexes.append(build(fcns.when(fcns.isnan(exprcol), len(axis.edges) + 1), 0))
        elif isinstance(axis, histbook.axis.cut):
            indexes.append(fcns.when(exprcol, 0, 1))
        else:
            raise AssertionError(axis)
    aggs = []
    for axis in hist._profile:
        raise NotImplementedError   # add aggregations
    index = fcns.struct(*indexes).alias("@index")
    if hist._weight is None:
        df2 = df.select(index)
        aggs.append(fcns.count(df2[df2.columns[0]]))
    else:
        exprcol = tocolumns(df, histbook.instr.totree(hist._weightparsed))
        df2 = df.select(index, exprcol, exprcol*exprcol)
        aggs.append(fcns.sum(df2[df2.columns[1]]))
        aggs.append(fcns.sum(df2[df2.columns[2]]))
    # df2.groupBy(df2[df2.columns[0]]).agg(*aggs).show()
    out = df2.groupBy(df2[df2.columns[0]]).agg(*aggs).collect()
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
            recurse(index[1:], columns, axis[1:], getornew(content, index[0], axis[1] if len(axis) > 1 else None))
        elif isinstance(axis[0], (histbook.axis.bin, histbook.axis.intbin, histbook.axis.split)):
            i = index[0] - (1 if not axis[0].underflow else 0)
            if i < axis[0].totbins:
                recurse(index[1:], columns, axis[1:], content[i])
        elif isinstance(axis[0], histbook.axis.cut):
            recurse(index[1:], columns, axis[1:], content[0 if index[0] else 1])
        else:
            raise AssertionError(axis[0])
    for row in out:
        hist._prefill()
        recurse(row[0], row[1:], hist._group + hist._fixed, hist._content)

hist = Hist(bin("latitude", 3, 37.7, 37.8), bin("longitude", 3, -122.5, -121.7))
fillspark(hist, df)
