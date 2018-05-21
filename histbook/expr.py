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
import functools
import itertools
import math
import sys
import types
try:
    import cPickle as pickle
except ImportError:
    import pickle

import meta
import numpy

class ExpressionError(Exception): pass

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

    def __cmp__(self, other):
        if self.__eq__(other):
            return 0
        elif self.__lt__(other):
            return -1
        else:
            return 1

    @staticmethod
    def parse(expression, defs=None, returnlabel=False):
        _defs = {"pi": Const(math.pi), "e": Const(math.e), "inf": Const(float("inf")), "nan": Const(float("nan"))}
        if defs is not None:
            for n, x in defs.items():
                if isinstance(x, Expr):
                    _defs[n] = x
                elif sys.version_info[0] < 3 and isinstance(x, (str, unicode)):
                    _defs[n] = Expr.parse(x)
                elif sys.version_info[0] >= 3 and isinstance(x, str):
                    _defs[n] = Expr.parse(x)
                else:
                    try:
                        _defs[n] = Const(pickle.loads(pickle.dumps(x)))
                    except:
                        raise ExpressionError("object can't be included in an expression as symbol {0} because it refers to an unserializable object".format(repr(n)))

        pyast = None
        label = None
        params = None
        if isinstance(expression, types.FunctionType):   # more specific than callable(...)
            fcn = meta.decompiler.decompile_func(expression)
            if isinstance(fcn, ast.FunctionDef) and len(fcn.body) == 1 and isinstance(fcn.body[0], ast.Return):
                pyast = fcn.body[0].value
                label = expression.__name__
            elif isinstance(fcn, ast.Lambda):
                pyast = fcn.body.value
                label = meta.dump_python_source(pyast).strip()
            params = expression.__code__.co_varnames[expression.__code__.co_argcount]

        elif (sys.version_info[0] < 3 and isinstance(expression, basestring)) or (sys.version_info[0] >= 3 and isinstance(expression, str)):
            mod = ast.parse(expression)
            if len(mod.body) == 1 and isinstance(mod.body[0], ast.Expr):
                pyast = mod.body[0].value
                label = expression
                
        if pyast is None:
            raise TypeError("expression must be a one-line string, one-line function, or lambda expression, not {0}".format(repr(expression)))

        calculate = {"+": lambda x, y: x + y,
                     "-": lambda x, y: x - y,
                     "*": lambda x, y: x * y,
                     "/": lambda x, y: float(x) / float(y),
                     "//": lambda x, y: int(x // y),
                     "%": lambda x, y: x % y,
                     "**": lambda x, y: x ** y,
                     "|": lambda x, y: numpy.uint64(x) | numpy.uint64(y),
                     "&": lambda x, y: numpy.uint64(x) & numpy.uint64(y),
                     "^": lambda x, y: numpy.uint64(x) ^ numpy.uint64(y)}

        env = dict(globals())
        def resolve(node):
            if isinstance(node, ast.Attribute):
                return getattr(resolve(node.value), node.attr, None)
            elif isinstance(node, ast.Name):
                return env.get(node.id, None)
            else:
                raise ExpressionError("functions must be named, not constructed: {0}".format(meta.dump_python_source(node).strip()))

        def recurse(node, relations=False):
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
                if node.id == "None":
                    return Const(None)
                elif node.id == "True":
                    return Const(True)
                elif node.id == "False":
                    return Const(False)
                elif node.id in _defs:
                    return _defs[node.id]
                elif params is not None and node.id not in params:
                    if node.id in env:
                        try:
                            return Const(pickle.loads(pickle.dumps(env[node.id])))
                        except:
                            raise ExpressionError("symbol {0} can't be included in an expression because it refers to an unserializable object in the global scope".format(repr(node.id)))
                    else:
                        raise ExpressionError("symbol {0} is not a function parameter and not in the global scope".format(repr(node.id)))
                else:
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

            elif relations and isinstance(node, ast.Compare) and len(node.ops) > 1:
                return recurse(ast.BoolOp(ast.And(), [ast.Compare(node.left if i == 0 else node.comparators[i - 1], [node.ops[i]], [node.comparators[i]]) for i in range(len(node.ops))]), relations=True)

            elif isinstance(node, ast.Compare):
                raise ExpressionError("comparison operators are only allowed at the top of an expression: {0}".format(meta.dump_python_source(node).strip()))

            elif relations and isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                content = recurse(node.operand, relations=True)
                if isinstance(content, Name):
                    return Predicate(content.value, positive=False)
                else:
                    return Logical.negate(content).simplify()

            elif relations and isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                return functools.reduce(LogicalAnd.combine, [Logical.normalform(recurse(x, relations=True)) for x in node.values]).simplify()

            elif relations and isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                return functools.reduce(LogicalOr.combine, [Logical.normalform(recurse(x, relations=True)) for x in node.values]).simplify()

            elif isinstance(node, ast.BoolOp):
                raise ExpressionError("logical operators are only allowed at the top of an expression: {0}".format(meta.dump_python_source(node).strip()))
                
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                content = recurse(node.operand)
                if isinstance(content, Const):
                    return Const(-content.value)
                else:
                    return PlusMinus.negate(content).simplify()

            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
                return recurse(node.operand)

            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
                content = recurse(node.operand)
                if isinstance(content, Const):
                    return Const(~content.value)
                else:
                    return BitAnd.negate(content).simplify()

            elif isinstance(node, ast.UnaryOp):
                raise ExpressionError("only unary operators supported: 'not', '-', '+', and '~': {0}".format(meta.dump_python_source(node).strip()))

            elif isinstance(node, ast.BinOp):
                if   isinstance(node.op, ast.Add):      fcn = "+"
                elif isinstance(node.op, ast.Sub):      fcn = "-"
                elif isinstance(node.op, ast.Mult):     fcn = "*"
                elif isinstance(node.op, ast.Div):      fcn = "/"
                elif isinstance(node.op, ast.FloorDiv): op, fcn = "//", "floor_divide"
                elif isinstance(node.op, ast.Mod):      op, fcn = "%",  "mod"
                elif isinstance(node.op, ast.Pow):      op, fcn = "**", "pow"
                elif isinstance(node.op, ast.BitOr):    fcn = "|"
                elif isinstance(node.op, ast.BitAnd):   fcn = "&"
                elif isinstance(node.op, ast.BitXor):   op, fcn = "^",  "xor"
                else:
                    raise ExpressionError("only binary operators supported: '+', '-', '*', '/', '//', '%', '**', '|', '&', and '^': {0}".format(meta.dump_python_source(node).strip()))

                left = recurse(node.left)
                right = recurse(node.right)

                if isinstance(left, Const) and isinstance(right, Const):
                    return Const(calculate[fcn](left.value, right.value))

                if fcn == "+":
                    return PlusMinus.combine(left, right).simplify()
                elif fcn == "-":
                    return PlusMinus.combine(left, PlusMinus.negate(right)).simplify()
                elif fcn == "*":
                    return PlusMinus.distribute(left, right).simplify()
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

                    return PlusMinus.distribute(left, negation).simplify()
                
                elif fcn == "pow" and isinstance(right, Const) and right.value == round(right.value) and 1 <= right.value < 5:
                    n = int(right.value)
                    left = PlusMinus.normalform(left)
                    if left.const == PlusMinus.identity and len(left.pos) == 1 and len(left.neg) == 0:
                        return PlusMinus(PlusMinus.identity, (TimesDiv(left.pos[0].const**n, tuple(sorted(left.pos[0].pos * n)), tuple(sorted(left.pos[0].neg * n))),), ()).simplify()
                    elif left.const == PlusMinus.identity and len(left.pos) == 0 and len(left.neg) == 1 and n % 2 == 0:
                        return PlusMinus(PlusMinus.identity, (TimesDiv(left.neg[0].const**n, tuple(sorted(left.neg[0].pos * n)), tuple(sorted(left.neg[0].neg * n))),), ()).simplify()
                    elif left.const == PlusMinus.identity and len(left.pos) == 0 and len(left.neg) == 1:
                        return PlusMinus(PlusMinus.identity, (), (TimesDiv(left.neg[0].const**n, tuple(sorted(left.neg[0].pos * n)), tuple(sorted(left.neg[0].neg * n))),)).simplify()
                    else:
                        return PlusMinus(PlusMinus.identity, (TimesDiv(TimesDiv.identity, tuple((left,) * n), ()),), ()).simplify()

                elif fcn == "pow" and isinstance(right, Const) and right.value == round(right.value) and -5 < right.value <= -1:
                    n = -int(right.value)
                    left = PlusMinus.normalform(left)
                    if left.const == PlusMinus.identity and len(left.pos) == 1 and len(left.neg) == 0:
                        return PlusMinus(PlusMinus.identity, (TimesDiv(left.pos[0].const**(-n), tuple(sorted(left.pos[0].neg * n)), tuple(sorted(left.pos[0].pos * n))),), ()).simplify()
                    elif left.const == PlusMinus.identity and len(left.pos) == 0 and len(left.neg) == 1 and n % 2 == 0:
                        return PlusMinus(PlusMinus.identity, (TimesDiv(left.neg[0].const**(-n), tuple(sorted(left.neg[0].neg * n)), tuple(sorted(left.neg[0].pos * n))),), ()).simplify()
                    elif left.const == PlusMinus.identity and len(left.pos) == 0 and len(left.neg) == 1:
                        return PlusMinus(PlusMinus.identity, (), (TimesDiv(left.neg[0].const**(-n), tuple(sorted(left.neg[0].neg * n)), tuple(sorted(left.neg[0].pos * n))),)).simplify()
                    else:
                        return PlusMinus(PlusMinus.identity, (TimesDiv(TimesDiv.identity, (), tuple((left,) * n)),), ()).simplify()

                elif fcn == "&":
                    raise NotImplementedError

                elif fcn == "|":
                    raise NotImplementedError

                else:
                    return BinOp(fcn, left, right, op)

            elif isinstance(node, ast.Call):
                fcn = Expr.recognized.get(resolve(node.func), None)
                if fcn is None and node.func.id in Expr.recognized.values():
                    fcn = node.func.id
                else:
                    raise ExpressionError("unhandled function in expression: {0}".format(meta.dump_python_source(node).strip()))
                return Call(fcn, *(recurse(x) for x in node.args))

            else:
                ExpressionError("unhandled syntax in expression: {0}".format(meta.dump_python_source(node).strip()))

        if returnlabel:
            return recurse(pyast, relations=True), label
        else:
            return recurse(pyast, relations=True)
        
    recognized = {abs: "abs", max: "max", min: "min"}

class _Placeholder(object):
    count = 0
    def __init__(self):
        self.index = _Placeholder.count
        _Placeholder.count += 1
    def __repr__(self):
        return "Placeholder({0})".format(self.index)
    def __hash__(self):
        return hash((_Placeholder, self.index))
    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.index == other.index
    def __ne__(self, other):
        return not self.__eq__(other)

def _recognize(module, pyname, name):
    if hasattr(module, pyname):
        Expr.recognized[getattr(module, pyname)] = name
    else:
        Expr.recognized[_Placeholder()] = name

_recognize(math, "acos", "acos")
_recognize(math, "acosh", "acosh")
_recognize(math, "asin", "asin")
_recognize(math, "asinh", "asinh")
_recognize(math, "atan2", "atan2")
_recognize(math, "atan", "atan")
_recognize(math, "atanh", "atanh")
_recognize(math, "ceil", "ceil")
_recognize(math, "copysign", "copysign")
_recognize(math, "cos", "cos")
_recognize(math, "cosh", "cosh")
_recognize(math, "degrees", "rad2deg")
_recognize(math, "erfc", "erfc")
_recognize(math, "erf", "erf")
_recognize(math, "exp", "exp")
_recognize(math, "expm1", "expm1")
_recognize(math, "factorial", "factorial")
_recognize(math, "floor", "floor")
_recognize(math, "fmod", "fmod")
_recognize(math, "gamma", "gamma")
_recognize(math, "hypot", "hypot")
_recognize(math, "isinf", "isinf")
_recognize(math, "isnan", "isnan")
_recognize(math, "lgamma", "lgamma")
_recognize(math, "log10", "log10")
_recognize(math, "log1p", "log1p")
_recognize(math, "log", "log")
_recognize(math, "pow", "pow")
_recognize(math, "radians", "deg2rad")
_recognize(math, "sinh", "sinh")
_recognize(math, "sin", "sin")
_recognize(math, "sqrt", "sqrt")
_recognize(math, "tanh", "tanh")
_recognize(math, "tan", "tan")
_recognize(math, "trunc", "trunc")

_recognize(numpy, "absolute", "abs")
_recognize(numpy, "arccos", "acos")
_recognize(numpy, "arccosh", "acosh")
_recognize(numpy, "arcsin", "asin")
_recognize(numpy, "arcsinh", "asinh")
_recognize(numpy, "arctan2", "atan2")
_recognize(numpy, "arctan", "atan")
_recognize(numpy, "arctanh", "atanh")
_recognize(numpy, "bitwise_xor", "xor")
_recognize(numpy, "ceil", "ceil")
_recognize(numpy, "conjugate", "conjugate")
_recognize(numpy, "copysign", "copysign")
_recognize(numpy, "cos", "cos")
_recognize(numpy, "cosh", "cosh")
_recognize(numpy, "deg2rad", "deg2rad")
_recognize(numpy, "degrees", "rad2deg")
_recognize(numpy, "exp2", "exp2")
_recognize(numpy, "exp", "exp")
_recognize(numpy, "expm1", "expm1")
_recognize(numpy, "floor", "floor")
_recognize(numpy, "fmod", "fmod")
_recognize(numpy, "heaviside", "heaviside")
_recognize(numpy, "hypot", "hypot")
_recognize(numpy, "isfinite", "isfinite")
_recognize(numpy, "isinf", "isinf")
_recognize(numpy, "isnan", "isnan")
_recognize(numpy, "left_shift", "left_shift")
_recognize(numpy, "log10", "log10")
_recognize(numpy, "log1p", "log1p")
_recognize(numpy, "log2", "log2")
_recognize(numpy, "logaddexp2", "logaddexp2")
_recognize(numpy, "logaddexp", "logaddexp")
_recognize(numpy, "log", "log")
_recognize(numpy, "maximum", "max")
_recognize(numpy, "minimum", "min")
_recognize(numpy, "power", "pow")
_recognize(numpy, "rad2deg", "rad2deg")
_recognize(numpy, "radians", "deg2rad")
_recognize(numpy, "remainder", "mod")
_recognize(numpy, "right_shift", "right_shift")
_recognize(numpy, "rint", "rint")
_recognize(numpy, "sign", "sign")
_recognize(numpy, "sinh", "sinh")
_recognize(numpy, "sin", "sin")
_recognize(numpy, "sqrt", "sqrt")
_recognize(numpy, "tanh", "tanh")
_recognize(numpy, "tan", "tan")
_recognize(numpy, "trunc", "trunc")

class Const(Expr):
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
        return self.__class__.__name__ == other.__class__.__name__ and self.value == other.value

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            if type(self.value).__name__ == type(other.value).__name__:
                return self.value < other.value
            else:
                return type(self.value).__name__ < type(other.value).__name__
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def rename(self, names):
        return self

class Name(Expr):
    def __init__(self, value):
        self.value = value

    def _reprargs(self):
        return (repr(self.value),)

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash((Name, self.value))

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self.value == other.value

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return self.value < other.value
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def rename(self, names):
        assert self in names
        return Name(names[self])

class Call(Expr):
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
        return self.__class__.__name__ == other.__class__.__name__ and self.fcn == other.fcn and self.args == other.args

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return (self.fcn, self.args) < (other.fcn, other.args)
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def rename(self, names):
        if self in names:
            return Name(names[self])
        else:
            return self.__class__(self.fcn, *(x.rename(names) for x in self.args))

class BinOp(Call):
    def __init__(self, fcn, left, right, op):
        super(BinOp, self).__init__(fcn, left, right)
        self.op = op

    def __str__(self):
        return (" " + self.op + " ").join(("(" + str(x) + ")") if isinstance(x, BinOp) else str(x) for x in self.args)

class RingAlgebra(Expr):
    def __init__(self, const, pos, neg):
        self.const = const
        self.pos = pos
        self.neg = neg

    def _reprargs(self):
        return (repr(self.const), repr(self.pos), repr(self.neg))

    def __hash__(self):
        return hash((self.__class__, self.const, self.pos, self.neg))

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self.const == other.const and self.pos == other.pos and self.neg == other.neg

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return (self.const, self.pos, self.neg) < (other.const, other.pos, other.neg)
        else:
            return self.__class__.__name__ < other.__class__.__name__

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

    def rename(self, names):
        if self in names:
            return Name(names[self])
        else:
            return self.__class__(self.const, tuple(x.rename(names) for x in self.pos), tuple(x.rename(names) for x in self.neg))

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
                out = self.subop(self.negateval(out.neg[0].const), out.neg[0].pos, out.neg[0].neg)

            if len(out.pos) == len(out.neg) == 0:
                return Const(out.const)
            elif out.const == out.identity and len(out.pos) == 1 and len(out.neg) == 0:
                return out.pos[0]

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
        return 1.0 / value            # only because arithmetic is a field, not a ring

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

### FIXME: NotImplementedError

# class BitAnd(RingAlgebraMultLike):
#     commutative = True
#     identity = numpy.uint64(-1)

#     @staticmethod
#     def negateval(value):
#         raise AssertionError(value)   # bitwise arithmetic really is a ring

#     @staticmethod
#     def calcval(left, right):
#         return numpy.uint64(left) & numpy.uint64(right)

# class BitOr(RingAlgebraAddLike):
#     subop = BitAnd
#     commutative = True
#     identity = numpy.uint64(0)

#     @staticmethod
#     def negateval(value):
#         return ~numpy.uint64(value)

#     @staticmethod
#     def isnegval(value):
#         return False

#     @staticmethod
#     def calcval(left, right):
#         return numpy.uint64(left) | numpy.uint64(right)

class Logical(object):
    commutative = True

    def __init__(self, *args):
        self.args = tuple(sorted(set(args)))

    def _reprargs(self):
        return tuple(repr(x) for x in self.args)

    def __hash__(self):
        return hash((self.__class__, self.args))

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self.args == other.args

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return self.args < other.args
        else:
            return self.__class__.__name__ < other.__class__.__name__

    @classmethod
    def normalform(cls, arg):
        if isinstance(arg, Name):
            return LogicalOr(LogicalAnd(Predicate(arg.value)))
        elif isinstance(arg, Predicate):
            return LogicalOr(LogicalAnd(arg))
        elif isinstance(arg, Relation):
            return LogicalOr(LogicalAnd(arg))
        elif isinstance(arg, LogicalAnd):
            return LogicalOr(arg)
        elif isinstance(arg, LogicalOr):
            return arg
        else:
            raise AssertionError(arg)

    @classmethod
    def negate(op, arg):
        logicalor = op.normalform(arg)
        upsidedown = [[relation.negate() for relation in logicaland.args] for logicaland in logicalor.args]
        return LogicalOr(*(LogicalAnd(*x) for x in itertools.product(*upsidedown)))

    def rename(self, names):
        if self in names:
            return Name(names[self])
        else:
            return self.__class__(*(x.rename(names) for x in self.args))

class LogicalAnd(Logical, RingAlgebraMultLike):
    @classmethod
    def combine(op, left, right):
        left, right = op.normalform(left), op.normalform(right)
        return LogicalOr(*(LogicalAnd(*(x.args + y.args)) for x, y in itertools.product(left.args, right.args)))

    def simplify(self):
        if len(self.args) == 0 or all(x == Const(True) for x in self.args):
            return Const(True)
        elif any(x == Const(False) for x in self.args):
            return Const(False)
        elif len(self.args) == 1:
            return self.args[0]
        else:
            return self

class LogicalOr(Logical, RingAlgebraAddLike):
    @classmethod
    def combine(op, left, right):
        left, right = op.normalform(left), op.normalform(right)
        return LogicalOr(*(left.args + right.args))

    def simplify(self):
        if len(self.args) == 0 or all(x == Const(False) for x in self.args):
            return Const(False)
        elif any(x == Const(True) for x in self.args):
            return Const(True)
        elif len(self.args) == 1:
            return self.args[0].simplify()
        else:
            return self

class Relation(Expr):
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
        return self.__class__.__name__ == other.__class__.__name__ and self.cmp == other.cmp and self.left == other.left and self.right == other.right

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return (self.cmp, self.left, self.right) < (other.cmp, other.left, other.right)
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def negate(self):
        if self.cmp == "==":
            return Relation("!=", self.left, self.right)
        elif self.cmp == "!=":
            return Relation("==", self.left, self.right)
        elif self.cmp == "<":
            return Relation("<=", self.right, self.left)
        elif self.cmp == "<=":
            return Relation("<", self.right, self.left)
        elif self.cmp == "in":
            return Relation("not in", self.left, self.right)
        elif self.cmp == "not in":
            return Relation("in", self.left, self.right)
        else:
            raise AssertionError(self.cmp)

class Predicate(Expr):
    def __init__(self, value, positive=True):
        self.value = value
        self.positive = positive

    def _reprargs(self):
        return (repr(self.value), repr(self.positive))

    def __str__(self):
        if self.positive:
            return self.value
        else:
            return "not " + self.value

    def __hash__(self):
        return hash((Predicate, self.value, self.positive))

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self.value == other.value and self.positive == other.positive

    def __lt__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return (self.value, self.positive) < (other.value, other.positive)
        else:
            return self.__class__.__name__ < other.__class__.__name__

    def negate(self):
        return Predicate(self.value, positive=not self.positive)

    def rename(self, names):
        assert self in names
        return Predicate(names[self])
