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

import histbook.axis

class Exportable(object):
    def pandas(self, *profile, **opts):
        import pandas as pd

        content = self.table(*profile, **opts)
        allaxis = self._group + self._fixed

        names = [None for x in allaxis]
        arrays = []
        keys = [[] for x in allaxis]

        def index(j, content, key):
            if j < len(allaxis):
                axis = allaxis[j]
                names[j] = str(axis.expr)

                if isinstance(axis, histbook.axis.groupby):
                    for n in sorted(content):
                        index(j + 1, content[n], key + (n,))

                elif isinstance(axis, histbook.axis.groupbin):
                    closed = "left" if axis.closedlow else "right"
                    for n in sorted(content):
                        index(j + 1, content[n], key + (pd.Interval(n, n + float(axis.binwidth), closed=closed),))

                else:
                    if content is not None:
                        arrays.append(content)

                    if isinstance(axis, histbook.axis.bin):
                        closed = "left" if axis.closedlow else "right"
                        if axis.underflow:
                            index(j + 1, None, key + (pd.Interval(float("-inf"), axis.low, closed=closed),))
                        last = axis.low
                        for i in range(axis.numbins):
                            this = (float(i + 1) / float(axis.numbins)) * float(axis.high - axis.low) + float(axis.low)
                            index(j + 1, None, key + (pd.Interval(last, this, closed=closed),))
                            last = this
                        if axis.overflow:
                            index(j + 1, None, key + (pd.Interval(axis.high, float("inf"), closed=closed),))
                        if axis.nanflow:
                            index(j + 1, None, key + ("NaN",))

                    elif isinstance(axis, histbook.axis.intbin):
                        if axis.underflow:
                            index(j + 1, None, key + (pd.Interval(float("-inf"), int(axis.min), closed="left"),))
                        for i in range(int(axis.min), int(axis.max) + 1):
                            index(j + 1, None, key + (str(i),))
                        if axis.overflow:
                            index(j + 1, None, key + (pd.Interval(int(axis.max), float("inf"), closed="right"),))

                    elif isinstance(axis, histbook.axis.split):
                        raise NotImplementedError

                    elif isinstance(axis, histbook.axis.cut):
                        raise NotImplementedError

                    else:
                        raise AssertionError(axis)

            else:
                for j, k in enumerate(key):
                    keys[j].append(k)

        index(0, content, ())

        arrays = numpy.concatenate(arrays)
        return pd.DataFrame(index=pd.MultiIndex.from_arrays(keys, names=names),
                            columns=arrays.dtype.names,
                            data=arrays.view(arrays.dtype[arrays.dtype.names[0]]).reshape(len(keys[0]), -1))
