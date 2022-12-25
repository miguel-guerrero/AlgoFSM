# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
import re
import sys


# --------------------------------------------------------------------
# build up a text line by line
# --------------------------------------------------------------------
class Dumper:
    def __init__(self):
        self.out = []

    def dump(self, *args):
        self.out.append(" ".join(args))

    def dump_nonl(self, *args):
        self.out[-1] += " ".join(args)

    def val(self):
        return "\n".join(self.out)


# --------------------------------------------------------------------
# unified way to give errors etc
# --------------------------------------------------------------------
def error(*args):
    print("ERROR:", *args, file=sys.stderr)
    sys.exit(1)


def warning(*args):
    print("WARNING:", *args, file=sys.stderr)


def debug(*args):
    print("DEBUG:", *args, file=sys.stderr)


# --------------------------------------------------------------------
# Verilog misc routines
# --------------------------------------------------------------------
def _unpack_clk_name(clk):
    """
    given the clock name with optional ~ prefix for negedge sensitive
    unpack clock name and edge
    """
    clk = clk.strip()

    falling_edge = clk[0] == "~"
    if falling_edge:
        clk = clk[1:]

    return clk, falling_edge


def _unpack_rst_name(rst):
    """
    given the reset name with optional ~ prefix (for low true) and
    : suffix (for syncrhonous), extract these attributes and name
    """
    rst = rst.strip()

    low_act_rst = rst[0] == "~"
    if low_act_rst:
        rst = rst[1:]

    sync_rst = rst[-1] == ":"
    if sync_rst:
        rst = rst[:-1]

    return rst, low_act_rst, sync_rst


def get_ticks(args):
    """get sensitivity list to clock and reset"""

    clk, falling_edge = _unpack_clk_name(args.clk)
    rst, low_act_rst, sync_rst = _unpack_rst_name(args.rst)

    tick = "@("
    tick += "negedge " if falling_edge else "posedge "
    tick += clk
    tick_no_rst = tick + ")"

    if not sync_rst:
        tick += " or "
        tick += "negedge " if low_act_rst else "posedge "
        tick += rst
    tick += ")"
    return tick, tick_no_rst


def get_resets(args):
    """get equation that indicates we are in reset condition"""
    rst, low_act_rst, _ = _unpack_rst_name(args.rst)
    if low_act_rst:
        return (f"!{rst}", rst)
    else:
        return (rst, f"!{rst}")


def is_one(expr):
    """return True if the expressions for sure evals to 1, else False"""
    return (
        re.match(r"\s*1\s*$", expr)
        or re.match(r"\s*1?'[bdh]1\s*$", expr)
    ) is not None


def is_zero(expr):
    """return True if the expressions for sure evals to 0, else False"""
    return (
        re.match(r"\s*0\s*$", expr)
        or re.match(r"\s*1?'[bdh]0\s*$", expr)
    ) is not None


def is_pure_negation(expr):
    expr = expr.strip()
    m = re.match(r"^[!\~]\s*\(.*\)$", expr)
    return m is not None


def negate(expr):
    if is_pure_negation(expr):
        expr = expr.strip()
        m = re.match(r"^[!\~]\s*\((.*)\)$", expr)
        return m.group(1)
    else:
        return "!(" + expr + ")"


def is_only_stay(stay_txt, blk):
    lines = [line.strip() for line in blk.split("\n")]
    lines = [line for line in lines if line != ""]
    return len(lines) == 1 and lines[0] == stay_txt


def is_nonblocking_assign(stm):
    return re.match(r"\s*(\w+)\s*\<\=\s*(.*)$", stm) is not None


# --------------------------------------------------------------------
# General misc routines
# --------------------------------------------------------------------
def get_base(path):
    return path[path.rindex("/") + 1:]


def indent(ind, txt):
    txt = txt.rstrip()
    return "\n".join(ind + line for line in txt.split("\n"))
