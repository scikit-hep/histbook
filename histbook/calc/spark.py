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
    
def fillspark(hist, df):
    pass
    



# df = spark.read.csv("businesses_plus.csv", header=True)
# from histbook import *
# hist = Hist(bin("latitude", 3, 37.7, 37.8), bin("longitude", 3, -122.5, -121.7))

# import pyspark.sql.functions
# indexes = []
# for axis in hist._group + hist._fixed:
#     exprcol = tocolumns(df, histbook.instr.totree(axis._parsed))
#     if isinstance(axis, histbook.axis.groupby):
#         raise NotImplementedError
#     elif isinstance(axis, histbook.axis.groupbin):
#         raise NotImplementedError
#     elif isinstance(axis, histbook.axis.bin):
#         scaled = (exprcol - axis.low) * (axis.numbins / (axis.high - axis.low))
#         if bin.closedlow:
#             discretized = pyspark.sql.functions.floor(scaled) + 1
#         else:
#             discretized = pyspark.sql.functions.ceil(scaled)
#         indexes.append(pyspark.sql.functions.greatest(pyspark.sql.functions.lit(0), pyspark.sql.functions.least(pyspark.sql.functions.lit(axis.numbins + 1), discretized)))
#     elif isinstance(axis, histbook.axis.intbin):
#         raise NotImplementedError
#     elif isinstance(axis, histbook.axis.split):
#         raise NotImplementedError
#     elif isinstance(axis, histbook.axis.cut):
#         raise NotImplementedError
#     elif isinstance(axis, histbook.axis.profile):
#         raise NotImplementedError
#     else:
#         raise AssertionError(axis)

# aggs = []
# for axis in hist._profile:
#     raise NotImplementedError   # add aggregations

# index = pyspark.sql.functions.struct(*indexes).alias("@index")

# if hist._weight is None:
#     df2 = df.select(index)
#     aggs.append(pyspark.sql.functions.count(df2[df2.columns[0]]))
# else:
#     exprcol = tocolumns(df, histbook.instr.totree(hist._weightparsed))
#     df2 = df.select(index, exprcol, exprcol*exprcol)
#     aggs.append(pyspark.sql.functions.sum(df2[df2.columns[1]]))
#     aggs.append(pyspark.sql.functions.sum(df2[df2.columns[2]]))

# # df2.groupBy(df2[df2.columns[0]]).agg(*aggs).show()

# out = df2.groupBy(df2[df2.columns[0]]).agg(*aggs).collect()

# def recurse(index, columns, axis, content):
#     if len(axis) == 0:
#         content += columns
#     elif isinstance(axis[0], histbook.axis.groupby):
#         raise NotImplementedError
#     elif isinstance(axis[0], histbook.axis.groupbin):
#         raise NotImplementedError
#     elif isinstance(axis[0], histbook.axis.bin):
#         i = index[0] - (1 if not axis[0].underflow else 0)
#         if i < axis[0].totbins:
#             recurse(index[1:], columns, axis[1:], content[i])
#     elif isinstance(axis[0], histbook.axis.intbin):
#         raise NotImplementedError
#     elif isinstance(axis[0], histbook.axis.split):
#         raise NotImplementedError
#     elif isinstance(axis[0], histbook.axis.cut):
#         raise NotImplementedError
#     else:
#         raise AssertionError(axis[0])

# for row in out:
#     hist._prefill()
#     recurse(row[0], row[1:], hist._group + hist._fixed, hist._content)

