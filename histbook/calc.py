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

import histbook.expr

import numpy
INDEXTYPE = numpy.int32

library = {}

library["numpy.add"] = numpy.add
library["numpy.subtract"] = numpy.subtract
library["numpy.multiply"] = numpy.multiply
library["numpy.true_divide"] = numpy.true_divide
library["numpy.equal"] = numpy.equal
library["numpy.not_equal"] = numpy.not_equal
library["numpy.less"] = numpy.less
library["numpy.less_equal"] = numpy.less_equal
try:
    library["numpy.isin"] = numpy.isin
except AttributeError:
    library["numpy.isin"] = numpy.in1d
library["numpy.logical_or"] = numpy.logical_or
library["numpy.logical_and"] = numpy.logical_and
library["numpy.logical_not"] = numpy.logical_not

library["abs"] = numpy.absolute
library["acos"] = numpy.arccos
library["acosh"] = numpy.arccosh
library["asin"] = numpy.arcsin
library["asinh"] = numpy.arcsinh
library["atan2"] = numpy.arctan2
library["atan"] = numpy.arctan
library["atanh"] = numpy.arctanh
library["xor"] = numpy.bitwise_xor
library["ceil"] = numpy.ceil
library["conjugate"] = numpy.conjugate
library["copysign"] = numpy.copysign
library["cos"] = numpy.cos
library["cosh"] = numpy.cosh
library["deg2rad"] = numpy.deg2rad
library["exp2"] = numpy.exp2
library["exp"] = numpy.exp
library["expm1"] = numpy.expm1
library["floor"] = numpy.floor
library["fmod"] = numpy.fmod
try:
    library["heaviside"] = lambda x, middle=0.5: numpy.heaviside(x, middle)
except AttributeError:
    def heaviside(x, middle=0.5):
        out = numpy.where(x < 0, 0.0, 1.0)
        out[x == 0] = middle
        return out
    library["heaviside"] = heaviside
library["hypot"] = numpy.hypot
library["isfinite"] = numpy.isfinite
library["isinf"] = numpy.isinf
library["isnan"] = numpy.isnan
library["left_shift"] = numpy.left_shift
library["log10"] = numpy.log10
library["log1p"] = numpy.log1p
library["log2"] = numpy.log2
library["logaddexp2"] = numpy.logaddexp2
library["logaddexp"] = numpy.logaddexp
library["log"] = numpy.log
library["max"] = numpy.maximum
library["min"] = numpy.minimum
library["pow"] = numpy.power
library["rad2deg"] = numpy.rad2deg
library["mod"] = numpy.remainder
library["right_shift"] = numpy.right_shift
library["rint"] = numpy.rint
library["sign"] = numpy.sign
library["sinh"] = numpy.sinh
library["sin"] = numpy.sin
library["sqrt"] = numpy.sqrt
library["tanh"] = numpy.tanh
library["tan"] = numpy.tan
library["trunc"] = numpy.trunc

def vectorized_erf(complement):
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911
    def erf(values):
        sign = numpy.where(values < 0, -1.0, 1.0)
        values = numpy.absolute(values)
        t = 1.0 / (values * p + 1)
        y = 1.0 - ((((a5*t + a4)*t + a3)*t + a2)*t + a1)*t * numpy.exp(numpy.negative(numpy.square(values)))
        if complement:
            return 1.0 - sign * y
        else:
            return sign * y
    return erf

library["erf"] = vectorized_erf(False)
library["erfc"] = vectorized_erf(True)

def vectorized_gamma(logarithm):
    cofs = (76.18009173, -86.50532033, 24.01409822, -1.231739516e0, 0.120858003e-2, -0.536382e-5)
    stp = 2.50662827465
    def lgamma(values):
        x = values - 1.0
        tmp = x + 5.5
        tmp = (x + 0.5)*numpy.log(tmp) - tmp
        ser = numpy.ones(len(values), dtype=numpy.dtype(numpy.float64))
        for cof in cofs:
            numpy.add(x, 1.0, x)
            numpy.add(ser, cof/x, ser)
        return tmp + numpy.log(stp*ser)
    if logarithm:
        return lgamma
    else:
        return lambda values: numpy.exp(lgamma(values))

library["gamma"] = vectorized_gamma(False)
lgamma = library["lgamma"] = vectorized_gamma(True)
library["factorial"] = lambda values: numpy.round(numpy.exp(lgamma(numpy.round(values) + 1)))

def histbook_groupby(values):
    uniques, inverse = numpy.unique(values, return_inverse=True)
    inverse = inverse.astype(INDEXTYPE)
    return uniques, inverse

library["histbook.groupby"] = histbook_groupby

def histbook_groupbin(closedlow):
    def groupbin(values, binwidth, origin):
        if origin == 0:
            indexes = numpy.multiply(values, 1.0/float(binwidth))
        else:
            indexes = values - float(origin)
            numpy.multiply(indexes, 1.0/float(binwidth), indexes)

        if closedlow:
            numpy.floor(indexes, indexes)
        else:
            numpy.ceil(indexes, indexes)
            numpy.subtract(indexes, 1, indexes)

        numpy.multiply(indexes, float(binwidth), indexes)
        if origin != 0:
            numpy.add(indexes, float(origin), indexes)

        ok = numpy.isnan(indexes)
        numpy.logical_not(ok, ok)

        if ok.all():
            uniques, inverse = numpy.unique(indexes, return_inverse=True)
            inverse = inverse.astype(INDEXTYPE)
        else:
            uniques, okinverse = numpy.unique(indexes[ok], return_inverse=True)
            inverse = numpy.ones(indexes.shape, dtype=INDEXTYPE)
            numpy.multiply(inverse, -1, inverse)
            inverse[ok] = okinverse
        return uniques, inverse

    return groupbin

library["histbook.groupbinL"] = histbook_groupbin(True)
library["histbook.groupbinH"] = histbook_groupbin(False)
    
def histbook_bin(underflow, overflow, nanflow, closedlow):
    if nanflow:
        nanindex = (1 if underflow else 0) + (1 if overflow else 0)
    else:
        nanindex = numpy.ma.masked

    if underflow:
        shift = 1
    else:
        shift = 0

    def bin(values, numbins, low, high):
        indexes = values - float(low)
        numpy.multiply(indexes, float(numbins) / float(high - low), indexes)

        if closedlow:
            numpy.floor(indexes, indexes)
            if shift != 0:
                numpy.add(indexes, shift, indexes)
        else:
            numpy.ceil(indexes, indexes)
            numpy.add(indexes, shift - 1, indexes)

        out = numpy.ma.array(indexes, dtype=INDEXTYPE)
        with numpy.errstate(invalid="ignore"):
            if underflow:
                numpy.maximum(out, 0, out)
            else:
                out[out < 0] = numpy.ma.masked
            if overflow:
                numpy.minimum(out, shift + numbins, out)
            else:
                out[out >= (numbins + shift)] = numpy.ma.masked
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

def histbook_intbin(underflow, overflow):
    if underflow:
        shift = 1
    else:
        shift = 0

    def intbin(values, min, max):
        indexes = numpy.ma.array((values + (shift - min)), dtype=INDEXTYPE)

        if underflow:
            numpy.maximum(indexes, 0, indexes)
        else:
            indexes[indexes < 0] = numpy.ma.masked

        if overflow:
            numpy.minimum(indexes, (shift + 1 + max - min), indexes)
        else:
            indexes[indexes > (shift + max - min)] = numpy.ma.masked

        return indexes

    return intbin

library["histbook.intbinUO"] = histbook_intbin(True, True)
library["histbook.intbinU_"] = histbook_intbin(True, False)
library["histbook.intbin_O"] = histbook_intbin(False, True)
library["histbook.intbin__"] = histbook_intbin(False, False)

def histbook_split(underflow, overflow, nanflow, closedlow):
    def split(values, edges):
        indexes = numpy.ma.array(numpy.digitize(values, edges), dtype=INDEXTYPE)
        if not closedlow:
            indexes[library["numpy.isin"](values, edges)] -= 1

        if not overflow:
            indexes[indexes == len(edges)] = numpy.ma.masked

        if nanflow:
            indexes[numpy.isnan(values)] = len(edges) + (1 if overflow else 0)
        else:
            indexes[numpy.isnan(values)] = numpy.ma.masked

        if not underflow:
            indexes[indexes == 0] = numpy.ma.masked
            numpy.subtract(indexes, 1, indexes)

        return indexes

    return split

library["histbook.splitUONL"] = histbook_split(True, True, True, True)
library["histbook.splitUONH"] = histbook_split(True, True, True, False)
library["histbook.splitUO_L"] = histbook_split(True, True, False, True)
library["histbook.splitUO_H"] = histbook_split(True, True, False, False)
library["histbook.splitU_NL"] = histbook_split(True, False, True, True)
library["histbook.splitU_NH"] = histbook_split(True, False, True, False)
library["histbook.splitU__L"] = histbook_split(True, False, False, True)
library["histbook.splitU__H"] = histbook_split(True, False, False, False)
library["histbook.split_ONL"] = histbook_split(False, True, True, True)
library["histbook.split_ONH"] = histbook_split(False, True, True, False)
library["histbook.split_O_L"] = histbook_split(False, True, False, True)
library["histbook.split_O_H"] = histbook_split(False, True, False, False)
library["histbook.split__NL"] = histbook_split(False, False, True, True)
library["histbook.split__NH"] = histbook_split(False, False, True, False)
library["histbook.split___L"] = histbook_split(False, False, False, True)
library["histbook.split___H"] = histbook_split(False, False, False, False)

library["histbook.cut"] = lambda values: numpy.ma.array(values, dtype=INDEXTYPE)

def calculate(expr, symbols):
    if isinstance(expr, (histbook.expr.Name, histbook.expr.Predicate)):
        return symbols[expr.value]

    elif isinstance(expr, histbook.expr.Const):
        return expr.value

    elif isinstance(expr, histbook.expr.Call) and expr.fcn in library:
        return library[expr.fcn](*(calculate(arg, symbols) for arg in expr.args))
            
    else:
        raise AssertionError(repr(expr))
