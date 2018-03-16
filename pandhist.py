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

def cut(expression):
    return HistogramLayoutBinning([("cut", expression)],
                                  [["fail", "pass"]],
                                  [expression])

class HistogramLayout(object):
    def __init__(self, specification, indexes, expressions, columns):
        self.specification = specification
        self.indexes = indexes
        self.expressions = expressions
        self.columns = columns

    def _newcolumn(self, specification, newcolumns):
        columns = list(self.columns)
        for column in newcolumns:
            if column in columns:
                raise ValueError("attempting to attach {0} twice".format(repr(column)))
            if column == "sumw2":
                columns[0] = "sumw"
            columns.append(column)
        return HistogramLayout(specification, self.indexes, self.expressions, columns)

    def weighted(self):
        return self._newcolumn(self.specification + [("sumw2", "")], ["sumw2"])

    def profile(self, expression):
        return self._newcolumn(self.specification + [("sum", expression), ("sum2", expression)], ["sum({0})".format(expression), "sum2({0})".format(expression)])

    def min(self, expression):
        return self._newcolumn(self.specification + [("min", expression)], ["min({0})".format(expression)])

    def max(self, expression):
        return self._newcolumn(self.specification + [("max", expression)], ["max({0})".format(expression)])

    def minmax(self, expression):
        return self._newcolumn(self.specification + [("min", expression), ("max", expression)], ["min({0})".format(expression), "max({0})".format(expression)])

    def fillable(self, method="python", env={}):
        out = pandas.DataFrame(
            index=pandas.MultiIndex.from_product(self.indexes, names=self.expressions),
            columns=self.columns,
            data=dict((x, float("inf") if x.startswith("min") else float("-inf") if x.startswith("max") else 0.0) for x in self.columns))

        if method == "python":
            fill = _makefill(self.specification, env)
        else:
            raise NotImplementedError("unrecognized fillable method: {0}".format(method))

        out.__dict__["fill"] = types.MethodType(fill, out, out.__class__)
        out.__dict__["fillargs"] = fill.__code__.co_varnames[1:fill.__code__.co_argcount]
        return out

class HistogramLayoutBinning(HistogramLayout):
    def __init__(self, specification, indexes, expressions):
        super(HistogramLayoutBinning, self).__init__(specification, indexes, expressions, ["count"])

    def bin(self, numbins, low, high, expression, closed="left"):
        return HistogramLayoutBinning(self.specification + [("bin", numbins, low, high, closed, expression)],
                                      self.indexes + [_binintervals(numbins, low, high, closed)],
                                      self.expressions + [expression])

    def irrbin(self, edges, expression, closed="left"):
        return HistogramLayoutBinning(self.specification + [("irrbin", edges, closed, expression)],
                                      self.indexes + [_irrbinintervals(edges, closed)],
                                      self.expressions + [expression])

    def cut(self, expression):
        return HistogramLayoutBinning(self.specification + [("cut", expression)],
                                      self.indexes + [["fail", "pass"]],
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
    
def _makefill(specification, env):
    expressions = []
    newspecification = []
    for spec in specification:
        newspecification.append(spec + (ast.parse(spec[-1]).body,))
        expressions.append(newspecification[-1][-1])

    weighted = ("sumw2", "") in specification

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
        elif spec[0] == "cut":
            stridemap[i] = stride
            stride *= 2
        elif spec[0] == "sumw2" or spec[0] == "sum" or spec[0] == "sum2" or spec[0] == "min" or spec[0] == "max":
            pass
        else:
            raise AssertionError(spec[0])

    inputs = []
    symbols = set(env)
    _symbols(expressions, inputs, symbols)

    statements = []
    module = ast.parse("def fill(self{0}{1}): REPLACEME".format("".join(", " + x for x in inputs), ", weight=1.0" if weighted else ""))
    module.body[0].body = statements

    floorsym = _newsymbol(symbols)
    ceilsym = _newsymbol(symbols)
    indexsym = _newsymbol(symbols)
    statements.append(_wrap(ast.Assign([ast.Name(indexsym, ast.Store())], ast.Num(0))))

    column = 1
    quantities = {}
    for i, spec in enumerate(newspecification):
        stmts = spec[-1]
        if len(stmts) > 0:
            if not isinstance(stmts[-1], ast.Expr):
                raise SyntaxError("last statement in a quantity must be a pure expression, not {0}".format(repr(spec[-2])))
            if spec[-2] not in quantities:
                quantity = _newsymbol(symbols)
                statements.extend(stmts[:-1])
                statements.append(_wrap(ast.Assign([ast.Name(quantity, ast.Store())], stmts[-1].value)))
                quantities[spec[-2]] = quantity
            else:
                quantity = quantities[spec[-2]]
        else:
            assert spec[0] == "sumw2"

        if spec[0] == "bin":
            numbins = int(spec[1])
            low = float(spec[2])
            high = float(spec[3])
            closed = spec[4]
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

        elif spec[0] == "irrbin":
            edges = map(float, spec[1])
            closed = spec[2]
            chain = []
            for edgei, edge in reversed(list(enumerate(edges))):
                chain.append("""
elif {QUANTITY} {GT} {EDGE}:
    {INDEX} += {SKIP}
""".format(QUANTITY=quantity,
           GT=">=" if closed == "left" else ">",
           EDGE=edge,
           INDEX=indexsym,
           SKIP=(edgei + 1)*stridemap[i]).strip())
            statements.extend(ast.parse("\n".join(chain)[2:]).body)

        elif spec[0] == "cut":
            statements.extend(ast.parse("""
if {QUANTITY}:
    {INDEX} += {SKIP}
""".format(QUANTITY=quantity,
           INDEX=indexsym,
           SKIP=stridemap[i])).body)

        elif spec[0] == "sumw2":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] += weight*weight".format(INDEX=indexsym, COLUMN=column)).body)
            column += 1

        elif spec[0] == "sum":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] += {WEIGHT}{QUANTITY}".format(INDEX=indexsym, COLUMN=column, WEIGHT="weight*" if weighted else "", QUANTITY=quantity)).body)
            column += 1

        elif spec[0] == "sum2":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] += {WEIGHT}{QUANTITY}*{QUANTITY}".format(INDEX=indexsym, COLUMN=column, WEIGHT="weight*" if weighted else "", QUANTITY=quantity)).body)
            column += 1

        elif spec[0] == "min":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] = min(self.values[{INDEX}, {COLUMN}], {QUANTITY})".format(INDEX=indexsym, COLUMN=column, QUANTITY=quantity)).body)
            column += 1

        elif spec[0] == "max":
            statements.extend(ast.parse("self.values[{INDEX}, {COLUMN}] = max(self.values[{INDEX}, {COLUMN}], {QUANTITY})".format(INDEX=indexsym, COLUMN=column, QUANTITY=quantity)).body)
            column += 1

        else:
            raise AssertionError(spec[0])

    if weighted:
        statements.extend(ast.parse("self.values[{INDEX}, 0] += weight".format(INDEX=indexsym)).body)
    else:
        statements.extend(ast.parse("self.values[{INDEX}, 0] += 1".format(INDEX=indexsym)).body)

    globs = {floorsym: math.floor, ceilsym: math.ceil}
    globs.update(env)
    exec(compile(module, "<generated by pandhist>", "exec"), globs)
    return globs["fill"]

def hadd(histograms):
    out = None
    for histogram in histograms:
        if out is None:
            out = histogram.copy()
        else:
            if not numpy.array_equal(out.index, histogram.index):
                raise ValueError("histogram indexes do not match:\n{0}\n{1}".format(out.index, histogram.index))
            if set(out.columns) != set(histogram.columns):
                raise ValueError("histogram columns do not match:\n{0}\n{1}".format(sorted(out.columns), sorted(histogram.columns)))
            for column in out.columns:
                if column.startswith("min"):
                    numpy.minimum(out[column].values, histogram[column].values, out[column].values)
                elif column.startswith("max"):
                    numpy.maximum(out[column].values, histogram[column].values, out[column].values)
                else:
                    numpy.add(out[column].values, histogram[column].values, out[column].values)
    return out
