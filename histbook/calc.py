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

import histbook.expr
import histbook.stmt

import numpy
INDEXTYPE = numpy.int32

library = {}

def histbook_bin(underflow, overflow, nanflow, closedlow):
    # don't actually specialize the code; placeholder for backends unfriendly to branching (e.g. GPU)

    shift = 0
    if underflow:
        underindex = 0
        shift += 1
    else:
        underindex = numpy.ma.masked

    if overflow:
        overindex = shift
        shift += 1
    else:
        overindex = numpy.ma.masked

    if nanflow:
        nanindex = shift
    else:
        nanindex = numpy.ma.masked

    if underflow:
        shift = 1
    else:
        shift = 0

    def bin(values, numbins, low, high):
        indexes = values - float(low)
        numpy.multiply(indexes, numbins / (high - low), indexes)

        if closedlow:
            indexes = numpy.floor(indexes)
            if shift != 0:
                numpy.add(indexes, shift, indexes)
        else:
            indexes = numpy.ceil(indexes)
            numpy.add(indexes, shift - 1, indexes)

        out = numpy.ma.array(indexes, dtype=INDEXTYPE)
        with numpy.errstate(invalid="ignore"):
            out[indexes < 0] = underindex
            out[indexes >= (numbins + shift)] = overindex + numbins
            out[numpy.isnan(indexes)] = nanindex + numbins
        return out

    return bin

library["histbook.binUONL"] = histbook_bin(True, True, True, True)
library["histbook.binUONH"] = histbook_bin(True, True, True, False)
library["histbook.binUO_L"] = histbook_bin(True, True, False, True)
library["histbook.binUO_H"] = histbook_bin(True, True, False, False)
library["histbook.binU_NL"] = histbook_bin(True, False, True, True)
library["histbook.binU_NH"] = histbook_bin(True, False, True, False)
library["histbook.binU__L"] = histbook_bin(True, False, False, True)
library["histbook.binU__H"] = histbook_bin(True, False, False, False)
library["histbook.bin_ONL"] = histbook_bin(False, True, True, True)
library["histbook.bin_ONH"] = histbook_bin(False, True, True, False)
library["histbook.bin_O_L"] = histbook_bin(False, True, False, True)
library["histbook.bin_O_H"] = histbook_bin(False, True, False, False)
library["histbook.bin__NL"] = histbook_bin(False, False, True, True)
library["histbook.bin__NH"] = histbook_bin(False, False, True, False)
library["histbook.bin___L"] = histbook_bin(False, False, False, True)
library["histbook.bin___H"] = histbook_bin(False, False, False, False)

def calculate(expr, symbols):
    print repr(expr)

    if isinstance(expr, (histbook.expr.Name, histbook.expr.Predicate)):
        return symbols[expr.value]

    elif isinstance(expr, histbook.expr.Const):
        return expr.value

    elif isinstance(expr, histbook.expr.Call) and expr.fcn in library:
        return library[expr.fcn](*(calculate(arg, symbols) for arg in expr.args))
            
    else:
        raise NotImplementedError(expr)
