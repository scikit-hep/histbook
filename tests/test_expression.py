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

    def test_plusmult_field(self):
        expr = "(y + z) * 3"
        print
        print repr(Expr.parse(expr).expr)
        print str(Expr.parse(expr).expr)

    def test_unary_plusminus(self):
        self.assertEqual(Expr.parse("+x").expr, Name("x"))
        self.assertEqual(Expr.parse("-x").expr, PlusMinus(0, (), (TimesDiv(1, (Name("x"),), ()),)))
        self.assertEqual(Expr.parse("++x").expr, Name("x"))
        self.assertEqual(Expr.parse("--x").expr, PlusMinus(0, (TimesDiv(1, (Name("x"),), ()),), ()))
        self.assertEqual(Expr.parse("+++x").expr, Name("x"))
        self.assertEqual(Expr.parse("---x").expr, PlusMinus(0, (), (TimesDiv(1, (Name("x"),), ()),)))
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
        self.assertEqual(Expr.parse("x * y").expr, PlusMinus(0, (TimesDiv(1, (Name("x"), Name("y")), ()),), ()))






    def test_distributive(self):
        pass


        # q = Expr.parse("x - y").expr
        # print("")
        # print("")
        # print(repr(str(q)))
        # print(repr(q))
        # print("")

    # def test_binop(self):
    #     self.assertEqual(Expr.parse("x * y").expr, BinOp("*", Name("x"), Name("y")))
    #     self.assertEqual(Expr.parse("y * x").expr, BinOp("*", Name("x"), Name("y")))
    #     self.assertEqual(Expr.parse("x * 3").expr, BinOp("*", Const(3), Name("x")))
    #     self.assertEqual(Expr.parse("3 * x").expr, BinOp("*", Const(3), Name("x")))
    #     self.assertEqual(Expr.parse("x * y * z").expr, BinOp("*", Name("x"), Name("y"), Name("z")))
    #     self.assertEqual(Expr.parse("z * y * x").expr, BinOp("*", Name("x"), Name("y"), Name("z")))
    #     self.assertEqual(Expr.parse("x * (y * z)").expr, BinOp("*", Name("x"), Name("y"), Name("z")))
    #     self.assertEqual(Expr.parse("x * y * 3").expr, BinOp("*", Const(3), Name("x"), Name("y")))
    #     self.assertEqual(Expr.parse("3 * y * x").expr, BinOp("*", Const(3), Name("x"), Name("y")))
    #     self.assertEqual(Expr.parse("3 * (y * x)").expr, BinOp("*", Const(3), Name("x"), Name("y")))
    #     self.assertEqual(Expr.parse("x * (y * 3)").expr, BinOp("*", Const(3), Name("x"), Name("y")))
    #     self.assertEqual(Expr.parse("(x * y) * (z * 3)").expr, BinOp("*", Const(3), Name("x"), Name("y"), Name("z")))

