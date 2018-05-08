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

import ast
import itertools
import math

import meta
import numpy

class ExpressionError(Exception): pass

class Dim(object):
    def __init__(self, names, expr):
        self.names = names
        self.expr = expr

    def __repr__(self):
        return "Dim({0}, {1})".format(repr(self.names), repr(self.expr))

    def __str__(self):
        return repr(self)

class Expr(object):
    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(self._reprargs()))

    # assumes __eq__ and __lt__ have been defined

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __gt__(self, other):
        return not self.__lt__(other) and not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    recognized = {
        math.sqrt: "sqrt",
        numpy.sqrt: "sqrt",
        }

    @staticmethod
    def parse(expression):
        inverse = {"==": "!=",
                   "!=": "==",
                   "<":  ">=",
                   "<=": ">",
                   ">":  "<=",
                   ">=": "<",
                   "in": "not in",
                   "not in": "in"}

        calculate = {"+": lambda x, y: x + y,
                     "-": lambda x, y: x - y,
                     "*": lambda x, y: x * y,
                     "/": lambda x, y: x / y,
                     "//": lambda x, y: x // y,
                     "%": lambda x, y: x % y,
                     "**": lambda x, y: x ** y,
                     "|": lambda x, y: x | y,
                     "&": lambda x, y: x & y,
                     "^": lambda x, y: x ^ y}

        def not_(expr):
            if isinstance(expr, Relation):
                if expr.cmp == "==":
                    return Relation("!=", expr.left, expr.right)
                elif expr.cmp == "<":
                    return Relation("<=", expr.right, expr.left)
                elif expr.cmp == "<=":
                    return Relation("<", expr.right, expr.left)
                elif expr.cmp == "in":
                    return Relation("not in", expr.right, expr.left)
                elif expr.cmp == "not in":
                    return Relation("in", expr.right, expr.left)
                else:
                    raise AssertionError(expr)

            elif isinstance(expr, And):
                return Or(*[not_(x) for x in expr.args])

            elif isinstance(expr, Or):
                notlogical = [not_(x) for x in expr.args if not isinstance(x, And)]
                logical    = [not_(x) for x in expr.args if     isinstance(x, And)]
                if len(logical) == 0:
                    return And(*notlogical)
                else:
                    return Or(*[And(*([x] + notlogical)) for x in logical])
            else:
                raise AssertionError(expr)

        def and_(*exprs):
            ands       = [x for x in exprs if isinstance(x, And)]
            ors        = [x for x in exprs if isinstance(x, Or)]
            notlogical = [x for x in exprs if not isinstance(x, (And, Or))]
            for x in ands:
                notlogical += x.args
            ors += [Or(*notlogical)]
            out = Or(*[And(*args) for args in itertools.product([x.args for x in ors])])
            if len(out.args) == 0:
                raise AssertionError(out)
            elif len(out.args) == 1:
                return out.args[0]
            else:
                return out

        def or_(*exprs):
            ors    = [x for x in exprs if isinstance(x, Or)]
            others = [x for x in exprs if not isinstance(x, Or)]
            for x in ors:
                others += x.args
            return Or(*others)

        globs = globals()

        def resolve(node):
            if isinstance(node, ast.Attribute):
                return getattr(resolve(node.value), node.attr)
            elif isinstance(node, ast.Name):
                return globs[node.id]
            else:
                raise ExpressionError("not a function name: {0}".format(meta.dump_python_source(node).strip()))

        names = []
        def recurse(node, relations=False, intervals=False):
            if isinstance(node, ast.Num):
                return Const(node.n)

            elif isinstance(node, ast.Str):
                return Const(node.s)

            elif isinstance(node, ast.Dict) and len(node.keys) == 0:
                return Const(set())

            elif isinstance(node, ast.Set):
                content = [recurse(x) for x in node.elts]
                if all(isinstance(x, Const) for x in content):
                    return Const(set(x.value for x in content))
                else:
                    raise ExpressionError("sets in expressions may not contain variable contents: {0}".format(meta.dump_python_source(node).strip()))

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id == "None" or (node.id in globs and globs[node.id] is None):
                    return Const(None)
                elif node.id == "True" or (node.id in globs and globs[node.id] is True):
                    return Const(True)
                elif node.id == "False" or (node.id in globs and globs[node.id] is False):
                    return Const(False)
                else:
                    if node.id not in names:
                        names.append(node.id)
                    return Name(node.id)

            elif isinstance(node, getattr(ast, "NameConstant", tuple)):  # node will never be tuple
                if node.value is None:
                    return Const(None)
                elif node.value is True:
                    return Const(True)
                elif node.value is False:
                    return Const(False)
                else:
                    raise AssertionError(node)

            elif relations and isinstance(node, ast.Compare) and len(node.ops) == 1:
                if   isinstance(node.ops[0], ast.Eq):    cmp, swap = "==",     None
                elif isinstance(node.ops[0], ast.NotEq): cmp, swap = "!=",     None
                elif isinstance(node.ops[0], ast.Lt):    cmp, swap = "<",      False
                elif isinstance(node.ops[0], ast.LtE):   cmp, swap = "<=",     False
                elif isinstance(node.ops[0], ast.Gt):    cmp, swap = "<",      True
                elif isinstance(node.ops[0], ast.GtE):   cmp, swap = "<=",     True
                elif isinstance(node.ops[0], ast.In):    cmp, swap = "in",     False
                elif isinstance(node.ops[0], ast.NotIn): cmp, swap = "not in", False
                else:
                    raise ExpressionError("only comparision relations supported: '==', '!=', '<', '<=', '>', '>=', 'in', and 'not in': {0}".format(meta.dump_python_source(node).strip()))
                
                left = recurse(node.left)
                right = recurse(node.comparators[0])
                if swap is True:
                    left, right = right, left
                elif swap is None:
                    left, right = sorted([left, right])

                if (cmp == "in" or cmp == "not in") and not (isinstance(right, Const) and isinstance(right.value, set)):
                    raise ExpressionError("comparisons 'in' and 'not in' can only be used with a set: {0}".format(meta.dump_python_source(node).strip()))

                return Relation(cmp, left, right)

            elif intervals and isinstance(node, ast.Compare) and len(node.ops) == 2:
                if isinstance(node.ops[0], ast.LtE) and isinstance(node.ops[1], ast.Lt):
                    low = recurse(node.left)
                    high = recurse(node.comparators[1])
                    lowclosed = True
                elif isinstance(node.ops[0], ast.Lt) and isinstance(node.ops[1], ast.LtE):
                    low = recurse(node.left)
                    high = recurse(node.comparators[1])
                    lowclosed = False
                elif isinstance(node.ops[0], ast.Gt) and isinstance(node.ops[1], ast.GtE):
                    low = recurse(node.comparators[1])
                    high = recurse(node.left)
                    lowclosed = True
                elif isinstance(node.ops[0], ast.GtE) and isinstance(node.ops[1], ast.Gt):
                    low = recurse(node.comparators[1])
                    high = recurse(node.left)
                    lowclosed = False
                else:
                    raise ExpressionError("interval comparisons may be A <= x < B, A < x <= B, A > x >= B, A >= x > B, but no other combination: {0}".format(meta.dump_python_source(node).strip()))

                arg = recurse(node.comparators[0])
                if isinstance(low, Const) and isinstance(high, Const) and not isinstance(arg, Const):
                    return Interval(arg, low, high, lowclosed=lowclosed)
                else:
                    raise ExpressionError("interval comparisons must have known constants on the low and high edge with an unknown expression in the middle: {0}".format(meta.dump_python_source(node).strip()))

            elif isinstance(node, ast.Compare):
                raise ExpressionError("comparison operators are only allowed at the top of an expression and only interval ranges are allowed to be chained: {0}".format(meta.dump_python_source(node).strip()))

            elif relations and isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return not_(recurse(node.operand, relations=True))

            elif relations and isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                return and_(*[recurse(x, relations=True) for x in node.values])

            elif relations and isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                return or_(*[recurse(x, relations=True) for x in node.values])

            elif isinstance(node, ast.BoolOp):
                raise ExpressionError("logical operators are only allowed at the top of an expression: {0}".format(meta.dump_python_source(node).strip()))
                
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                content = recurse(node.operand)
                if isinstance(content, Const):
                    return Const(-content.value)
                else:
                    return PlusMinus.negate(content)

            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
                return recurse(node.operand)

            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
                content = recurse(node.operand)
                if isinstance(content, Const):
                    return Const(~content.value)
                else:
                    return BitAnd.negate(content)

            elif isinstance(node, ast.UnaryOp):
                raise ExpressionError("only unary operators supported: 'not', '-', '+', and '~': {0}".format(meta.dump_python_source(node).strip()))

            elif isinstance(node, ast.BinOp):
                if   isinstance(node.op, ast.Add):      fcn = "+"
                elif isinstance(node.op, ast.Sub):      fcn = "-"
                elif isinstance(node.op, ast.Mult):     fcn = "*"
                elif isinstance(node.op, ast.Div):      fcn = "/"
                elif isinstance(node.op, ast.FloorDiv): fcn = "//"
                elif isinstance(node.op, ast.Mod):      fcn = "%"
                elif isinstance(node.op, ast.Pow):      fcn = "**"
                elif isinstance(node.op, ast.BitOr):    fcn = "|"
                elif isinstance(node.op, ast.BitAnd):   fcn = "&"
                elif isinstance(node.op, ast.BitXor):   fcn = "^"
                else:
                    raise ExpressionError("only binary operators supported: '+', '-', '*', '/', '//', '%', '**', '|', '&', and '^': {0}".format(meta.dump_python_source(node).strip()))

                left = recurse(node.left)
                right = recurse(node.right)

                if isinstance(left, Const) and isinstance(right, Const):
                    return Const(calculate[fcn](left.value, right.value))

                if fcn == "+":
                    return PlusMinus.combine(left, right)
                elif fcn == "-":
                    return PlusMinus.combine(left, PlusMinus.negate(right))
                elif fcn == "*":
                    return PlusMinus.distribute(left, right)
                elif fcn == "/":
                    # PlusMinus is implemented as a RingAlgebra, but it's really a Field
                    right = PlusMinus.normalform(right)

                    if len(right.pos) == len(right.neg) == 0:
                        negation = TimesDiv(TimesDiv.negateval(right.const), (), ())
                    elif right.const == PlusMinus.identity and len(right.pos) == 1 and len(right.neg) == 0:
                        negation = TimesDiv.negate(right.pos[0])
                    elif right.const == PlusMinus.identity and len(right.pos) == 0 and len(right.neg) == 1:
                        negation = TimesDiv.negate(right.neg[0])
                        negation.const = PlusMinus.negateval(negation.const)
                    else:
                        negation = TimesDiv.negate(right)   # additive terms in the denominator

                    return PlusMinus.distribute(left, negation)

                else:
                    return BinOp(fcn, left, right)

            elif isinstance(node, ast.Call):
                if node.func.id in Expr.recognized.values():
                    fcn = node.func.id
                else:
                    fcn = Expr.recognized.get(resolve(node.func), None)
                if fcn is None:
                    raise ExpressionError("unhandled function in expression: {0}".format(meta.dump_python_source(node).strip()))
                return Call(fcn, tuple(recurse(x) for x in node.args))

            else:
                ExpressionError("unhandled syntax in expression: {0}".format(meta.dump_python_source(node).strip()))

        if callable(expression):
            fcn = meta.decompiler.decompile_func(expression)
            if isinstance(fcn, ast.FunctionDef) and len(fcn.body) == 1 and isinstance(fcn.body[0], ast.Return):
                return Dim(names, recurse(fcn.body[0].value, relations=True, intervals=True))
            elif isinstance(fcn, ast.Lambda):
                return Dim(names, recurse(fcn.body.value, relations=True, intervals=True))
        else:
            mod = ast.parse(expression)
            if len(mod.body) == 1 and isinstance(mod.body[0], ast.Expr):
                return Dim(names, recurse(mod.body[0].value, relations=True, intervals=True))

        raise TypeError("expression must be a one-line string, one-line function, or lambda expression, not {0}".format(repr(expression)))

# the details of the canonical order are not important; we just need a way to ignore order sometimes

class Const(Expr):
    _order = 0

    def __init__(self, value):
        self.value = value

    def _reprargs(self):
        return (repr(self.value),)

    def __str__(self):
        return str(self.value)

    def __hash__(self):
        if isinstance(self.value, set):
            value = (set, tuple(sorted(self.value)))
        else:
            value = self.value
        return hash((Const, value))

    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value

    def __lt__(self, other):
        if self._order == other._order:
            if type(self.value) == type(other.value):
                return self.value < other.value
            else:
                return type(self.value) < type(other.value)
        else:
            return self._order < other._order

class Name(Expr):
    _order = 1

    def __init__(self, value):
        self.value = value

    def _reprargs(self):
        return (repr(self.value),)

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash((Name, self.value))

    def __eq__(self, other):
        return isinstance(other, Name) and self.value == other.value

    def __lt__(self, other):
        if self._order == other._order:
            return self.value < other.value
        else:
            return self._order < other._order

class Call(Expr):
    _order = 2

    def __init__(self, fcn, *args):
        self.fcn = fcn
        self.args = args

    def _reprargs(self):
        return (repr(self.fcn),) + tuple(repr(x) for x in self.args)

    def __str__(self):
        return "{0}({1})".format(self.fcn, ", ".join(str(x) for x in self.args))

    def __hash__(self):
        return hash((Call, self.fcn, self.args))

    def __eq__(self, other):
        return isinstance(other, Call) and self.fcn == other.fcn and self.args == other.args

    def __lt__(self, other):
        if self._order == other._order:
            return (self.fcn, self.args) < (other.fcn, other.args)
        else:
            return self._order < other._order

class BinOp(Call):
    def __str__(self):
        return (" " + self.fcn + " ").join(("(" + str(x) + ")") if isinstance(x, BinOp) else str(x) for x in self.args)

class RingAlgebra(Call):
    _order = 3

    def __init__(self, const, pos, neg):
        self.const = const
        self.pos = pos
        self.neg = neg

    def _reprargs(self):
        return (repr(self.const), repr(self.pos), repr(self.neg))

    def __hash__(self):
        return hash((self.__class__, self.const, self.pos, self.neg))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.const == other.const and self.pos == other.pos and self.neg == other.neg

    def __lt__(self, other):
        if self._order == other._order:
            return (self.const, self.pos, self.neg) < (other.const, other.pos, other.neg)
        else:
            return self._order < other._order

    commutative = False

    @classmethod
    def negate(op, arg):
        arg = op.normalform(arg)
        return op(op.negateval(arg.const), arg.neg, arg.pos)

    @classmethod
    def collect(op, arg):
        return arg

    @classmethod
    def combine(op, left, right):
        left, right = op.normalform(left), op.normalform(right)

        if op.commutative:
            pos = tuple(sorted(left.pos + right.pos))
            neg = tuple(sorted(left.neg + right.neg))
        else:
            pos = left.pos + right.pos
            neg = left.neg + right.neg

        return op.collect(op(op.calcval(left.const, right.const), pos, neg))

class RingAlgebraMultLike(RingAlgebra):
    @classmethod
    def normalform(op, arg):
        if isinstance(arg, op):
            return arg
        elif isinstance(arg, Const):
            return op(arg.value, (), ())
        else:
            return op(op.identity, (arg,), ())

    def similar(self, other):
        return isinstance(other, self.__class__) and self.pos == other.pos and self.neg == other.neg
        
class RingAlgebraAddLike(RingAlgebra):
    @classmethod
    def normalform(op, arg):
        if isinstance(arg, op):
            return arg
        else:
            arg = op.subop.normalform(arg)
            if len(arg.pos) == len(arg.neg) == 0:
                return op(arg.const, (), ())
            elif op.isnegval(arg.const):
                return op(op.identity, (), (op.subop(op.negateval(arg.const), arg.pos, arg.neg),))
            else:
                return op(op.identity, (arg,), ())

    @classmethod
    def collect(op, arg):
        const = arg.const
        terms = []

        def cancel(x):
            pos, neg = list(x.pos), []
            for y in x.neg:
                try:
                    i = x.pos.index(y)
                except ValueError:
                    neg.append(y)
                else:
                    del pos[i]
            return op.subop(x.const, tuple(pos), tuple(neg))

        for x in arg.pos:
            x = cancel(x)
            if x.const == op.identity:
                pass
            elif len(x.pos) == len(x.neg) == 0:
                const = op.calcval(const, x.const)
            else:
                for y in terms:
                    if x.similar(y):
                        y.const = op.calcval(x.const, y.const)
                        break
                else:
                    terms.append(x)

        for x in arg.neg:
            x = cancel(x)
            if x.const == op.identity:
                pass
            elif len(x.pos) == len(x.neg) == 0:
                const = op.calcval(const, op.negateval(x.const))
            else:
                for y in terms:
                    if x.similar(y):
                        y.const = op.calcval(op.negateval(x.const), y.const)
                        break
                else:
                    terms.append(op.subop(op.negateval(x.const), x.pos, x.neg))

        posterms, negterms = [], []
        for x in terms:
            if x.const == op.identity:
                pass
            elif op.isnegval(x.const):
                x.const = op.negateval(x.const)
                negterms.append(x)
            else:
                posterms.append(x)

        if op.commutative:
            posterms.sort()
            negterms.sort()

        return op(const, tuple(posterms), tuple(negterms))
        
    @classmethod
    def distribute(op, left, right):
        left, right = op.normalform(left), op.normalform(right)
        pos, neg = [], []

        pos += [op.subop.combine(x, Const(right.const)) for x in left.pos]
        neg += [op.subop.combine(x, Const(right.const)) for x in left.neg]
        pos += [op.subop.combine(Const(left.const), y) for y in right.pos]
        neg += [op.subop.combine(Const(left.const), y) for y in right.neg]

        pos += [op.subop.combine(x, y) for x, y in itertools.product(left.pos, right.pos)]
        neg += [op.subop.combine(x, y) for x, y in itertools.product(left.pos, right.neg)]
        pos += [op.subop.combine(x, y) for x, y in itertools.product(left.neg, right.neg)]
        neg += [op.subop.combine(x, y) for x, y in itertools.product(left.neg, right.pos)]

        return op.collect(op(op.identity, tuple(pos), tuple(neg)))

    def simplify(self):
        out = self.__class__(self.const, self.pos, self.neg)

        if len(out.pos) == len(out.neg) == 0:
            return Const(out.const)

        elif out.const == out.identity and len(out.pos) + len(out.neg) == 1:
            if len(out.pos) == 1:
                out = out.pos[0]
            else:
                out = out.neg[0]

            if len(out.pos) == len(out.neg) == 0:
                return Const(out.const)
            elif out.const == out.identity and len(out.pos) + len(out.neg) == 1:
                if len(out.pos) == 1:
                    return out.pos[0]
                else:
                    return out.neg[0]

        return out

class RingAlgebraBinOp(object):
    def __str__(self):
        out = []
        if self.const != self.identity or len(self.pos) == 0:
            out.append(repr(self.const))
        for x in self.pos:
            if len(out) > 0:
                out.append(self.posop)
            out.append(str(x))
        for x in self.neg:
            out.append(self.negop)
            out.append(str(x))
        return "".join(out)

class TimesDiv(RingAlgebraBinOp, RingAlgebraMultLike):
    posop = "*"
    negop = "/"

    commutative = True
    identity = 1

    @staticmethod
    def negateval(value):
        return 1.0 / value

    @staticmethod
    def calcval(left, right):
        return left * right

class PlusMinus(RingAlgebraBinOp, RingAlgebraAddLike):
    posop = " + "
    negop = " - "

    subop = TimesDiv
    commutative = True
    identity = 0

    @staticmethod
    def negateval(value):
        return -value

    @staticmethod
    def isnegval(value):
        return value < 0

    @staticmethod
    def calcval(left, right):
        return left + right

class Relation(Expr):
    _order = 4

    def __init__(self, cmp, left, right):
        self.cmp = cmp
        self.left = left
        self.right = right

    def _reprargs(self):
        return (repr(self.cmp), repr(self.left), repr(self.right))

    def __str__(self):
        return "{0} {1} {2}".format(str(self.left), self.cmp, str(self.right))

    def __hash__(self):
        return hash((Relation, self.cmp, self.left, self.right))

    def __eq__(self, other):
        return isinstance(other, Relation) and self.cmp == other.cmp and self.left == other.left and self.right == other.right

    def __lt__(self, other):
        if self._order == other._order:
            return (self.cmp, self.left, self.right) < (other.cmp, other.left, other.right)
        else:
            return self._order < other._order

class Interval(Expr):
    _order = 5

    def __init__(self, arg, low, high, lowclosed=True):
        self.arg = arg
        self.low = low
        self.high = high
        self.lowclosed = lowclosed

    def _reprargs(self):
        if self.lowclosed:
            return (repr(self.low), repr(self.high), repr(self.arg))
        else:
            return (repr(self.low), repr(self.high), repr(self.arg), "lowclosed=False")

    def __str__(self):
        if self.lowclosed:
            return "{0} <= {1} < {2}".format(str(self.low), str(self.arg), str(self.high))
        else:
            return "{0} < {1} <= {2}".format(str(self.low), str(self.arg), str(self.high))

    def __hash__(self):
        return hash((Interval, self.arg, self.low, self.high, self.lowclosed))

    def __eq__(self, other):
        return isinstance(other, Interval) and self.arg == other.arg and self.low == other.low and self.high == other.high and self.lowclosed == other.lowclosed

    def __lt__(self, other):
        if self._order == other._order:
            return (self.arg, self.low, self.high, self.lowclosed) < (other.arg, other.low, other.high, other.lowclosed)
        else:
            return self._order < other._order

class Logical(Expr):
    _order = 6

    def __init__(self, *args):
        self.args = args

    def _reprargs(self):
        return tuple(repr(x) for x in self.args)

    def __hash__(self):
        return hash((self.__class__,) + self.args)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.args == other.args

    def __lt__(self, other):
        if self._order == other._order:
            return (self.__class__.__name__, self.args) < (other.__class__.__name__, self.args)
        else:
            return self._order < other._order

class And(Logical):
    def __str__(self):
        return " and ".format(str(x) for x in self.args)

class Or(Logical):
    def __str__(self):
        return " or ".format("(" + str(x) + ")" if isinstance(x, And) else str(x) for x in self.args)
