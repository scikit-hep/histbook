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

import unittest

from histbook.expr import *

class TestExpr(unittest.TestCase):
    def runTest(self):
        pass

    def test_const(self):
        self.assertEqual(Expr.parse("None"), Const(None))
        self.assertEqual(Expr.parse("True"), Const(True))
        self.assertEqual(Expr.parse("False"), Const(False))
        self.assertEqual(Expr.parse("1"), Const(1))
        self.assertEqual(Expr.parse("'hello'"), Const('hello'))
        self.assertEqual(Expr.parse("{}"), Const(set()))
        self.assertEqual(Expr.parse("{1, 2, 3}"), Const(set([1, 2, 3])))

    def test_name(self):
        self.assertEqual(Expr.parse("hello"), Name("hello"))

    def test_relation(self):
        self.assertEqual(Expr.parse("0 == x"), Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x == 0"), Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 != x"), Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x != 0"), Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 < x"), Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x < 0"), Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("0 <= x"), Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x <= 0"), Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("0 > x"), Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("x > 0"), Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 >= x"), Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("x >= 0"), Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x in {}"), Relation("in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("x in {1, 2, 3}"), Relation("in", Name("x"), Const(set([1, 2, 3]))))
        self.assertEqual(Expr.parse("x not in {}"), Relation("not in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("x not in {1, 2, 3}"), Relation("not in", Name("x"), Const(set([1, 2, 3]))))

    def test_unary_plusminus(self):
        self.assertEqual(Expr.parse("+x"), Name("x"))
        self.assertEqual(Expr.parse("-x"), TimesDiv(-1, (Name("x"),), ()))
        self.assertEqual(Expr.parse("++x"), Name("x"))
        self.assertEqual(Expr.parse("--x"), Name("x"))
        self.assertEqual(Expr.parse("+++x"), Name("x"))
        self.assertEqual(Expr.parse("---x"), TimesDiv(-1, (Name("x"),), ()))
        self.assertEqual(Expr.parse("-2"), Const(-2))
        self.assertEqual(Expr.parse("-(2 + 2)"), Const(-4))

    def test_plusminus(self):
        xterm = TimesDiv(1, (Name("x"),), ())
        yterm = TimesDiv(1, (Name("y"),), ())
        zterm = TimesDiv(1, (Name("z"),), ())

        self.assertEqual(Expr.parse("x + y"), PlusMinus(0, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("y + x"), PlusMinus(0, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("x + 3"), PlusMinus(3, (xterm,), ()))
        self.assertEqual(Expr.parse("3 + x"), PlusMinus(3, (xterm,), ()))
        self.assertEqual(Expr.parse("(x + y) + z"), PlusMinus(0, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("(z + y) + x"), PlusMinus(0, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("x + (y + z)"), PlusMinus(0, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("(x + y) + 3"), PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("(3 + y) + x"), PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("3 + (y + x)"), PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("x + (y + 3)"), PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("(x + y) + (z + 3)"), PlusMinus(3, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("-(x + y) + z"), PlusMinus(0, (zterm,), (xterm, yterm)))
        self.assertEqual(Expr.parse("-(z + y) + x"), PlusMinus(0, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("x + -(y + z)"), PlusMinus(0, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("-(x + y) + 3"), PlusMinus(3, (), (xterm, yterm)))
        self.assertEqual(Expr.parse("-(3 + y) + x"), PlusMinus(-3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("3 + -(y + x)"), PlusMinus(3, (), (xterm, yterm)))
        self.assertEqual(Expr.parse("x + -(y + 3)"), PlusMinus(-3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("-(x + y) + (z + 3)"), PlusMinus(3, (zterm,), (xterm, yterm)))
        self.assertEqual(Expr.parse("(x + y) + -(z + 3)"), PlusMinus(-3, (xterm, yterm), (zterm,)))

        self.assertEqual(Expr.parse("x - y"), PlusMinus(0, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("y - x"), PlusMinus(0, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("x - 3"), PlusMinus(-3, (xterm,), ()))
        self.assertEqual(Expr.parse("3 - x"), PlusMinus(3, (), (xterm,)))
        self.assertEqual(Expr.parse("(x - y) - z"), PlusMinus(0, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("(z - y) - x"), PlusMinus(0, (zterm,), (xterm, yterm)))
        self.assertEqual(Expr.parse("x - (y - z)"), PlusMinus(0, (xterm, zterm), (yterm,)))
        self.assertEqual(Expr.parse("(x - y) - 3"), PlusMinus(-3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("(3 - y) - x"), PlusMinus(3, (), (xterm, yterm)))
        self.assertEqual(Expr.parse("3 - (y - x)"), PlusMinus(3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("x - (y - 3)"), PlusMinus(3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("(x - y) - (z - 3)"), PlusMinus(3, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("-(x - y) - z"), PlusMinus(0, (yterm,), (xterm, zterm)))
        self.assertEqual(Expr.parse("-(z - y) - x"), PlusMinus(0, (yterm,), (xterm, zterm)))
        self.assertEqual(Expr.parse("x - -(y - z)"), PlusMinus(0, (xterm, yterm), (zterm,)))
        self.assertEqual(Expr.parse("-(x - y) - 3"), PlusMinus(-3, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("-(3 - y) - x"), PlusMinus(-3, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("3 - -(y - x)"), PlusMinus(3, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("x - -(y - 3)"), PlusMinus(-3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("-(x - y) - (z - 3)"), PlusMinus(3, (yterm,), (xterm, zterm)))
        self.assertEqual(Expr.parse("(x - y) - -(z - 3)"), PlusMinus(-3, (xterm, zterm), (yterm,)))

    def test_timesdiv(self):
        self.assertEqual(Expr.parse("x * y"), TimesDiv(1, (Name("x"), Name("y")), ()))
        self.assertEqual(Expr.parse("y * x"), TimesDiv(1, (Name("x"), Name("y")), ()))
        self.assertEqual(Expr.parse("3 * x"), TimesDiv(3, (Name("x"),), ()))
        self.assertEqual(Expr.parse("x * 3"), TimesDiv(3, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(x * y) * z"), TimesDiv(1, (Name("x"), Name("y"), Name("z")), ()))
        self.assertEqual(Expr.parse("x * (y * z)"), TimesDiv(1, (Name("x"), Name("y"), Name("z")), ()))
        self.assertEqual(Expr.parse("(x * 3) * y"), TimesDiv(3, (Name("x"), Name("y")), ()))
        self.assertEqual(Expr.parse("x * (3 * y)"), TimesDiv(3, (Name("x"), Name("y")), ()))

        self.assertEqual(Expr.parse("x / y"), TimesDiv(1, (Name("x"),), (Name("y"),)))
        self.assertEqual(Expr.parse("y / x"), TimesDiv(1, (Name("y"),), (Name("x"),)))
        self.assertEqual(Expr.parse("3 / x"), TimesDiv(3, (), (Name("x"),)))
        self.assertEqual(Expr.parse("x / 3"), TimesDiv(1.0/3.0, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(x / y) / z"), TimesDiv(1, (Name("x"),), (Name("y"), Name("z"))))
        self.assertEqual(Expr.parse("x / (y / z)"), TimesDiv(1, (Name("x"), Name("z")), (Name("y"),)))
        self.assertEqual(Expr.parse("(x / 3) / y"), TimesDiv(1.0/3.0, (Name("x"),), (Name("y"),)))
        self.assertEqual(Expr.parse("x / (3 / y)"), TimesDiv(1.0/3.0, (Name("x"), Name("y")), ()))

    def test_distributive(self):
        self.assertEqual(Expr.parse("a * (x + y)"), PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(1, (Name("a"), Name("y")), ())), ()))
        self.assertEqual(Expr.parse("(x + y) * a"), PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(1, (Name("a"), Name("y")), ())), ()))
        self.assertEqual(Expr.parse("a * (x + 3)"), PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(3, (Name("a"),), ())), ()))
        self.assertEqual(Expr.parse("(x + 3) * a"), PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(3, (Name("a"),), ())), ()))

        self.assertEqual(Expr.parse("a * (x + y) + a*x + a*y"), PlusMinus(0, (TimesDiv(2, (Name("a"), Name("x")), ()), TimesDiv(2, (Name("a"), Name("y")), ())), ()))
        self.assertEqual(Expr.parse("a * (x + y) - 2*a*x"), PlusMinus(0, (TimesDiv(1, (Name("a"), Name("y")), ()),), (TimesDiv(1, (Name("a"), Name("x")), ()),)))

        # simplifies (because it stays within the ring)
        self.assertEqual(Expr.parse("(x + y) / a"), PlusMinus(0, (TimesDiv(1, (Name("x"),), (Name("a"),)), TimesDiv(1, (Name("y"),), (Name("a"),))), ()))
        self.assertEqual(Expr.parse("(x + 3) / a"), PlusMinus(0, (TimesDiv(1, (Name("x"),), (Name("a"),)), TimesDiv(3, (), (Name("a"),))), ()))

        # does not simplify (because division of a sum puts it into the field)
        self.assertEqual(Expr.parse("a / (x + y)"), TimesDiv(1, (Name("a"),), (PlusMinus(0, (TimesDiv(1, (Name("x"),), ()), TimesDiv(1, (Name("y"),), ())), ()),)))
        self.assertEqual(Expr.parse("a / (x + 3)"), TimesDiv(1, (Name("a"),), (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()),)))

        self.assertEqual(Expr.parse("(2 - 2 - x) / a"), TimesDiv(-1, (Name("x"),), (Name("a"),)))
        self.assertEqual(Expr.parse("a / (2 - 2 - x)"), TimesDiv(-1, (Name("a"),), (Name("x"),)))

    def test_cancellation(self):
        self.assertEqual(Expr.parse("x - x"), Const(0))
        self.assertEqual(Expr.parse("x + x - 2*x"), Const(0))
        self.assertEqual(Expr.parse("a * (x + y) - a*x - a*y"), Const(0))
        self.assertEqual(Expr.parse("a * (x + y) - a*x"), TimesDiv(1, (Name("a"), Name("y")), ()))
        self.assertEqual(Expr.parse("a * (x + y)/y - a*x/y"), Name("a"))

        self.assertEqual(Expr.parse("(x + x*x)/x - x"), Const(1))
        self.assertEqual(Expr.parse("(x + x*x)/x - 1"), Name("x"))
        self.assertEqual(Expr.parse("x - (x + x*x)/x"), Const(-1))
        self.assertEqual(Expr.parse("1 - (x + x*x)/x"), TimesDiv(-1, (Name("x"),), ()))

    def test_lowintpower(self):
        self.assertEqual(Expr.parse("x**1"), Name("x"))
        self.assertEqual(Expr.parse("x**2"), TimesDiv(1, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("x**3"), TimesDiv(1, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("x**4"), TimesDiv(1, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-x)**1"), TimesDiv(-1, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(-x)**2"), TimesDiv(1, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-x)**3"), TimesDiv(-1, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-x)**4"), TimesDiv(1, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(2*x)**1"), TimesDiv(2, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(2*x)**2"), TimesDiv(4, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(2*x)**3"), TimesDiv(8, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(2*x)**4"), TimesDiv(16, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-2*x)**1"), TimesDiv(-2, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(-2*x)**2"), TimesDiv(4, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-2*x)**3"), TimesDiv(-8, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-2*x)**4"), TimesDiv(16, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(x + 3)**1"), PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()))
        self.assertEqual(Expr.parse("(x + 3)**2"), TimesDiv(1, (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()), PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ())), ()))

        self.assertEqual(Expr.parse("x**-1"), TimesDiv(1, (), (Name("x"),)))
        self.assertEqual(Expr.parse("x**-2"), TimesDiv(1, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("x**-3"), TimesDiv(1, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("x**-4"), TimesDiv(1, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-x)**-1"), TimesDiv(-1, (), (Name("x"),)))
        self.assertEqual(Expr.parse("(-x)**-2"), TimesDiv(1, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-x)**-3"), TimesDiv(-1, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-x)**-4"), TimesDiv(1, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(2*x)**-1"), TimesDiv(1.0/2.0, (), (Name("x"),)))
        self.assertEqual(Expr.parse("(2*x)**-2"), TimesDiv(1.0/4.0, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(2*x)**-3"), TimesDiv(1.0/8.0, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(2*x)**-4"), TimesDiv(1.0/16.0, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-2*x)**-1"), TimesDiv(-1.0/2.0, (), (Name("x"),)))
        self.assertEqual(Expr.parse("(-2*x)**-2"), TimesDiv(1.0/4.0, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-2*x)**-3"), TimesDiv(-1.0/8.0, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-2*x)**-4"), TimesDiv(1.0/16.0, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(x + 3)**-1"), TimesDiv(1, (), (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()),)))
        self.assertEqual(Expr.parse("(x + 3)**-2"), TimesDiv(1, (), (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()), PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()))))

    def test_binop(self):
        pass

    def test_logicalnot(self):
        self.assertEqual(Expr.parse("not x == 0"), Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("not x != 0"), Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("not x < 0"), Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("not x <= 0"), Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("not x > 0"), Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("not x >= 0"), Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("not x in {}"), Relation("not in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("not x not in {}"), Relation("in", Name("x"), Const(set())))

        self.assertEqual(Expr.parse("not p"), Predicate("p", positive=False))

    def test_logicals(self):
        self.assertEqual(Expr.parse("a and b"), LogicalAnd(Predicate("a"), Predicate("b")))
        self.assertEqual(Expr.parse("a or b"), LogicalOr(LogicalAnd(Predicate("a")), LogicalAnd(Predicate("b"))))
        self.assertEqual(Expr.parse("(a and b) or (c and d)"), LogicalOr(LogicalAnd(Predicate("a"), Predicate("b")), LogicalAnd(Predicate("c"), Predicate("d"))))
        self.assertEqual(Expr.parse("(a or b) and (c or d)"), LogicalOr(LogicalAnd(Predicate("a"), Predicate("c")), LogicalAnd(Predicate("a"), Predicate("d")), LogicalAnd(Predicate("b"), Predicate("c")), LogicalAnd(Predicate("b"), Predicate("d"))))
        self.assertEqual(Expr.parse("(a or b) and c"), LogicalOr(LogicalAnd(Predicate("a"), Predicate("c")), LogicalAnd(Predicate("b"), Predicate("c"))))
        self.assertEqual(Expr.parse("c and (a or b)"), LogicalOr(LogicalAnd(Predicate("a"), Predicate("c")), LogicalAnd(Predicate("b"), Predicate("c"))))
        self.assertEqual(Expr.parse("c or (a or b)"), LogicalOr(LogicalAnd(Predicate("a")), LogicalAnd(Predicate("b")), LogicalAnd(Predicate("c"))))

    def test_logical_negations(self):
        self.assertEqual(Expr.parse("not (a and b)"), LogicalOr(LogicalAnd(Predicate("a", False)), LogicalAnd(Predicate("b", False))))
        self.assertEqual(Expr.parse("not (a or b)"), LogicalAnd(Predicate("a", False), Predicate("b", False)))
        self.assertEqual(Expr.parse("not (x == 123 and x == 999)"), LogicalOr(LogicalAnd(Relation("!=", Const(123), Name("x"))), LogicalAnd(Relation("!=", Const(999), Name("x")))))
        self.assertEqual(Expr.parse("not (x == 123 or x == 999)"), LogicalAnd(Relation("!=", Const(123), Name("x")), Relation("!=", Const(999), Name("x"))))

    def test_function(self):
        self.assertEqual(Expr.parse("sqrt(x)"), Call("sqrt", Name("x")))
