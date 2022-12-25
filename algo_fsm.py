#!/usr/bin/python3
# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
import sys
from algofsm import parse_input


# --------------------------------------------------------------------
# M A I N
# --------------------------------------------------------------------
def mainCmdParser():
    import argparse

    cmdParser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    cmdParser.add_argument(
        "file",
        type=str,
        default="-",
        nargs="?",
        help=f"filename of the Input file to process. Give - for stdin",
    )
    cmdParser.add_argument(
        "-out",
        type=str,
        default="/dev/stdout",
        help=f"generated output filename",
    )
    cmdParser.add_argument(
        "-behav",
        action="store_true",
        default=False,
        help=f"output is behavioral. By default is synthesizable",
    )
    cmdParser.add_argument(
        "-clk",
        type=str,
        default="clk",
        help=f"clock signal name. Prefix with ~ for negedge active"
    )
    cmdParser.add_argument(
        "-rst",
        type=str,
        default="~rst_n",
        help=(
            "reset signal name. Prefix with ~ for negedge active, "
            "suffix with : for sync"
        )
    )
    cmdParser.add_argument(
        "-ena",
        type=str,
        default="",
        help=(
            "if provided the FSM enable will advance controlled "
            "by this active high signal (with FSM number appended)"
        )
    )
    cmdParser.add_argument(
        "-sd",
        type=int,
        default=0,
        help=(
            "if you want a delay for <= assignements, e.g. 1 for #1. "
            "Enter 0 for no delay added"
        )
    )
    cmdParser.add_argument(
        "-prefix",
        type=str,
        default="SM",
        help=f"prefix for localparam state constants",
    )
    cmdParser.add_argument(
        "-state",
        type=str,
        default="state",
        help=f"name of state variable generated",
    )
    cmdParser.add_argument(
        "-name",
        type=str,
        default="algofsm",
        help=f"prefix used to derive block name etc.",
    )
    cmdParser.add_argument(
        "-indent",
        type=int,
        default=4,
        help=f"number of spaces used to indent"
    )
    cmdParser.add_argument(
        "-state_suffix",
        type=str,
        default="_r",
        help=f"suffix for flopped state variables",
    )
    cmdParser.add_argument(
        "-dbg",
        type=int,
        default=0,
        help=f"debug Level. More detailed for higher numbers",
    )
    args = cmdParser.parse_args()
    args.sd = "#" + str(args.sd) + " " if args.sd > 0 else ""
    args.rename_states = True  # False only for debug/development
    args.tab = " " * args.indent
    if args.file == "-":
        args.file = "/dev/stdin"
    if args.out == "-":
        args.out = "/dev/stdout"

    return args


if __name__ == "__main__":
    args = mainCmdParser()
    parse_input.parseInputFile(args)
    sys.exit(0)
