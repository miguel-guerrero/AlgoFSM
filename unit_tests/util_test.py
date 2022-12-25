import unittest
import sys
sys.path.append("..")
import algofsm.utils as utils


class Testing(unittest.TestCase):
    def test_one(self):
        self.assertTrue(utils.is_one(" 1"))
        self.assertTrue(utils.is_one("1'b1 "))
        self.assertTrue(utils.is_one(" 'b1 "))
        self.assertTrue(utils.is_one("  1'd1 "))
        self.assertTrue(utils.is_one("'d1"))
        self.assertTrue(utils.is_one("1'h1"))
        self.assertTrue(utils.is_one("'h1"))

    def test_not_one(self):
        self.assertFalse(utils.is_one("0"))
        self.assertFalse(utils.is_one("1'b0"))
        self.assertFalse(utils.is_one("'b0"))
        self.assertFalse(utils.is_one("1'd0"))
        self.assertFalse(utils.is_one("'d0"))
        self.assertFalse(utils.is_one("1'h0"))
        self.assertFalse(utils.is_one("'h0"))

    def test_not_one2(self):
        self.assertFalse(utils.is_one("x"))
        self.assertFalse(utils.is_one(" 0"))

    def test_zero(self):
        self.assertTrue(utils.is_zero(" 0"))
        self.assertTrue(utils.is_zero("1'b0 "))
        self.assertTrue(utils.is_zero(" 'b0 "))
        self.assertTrue(utils.is_zero("  1'd0 "))
        self.assertTrue(utils.is_zero("'d0"))
        self.assertTrue(utils.is_zero("1'h0"))
        self.assertTrue(utils.is_zero("'h0"))

    def test_not_zero(self):
        self.assertFalse(utils.is_zero("1"))
        self.assertFalse(utils.is_zero("1'b1"))
        self.assertFalse(utils.is_zero("'b1"))
        self.assertFalse(utils.is_zero("1'd1"))
        self.assertFalse(utils.is_zero("'d1"))
        self.assertFalse(utils.is_zero("1'h1"))
        self.assertFalse(utils.is_zero("'h1"))

    def test_not_zero2(self):
        self.assertFalse(utils.is_zero("x"))
        self.assertFalse(utils.is_zero(" 1"))

    def test_is_pure_negation(self):
        self.assertTrue(utils.is_pure_negation(" !(as bd cd) "))
        self.assertTrue(utils.is_pure_negation(" !  (as bd cd) "))
        self.assertTrue(utils.is_pure_negation("~(x)"))
        self.assertTrue(utils.is_pure_negation("~((x))"))

    def test_not_is_pure_negation(self):
        self.assertFalse(utils.is_pure_negation(" (as bd cd) "))
        self.assertFalse(utils.is_pure_negation("(x)"))
        self.assertFalse(utils.is_pure_negation("((x))"))

    def test_negate(self):
        self.assertEqual(utils.negate("!(as cd)"), "as cd")
        self.assertEqual(utils.negate("(as bd cd)"), "!((as bd cd))")

    def test_getbase(self):
        self.assertEqual(utils.get_base("asd/fgh.yxy"), "fgh.yxy")

    def test_indent(self):
        self.assertEqual(utils.indent(".", "asd\n  yzx"), ".asd\n.  yzx")

    def test_nonb_assign(self):
        self.assertTrue(utils. is_nonblocking_assign(" asd12_22 <= asdf "))
        self.assertFalse(utils. is_nonblocking_assign(" asd12_22 = asdf "))
        self.assertFalse(utils. is_nonblocking_assign(" if (a <-5) x=1 "))
