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

import ast
import math
import types

import numpy
import pandas

def _irrbinintervals(edges, closed):
    if len(edges) == 0:
        raise ValueError("at least one bin edge must be provided")
    if closed != "left" and closed != "right":
        raise ValueError("closed must be 'left' for [low, high) or 'right' for (low, high]")
    underflow = pandas.Interval(float("-inf"), edges[0], closed)
    overflow  = pandas.Interval(edges[-1], float("inf"), closed)
    return [underflow] + [pandas.Interval(a, b, closed=closed) for a, b in zip(edges[:-1], edges[1:])] + [overflow]

def _binintervals(numbins, low, high, closed):
    if numbins <= 0:
        raise ValueError("numbins must be at least 1")
    edges = numpy.linspace(low, high, numbins + 1)
    return _irrbinintervals(edges, closed)

def bin(numbins, low, high, expression, closed="left"):
    return HistogramLayoutBinning([("bin", numbins, low, high, closed, expression)],
                                  [_binintervals(numbins, low, high, closed)],
                                  [expression])

def irrbin(edges, expression, closed="left"):
    return HistogramLayoutBinning([("irrbin", edges, closed, expression)],
                                  [_irrbinintervals(edges, closed)],
                                  [expression])

def frac(expression):
    return HistogramLayoutBinning([("frac", expression)],
                                  [["numer", "denom"]],
                                  [expression])

def cut(expression):
    return HistogramLayoutBinning([("cut", expression)],
                                  [["pass", "fail"]],
                                  [expression])

class HistogramLayout(object):
    def __init__(self, specification, indexes, expressions, columns):
        self.specification = specification
        self.indexes = indexes
        self.expressions = expressions
        self.columns = columns

    def _newcolumn(self, specification, column):
        if column in self.columns:
            raise ValueError("attempting to attach {0} twice".format(repr(column)))
        return HistogramLayout(specification, self.indexes, self.expressions, self.columns + [column])

    def sumw2(self):
        return self._newcolumn(self.specification + [("sumw2", "")], "sumw2")

    def sumwx(self, expression):
        return self._newcolumn(self.specification + [("sumwx", expression)], "sumwx({0})".format(expression))

    def sumwx2(self, expression):
        return self._newcolumn(self.specification + [("sumwx2", expression)], "sumwx2({0})".format(expression))

    def min(self, expression):
        return self._newcolumn(self.specification + [("min", expression)], "min({0})".format(expression))

    def max(self, expression):
        return self._newcolumn(self.specification + [("max", expression)], "max({0})".format(expression))

    def toDF(self):
        out = pandas.DataFrame(
            index=pandas.MultiIndex.from_product(self.indexes, names=self.expressions),
            columns=self.columns,
            data=dict((x, float("inf") if x.startswith("min") else float("-inf") if x.startswith("max") else 0.0) for x in self.columns))
        out.__dict__["fill"] = types.MethodType(_makefill(self.specification), out, out.__class__)
        return out

class HistogramLayoutBinning(HistogramLayout):
    def __init__(self, specification, indexes, expressions):
        super(HistogramLayoutBinning, self).__init__(specification, indexes, expressions, ["sumw"])

    def bin(self, numbins, low, high, expression, closed="left"):
        return HistogramLayoutBinning(self.specification + [("bin", numbins, low, high, closed, expression)],
                                      self.indexes + [_binintervals(numbins, low, high, closed)],
                                      self.expressions + [expression])

    def irrbin(self, edges, expression, closed="left"):
        return HistogramLayoutBinning(self.specification + [("irrbin", edges, closed, expression)],
                                      self.indexes + [_irrbinintervals(edges, closed)],
                                      self.expressions + [expression])

    def frac(self, expression):
        return HistogramLayoutBinning(self.specification + [("frac", expression)],
                                      self.indexes + [["numer", "denom"]],
                                      self.expressions + [expression])

    def cut(self, expression):
        return HistogramLayoutBinning(self.specification + [("cut", expression)],
                                      self.indexes + [["pass", "fail"]],
                                      self.expressions + [expression])

def _replace(node, **replacements):
    if isinstance(node, ast.Name) and node.id in replacements:
        return replacements[node.id]
    elif isinstance(node, ast.AST):
        for n in node._fields:
            setattr(node, n, _replace(getattr(node, n), **replacements))
        return node
    elif isinstance(node, dict):
        return dict((n, _replace(x, **replacements)) for n, x in node.items())
    elif isinstance(node, list):
        return [_replace(x, **replacements) for x in node]
    else:
        return node

def _symbols(node, inputs, symbols):
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        if node.id not in symbols:
            inputs.append(node.id)
        symbols.add(node.id)
    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        symbols.add(node.id)
    elif isinstance(node, ast.AST):
        for n in node._fields:
            _symbols(getattr(node, n), inputs, symbols)
    elif isinstance(node, dict):
        for x in node.values():
            _symbols(x, inputs, symbols)
    elif isinstance(node, list):
        for x in node:
            _symbols(x, inputs, symbols)

def _newsymbol(symbols):
    trial = None
    while trial is None or trial in symbols:
        trial = "_{0}".format(_newsymbol.n)
        _newsymbol.n += 1
    symbols.add(trial)
    return trial
        
_newsymbol.n = 0

def _wrap(node):
    if isinstance(node, ast.AST):
        if not hasattr(node, "lineno"):
            node.lineno = 1
        if not hasattr(node, "col_offset"):
            node.col_offset = 0
        for n in node._fields:
            _wrap(getattr(node, n))
    elif isinstance(node, dict):
        for x in node.values():
            _wrap(x)
    elif isinstance(node, list):
        for x in node:
            _wrap(x)
    return node
    
def _makefill(specification):
    expressions = []
    newspecification = []
    for spec in specification:
        newspecification.append(spec + (ast.parse(spec[-1]).body,))
        expressions.append(newspecification[-1][-1])

    stridemap = {}
    stride = 1
    for i, spec in reversed(list(enumerate(specification))):
        if spec[0] == "bin":
            numbins = int(spec[1])
            stridemap[i] = stride
            stride *= numbins + 2
        elif spec[0] == "irrbin":
            numedges = len(spec[1])
            stridemap[i] = stride
            stride *= numedges + 1
        elif spec[0] == "frac":
            stridemap[i] = stride
            stride *= 2
        elif spec[0] == "cut":
            stridemap[i] = stride
            stride *= 2
        else:
            raise AssertionError(spec[0])

    inputs = []
    symbols = set()
    _symbols(expressions, inputs, symbols)

    statements = []
    module = ast.parse("def fill(self{0}, weight=1.0): REPLACEME".format("".join(", " + x for x in inputs)))
    module.body[0].body = statements

    floorsym = _newsymbol(symbols)
    ceilsym = _newsymbol(symbols)
    indexsym = _newsymbol(symbols)
    statements.append(_wrap(ast.Assign([ast.Name(indexsym, ast.Store())], ast.Num(0))))

    for i, spec in enumerate(newspecification):
        stmts = spec[-1]
        if not isinstance(stmts[-1], ast.Expr):
            raise SyntaxError("last statement in a quantity must be a pure expression, not {0}".format(repr(spec[-2])))

        if spec[0] == "bin":
            numbins = int(spec[1])
            low = float(spec[2])
            high = float(spec[3])
            closed = spec[4]
            quantity = _newsymbol(symbols)
            statements.extend(stmts[:-1])
            statements.append(_wrap(ast.Assign([ast.Name(quantity, ast.Store())], stmts[-1].value)))
            statements.extend(ast.parse("""
if {QUANTITY} {GT} {HIGH}:
    {INDEX} += {HIGHSKIP}
elif {QUANTITY} {GT} {LOW}:
    {INDEX} += ({ONE_PLUS}int({FLOOR_OR_CEIL}({FACTOR}*({QUANTITY} - {LOW}))))*{STRIDE}
""".format(QUANTITY=quantity,
           GT=">=" if closed == "left" else ">",
           HIGH=high,
           INDEX=indexsym,
           HIGHSKIP=(numbins + 1)*stridemap[i],
           LOW=low,
           ONE_PLUS="1 + " if closed == "left" else "",
           FLOOR_OR_CEIL=floorsym if closed == "left" else ceilsym,
           FACTOR=numbins/(high - low),
           STRIDE=stridemap[i]
           )).body)
            
        else:
            raise NotImplementedError

    statements.extend(ast.parse("""
self.values[{INDEX}, 0] += weight
""".format(INDEX=indexsym)).body)

    print meta.dump_python_source(module).strip()

    globs = {floorsym: math.floor, ceilsym: math.ceil}
    exec(compile(module, "<generated by pandhist>", "exec"), globs)
    return globs["fill"]

import meta

