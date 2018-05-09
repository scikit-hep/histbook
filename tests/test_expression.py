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

import unittest

from histbook.expression import *

class TestExpression(unittest.TestCase):
    def runTest(self):
        pass

    def test_const(self):
        self.assertEqual(Expr.parse("None").expr, Const(None))
        self.assertEqual(Expr.parse("True").expr, Const(True))
        self.assertEqual(Expr.parse("False").expr, Const(False))
        self.assertEqual(Expr.parse("1").expr, Const(1))
        self.assertEqual(Expr.parse("'hello'").expr, Const('hello'))
        self.assertEqual(Expr.parse("{}").expr, Const(set()))
        self.assertEqual(Expr.parse("{1, 2, 3}").expr, Const({1, 2, 3}))

    def test_name(self):
        self.assertEqual(Expr.parse("hello").names, ["hello"])
        self.assertEqual(Expr.parse("hello").expr, Name("hello"))

    def test_relation(self):
        self.assertEqual(Expr.parse("0 == x").expr, Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x == 0").expr, Relation("==", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 != x").expr, Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x != 0").expr, Relation("!=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 < x").expr, Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x < 0").expr, Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("0 <= x").expr, Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x <= 0").expr, Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("0 > x").expr, Relation("<", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("x > 0").expr, Relation("<", Const(0), Name("x")))
        self.assertEqual(Expr.parse("0 >= x").expr, Relation("<=", Name("x"), Const(0)))
        self.assertEqual(Expr.parse("x >= 0").expr, Relation("<=", Const(0), Name("x")))
        self.assertEqual(Expr.parse("x in {}").expr, Relation("in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("x in {1, 2, 3}").expr, Relation("in", Name("x"), Const({1, 2, 3})))
        self.assertEqual(Expr.parse("x not in {}").expr, Relation("not in", Name("x"), Const(set())))
        self.assertEqual(Expr.parse("x not in {1, 2, 3}").expr, Relation("not in", Name("x"), Const({1, 2, 3})))

    def test_interval(self):
        self.assertEqual(Expr.parse("0 <= x < 3").expr, Interval(Name("x"), Const(0), Const(3), lowclosed=True))
        self.assertEqual(Expr.parse("0 < x <= 3").expr, Interval(Name("x"), Const(0), Const(3), lowclosed=False))
        self.assertEqual(Expr.parse("3 > x >= 0").expr, Interval(Name("x"), Const(0), Const(3), lowclosed=True))
        self.assertEqual(Expr.parse("3 >= x > 0").expr, Interval(Name("x"), Const(0), Const(3), lowclosed=False))

    def test_unary_plusminus(self):
        self.assertEqual(Expr.parse("+x").expr, Name("x"))
        self.assertEqual(Expr.parse("-x").expr, TimesDiv(-1, (Name("x"),), ()))
        self.assertEqual(Expr.parse("++x").expr, Name("x"))
        self.assertEqual(Expr.parse("--x").expr, Name("x"))
        self.assertEqual(Expr.parse("+++x").expr, Name("x"))
        self.assertEqual(Expr.parse("---x").expr, TimesDiv(-1, (Name("x"),), ()))
        self.assertEqual(Expr.parse("-2").expr, Const(-2))
        self.assertEqual(Expr.parse("-(2 + 2)").expr, Const(-4))

    def test_plusminus(self):
        xterm = TimesDiv(1, (Name("x"),), ())
        yterm = TimesDiv(1, (Name("y"),), ())
        zterm = TimesDiv(1, (Name("z"),), ())

        self.assertEqual(Expr.parse("x + y").expr, PlusMinus(0, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("y + x").expr, PlusMinus(0, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("x + 3").expr, PlusMinus(3, (xterm,), ()))
        self.assertEqual(Expr.parse("3 + x").expr, PlusMinus(3, (xterm,), ()))
        self.assertEqual(Expr.parse("(x + y) + z").expr, PlusMinus(0, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("(z + y) + x").expr, PlusMinus(0, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("x + (y + z)").expr, PlusMinus(0, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("(x + y) + 3").expr, PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("(3 + y) + x").expr, PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("3 + (y + x)").expr, PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("x + (y + 3)").expr, PlusMinus(3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("(x + y) + (z + 3)").expr, PlusMinus(3, (xterm, yterm, zterm), ()))
        self.assertEqual(Expr.parse("-(x + y) + z").expr, PlusMinus(0, (zterm,), (xterm, yterm)))
        self.assertEqual(Expr.parse("-(z + y) + x").expr, PlusMinus(0, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("x + -(y + z)").expr, PlusMinus(0, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("-(x + y) + 3").expr, PlusMinus(3, (), (xterm, yterm)))
        self.assertEqual(Expr.parse("-(3 + y) + x").expr, PlusMinus(-3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("3 + -(y + x)").expr, PlusMinus(3, (), (xterm, yterm)))
        self.assertEqual(Expr.parse("x + -(y + 3)").expr, PlusMinus(-3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("-(x + y) + (z + 3)").expr, PlusMinus(3, (zterm,), (xterm, yterm)))
        self.assertEqual(Expr.parse("(x + y) + -(z + 3)").expr, PlusMinus(-3, (xterm, yterm), (zterm,)))

        self.assertEqual(Expr.parse("x - y").expr, PlusMinus(0, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("y - x").expr, PlusMinus(0, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("x - 3").expr, PlusMinus(-3, (xterm,), ()))
        self.assertEqual(Expr.parse("3 - x").expr, PlusMinus(3, (), (xterm,)))
        self.assertEqual(Expr.parse("(x - y) - z").expr, PlusMinus(0, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("(z - y) - x").expr, PlusMinus(0, (zterm,), (xterm, yterm)))
        self.assertEqual(Expr.parse("x - (y - z)").expr, PlusMinus(0, (xterm, zterm), (yterm,)))
        self.assertEqual(Expr.parse("(x - y) - 3").expr, PlusMinus(-3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("(3 - y) - x").expr, PlusMinus(3, (), (xterm, yterm)))
        self.assertEqual(Expr.parse("3 - (y - x)").expr, PlusMinus(3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("x - (y - 3)").expr, PlusMinus(3, (xterm,), (yterm,)))
        self.assertEqual(Expr.parse("(x - y) - (z - 3)").expr, PlusMinus(3, (xterm,), (yterm, zterm)))
        self.assertEqual(Expr.parse("-(x - y) - z").expr, PlusMinus(0, (yterm,), (xterm, zterm)))
        self.assertEqual(Expr.parse("-(z - y) - x").expr, PlusMinus(0, (yterm,), (xterm, zterm)))
        self.assertEqual(Expr.parse("x - -(y - z)").expr, PlusMinus(0, (xterm, yterm), (zterm,)))
        self.assertEqual(Expr.parse("-(x - y) - 3").expr, PlusMinus(-3, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("-(3 - y) - x").expr, PlusMinus(-3, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("3 - -(y - x)").expr, PlusMinus(3, (yterm,), (xterm,)))
        self.assertEqual(Expr.parse("x - -(y - 3)").expr, PlusMinus(-3, (xterm, yterm), ()))
        self.assertEqual(Expr.parse("-(x - y) - (z - 3)").expr, PlusMinus(3, (yterm,), (xterm, zterm)))
        self.assertEqual(Expr.parse("(x - y) - -(z - 3)").expr, PlusMinus(-3, (xterm, zterm), (yterm,)))

    def test_timesdiv(self):
        self.assertEqual(Expr.parse("x * y").expr, TimesDiv(1, (Name("x"), Name("y")), ()))
        self.assertEqual(Expr.parse("y * x").expr, TimesDiv(1, (Name("x"), Name("y")), ()))
        self.assertEqual(Expr.parse("3 * x").expr, TimesDiv(3, (Name("x"),), ()))
        self.assertEqual(Expr.parse("x * 3").expr, TimesDiv(3, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(x * y) * z").expr, TimesDiv(1, (Name("x"), Name("y"), Name("z")), ()))
        self.assertEqual(Expr.parse("x * (y * z)").expr, TimesDiv(1, (Name("x"), Name("y"), Name("z")), ()))
        self.assertEqual(Expr.parse("(x * 3) * y").expr, TimesDiv(3, (Name("x"), Name("y")), ()))
        self.assertEqual(Expr.parse("x * (3 * y)").expr, TimesDiv(3, (Name("x"), Name("y")), ()))

        self.assertEqual(Expr.parse("x / y").expr, TimesDiv(1, (Name("x"),), (Name("y"),)))
        self.assertEqual(Expr.parse("y / x").expr, TimesDiv(1, (Name("y"),), (Name("x"),)))
        self.assertEqual(Expr.parse("3 / x").expr, TimesDiv(3, (), (Name("x"),)))
        self.assertEqual(Expr.parse("x / 3").expr, TimesDiv(1.0/3.0, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(x / y) / z").expr, TimesDiv(1, (Name("x"),), (Name("y"), Name("z"))))
        self.assertEqual(Expr.parse("x / (y / z)").expr, TimesDiv(1, (Name("x"), Name("z")), (Name("y"),)))
        self.assertEqual(Expr.parse("(x / 3) / y").expr, TimesDiv(1.0/3.0, (Name("x"),), (Name("y"),)))
        self.assertEqual(Expr.parse("x / (3 / y)").expr, TimesDiv(1.0/3.0, (Name("x"), Name("y")), ()))

    def test_distributive(self):
        self.assertEqual(Expr.parse("a * (x + y)").expr, PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(1, (Name("a"), Name("y")), ())), ()))
        self.assertEqual(Expr.parse("(x + y) * a").expr, PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(1, (Name("a"), Name("y")), ())), ()))
        self.assertEqual(Expr.parse("a * (x + 3)").expr, PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(3, (Name("a"),), ())), ()))
        self.assertEqual(Expr.parse("(x + 3) * a").expr, PlusMinus(0, (TimesDiv(1, (Name("a"), Name("x")), ()), TimesDiv(3, (Name("a"),), ())), ()))

        self.assertEqual(Expr.parse("a * (x + y) + a*x + a*y").expr, PlusMinus(0, (TimesDiv(2, (Name("a"), Name("x")), ()), TimesDiv(2, (Name("a"), Name("y")), ())), ()))
        self.assertEqual(Expr.parse("a * (x + y) - 2*a*x").expr, PlusMinus(0, (TimesDiv(1, (Name("a"), Name("y")), ()),), (TimesDiv(1, (Name("a"), Name("x")), ()),)))

        # simplifies (because it stays within the ring)
        self.assertEqual(Expr.parse("(x + y) / a").expr, PlusMinus(0, (TimesDiv(1, (Name("x"),), (Name("a"),)), TimesDiv(1, (Name("y"),), (Name("a"),))), ()))
        self.assertEqual(Expr.parse("(x + 3) / a").expr, PlusMinus(0, (TimesDiv(1, (Name("x"),), (Name("a"),)), TimesDiv(3, (), (Name("a"),))), ()))

        # does not simplify (because division of a sum puts it into the field)
        self.assertEqual(Expr.parse("a / (x + y)").expr, TimesDiv(1, (Name("a"),), (PlusMinus(0, (TimesDiv(1, (Name("x"),), ()), TimesDiv(1, (Name("y"),), ())), ()),)))
        self.assertEqual(Expr.parse("a / (x + 3)").expr, TimesDiv(1, (Name("a"),), (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()),)))

        self.assertEqual(Expr.parse("(2 - 2 - x) / a").expr, TimesDiv(-1, (Name("x"),), (Name("a"),)))
        self.assertEqual(Expr.parse("a / (2 - 2 - x)").expr, TimesDiv(-1, (Name("a"),), (Name("x"),)))

    def test_cancellation(self):
        self.assertEqual(Expr.parse("x - x").expr, Const(0))
        self.assertEqual(Expr.parse("x + x - 2*x").expr, Const(0))
        self.assertEqual(Expr.parse("a * (x + y) - a*x - a*y").expr, Const(0))
        self.assertEqual(Expr.parse("a * (x + y) - a*x").expr, TimesDiv(1, (Name("a"), Name("y")), ()))
        self.assertEqual(Expr.parse("a * (x + y)/y - a*x/y").expr, Name("a"))

        self.assertEqual(Expr.parse("(x + x*x)/x - x").expr, Const(1))
        self.assertEqual(Expr.parse("(x + x*x)/x - 1").expr, Name("x"))
        self.assertEqual(Expr.parse("x - (x + x*x)/x").expr, Const(-1))
        self.assertEqual(Expr.parse("1 - (x + x*x)/x").expr, TimesDiv(-1, (Name("x"),), ()))

    def test_lowintpower(self):
        self.assertEqual(Expr.parse("x**1").expr, Name("x"))
        self.assertEqual(Expr.parse("x**2").expr, TimesDiv(1, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("x**3").expr, TimesDiv(1, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("x**4").expr, TimesDiv(1, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-x)**1").expr, TimesDiv(-1, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(-x)**2").expr, TimesDiv(1, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-x)**3").expr, TimesDiv(-1, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-x)**4").expr, TimesDiv(1, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(2*x)**1").expr, TimesDiv(2, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(2*x)**2").expr, TimesDiv(4, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(2*x)**3").expr, TimesDiv(8, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(2*x)**4").expr, TimesDiv(16, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-2*x)**1").expr, TimesDiv(-2, (Name("x"),), ()))
        self.assertEqual(Expr.parse("(-2*x)**2").expr, TimesDiv(4, (Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-2*x)**3").expr, TimesDiv(-8, (Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(-2*x)**4").expr, TimesDiv(16, (Name("x"), Name("x"), Name("x"), Name("x")), ()))
        self.assertEqual(Expr.parse("(x + 3)**1").expr, PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()))
        self.assertEqual(Expr.parse("(x + 3)**2").expr, TimesDiv(1, (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()), PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ())), ()))

        self.assertEqual(Expr.parse("x**-1").expr, TimesDiv(1, (), (Name("x"),)))
        self.assertEqual(Expr.parse("x**-2").expr, TimesDiv(1, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("x**-3").expr, TimesDiv(1, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("x**-4").expr, TimesDiv(1, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-x)**-1").expr, TimesDiv(-1, (), (Name("x"),)))
        self.assertEqual(Expr.parse("(-x)**-2").expr, TimesDiv(1, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-x)**-3").expr, TimesDiv(-1, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-x)**-4").expr, TimesDiv(1, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(2*x)**-1").expr, TimesDiv(1.0/2.0, (), (Name("x"),)))
        self.assertEqual(Expr.parse("(2*x)**-2").expr, TimesDiv(1.0/4.0, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(2*x)**-3").expr, TimesDiv(1.0/8.0, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(2*x)**-4").expr, TimesDiv(1.0/16.0, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-2*x)**-1").expr, TimesDiv(-1.0/2.0, (), (Name("x"),)))
        self.assertEqual(Expr.parse("(-2*x)**-2").expr, TimesDiv(1.0/4.0, (), (Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-2*x)**-3").expr, TimesDiv(-1.0/8.0, (), (Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(-2*x)**-4").expr, TimesDiv(1.0/16.0, (), (Name("x"), Name("x"), Name("x"), Name("x"))))
        self.assertEqual(Expr.parse("(x + 3)**-1").expr, TimesDiv(1, (), (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()),)))
        self.assertEqual(Expr.parse("(x + 3)**-2").expr, TimesDiv(1, (), (PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()), PlusMinus(3, (TimesDiv(1, (Name("x"),), ()),), ()))))

    def test_binop(self):
        pass

    def test_logicalnot(self):
        self.assertEqual(Expr.parse("not x == 0").expr, LogicalOr(LogicalAnd(Relation("!=", Const(0), Name("x")))))
        self.assertEqual(Expr.parse("not x != 0").expr, LogicalOr(LogicalAnd(Relation("==", Const(0), Name("x")))))
        self.assertEqual(Expr.parse("not x < 0").expr, LogicalOr(LogicalAnd(Relation("<=", Const(0), Name("x")))))
        self.assertEqual(Expr.parse("not x <= 0").expr, LogicalOr(LogicalAnd(Relation("<", Const(0), Name("x")))))
        self.assertEqual(Expr.parse("not x > 0").expr, LogicalOr(LogicalAnd(Relation("<=", Name("x"), Const(0)))))
        self.assertEqual(Expr.parse("not x >= 0").expr, LogicalOr(LogicalAnd(Relation("<", Name("x"), Const(0)))))
        self.assertEqual(Expr.parse("not x in {}").expr, LogicalOr(LogicalAnd(Relation("not in", Name("x"), Const(set())))))
        self.assertEqual(Expr.parse("not x not in {}").expr, LogicalOr(LogicalAnd(Relation("in", Name("x"), Const(set())))))

        self.assertEqual(Expr.parse("not p").expr, Predicate("p", positive=False))

    def test_logicals(self):
        self.assertEqual(Expr.parse("a and b").expr, LogicalOr(LogicalAnd(Predicate("a"), Predicate("b"))))
        self.assertEqual(Expr.parse("a or b").expr, LogicalOr(LogicalAnd(Predicate("a")), LogicalAnd(Predicate("b"))))
        self.assertEqual(Expr.parse("(a and b) or (c and d)").expr, LogicalOr(LogicalAnd(Predicate("a"), Predicate("b")), LogicalAnd(Predicate("c"), Predicate("d"))))
        self.assertEqual(Expr.parse("(a or b) and (c or d)").expr, LogicalOr(LogicalAnd(Predicate("a"), Predicate("c")), LogicalAnd(Predicate("a"), Predicate("d")), LogicalAnd(Predicate("b"), Predicate("c")), LogicalAnd(Predicate("b"), Predicate("d"))))
        self.assertEqual(Expr.parse("(a or b) and c").expr, LogicalOr(LogicalAnd(Predicate("a"), Predicate("c")), LogicalAnd(Predicate("b"), Predicate("c"))))
        self.assertEqual(Expr.parse("c and (a or b)").expr, LogicalOr(LogicalAnd(Predicate("a"), Predicate("c")), LogicalAnd(Predicate("b"), Predicate("c"))))
        self.assertEqual(Expr.parse("c or (a or b)").expr, LogicalOr(LogicalAnd(Predicate("a")), LogicalAnd(Predicate("b")), LogicalAnd(Predicate("c"))))

    def test_logical_negations(self):
        self.assertEqual(Expr.parse("not (a and b)").expr, LogicalOr(LogicalAnd(Predicate("a", False)), LogicalAnd(Predicate("b", False))))
        self.assertEqual(Expr.parse("not (a or b)").expr, LogicalOr(LogicalAnd(Predicate("a", False), Predicate("b", False))))
        self.assertEqual(Expr.parse("not (x == 123 and x == 999)").expr, LogicalOr(LogicalAnd(Relation("!=", Const(123), Name("x"))), LogicalAnd(Relation("!=", Const(999), Name("x")))))
        self.assertEqual(Expr.parse("not (x == 123 or x == 999)").expr, LogicalOr(LogicalAnd(Relation("!=", Const(123), Name("x")), Relation("!=", Const(999), Name("x")))))

