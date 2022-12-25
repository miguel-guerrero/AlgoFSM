# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
import re
from enum import Enum, auto
from . import utils
from . import fsm_converter
from . import fsm_converter_rtl


class ParserState(Enum):
    Idle = auto()
    Done = auto()
    InSmBegin = auto()
    InSmForever = auto()
    InSmEnd = auto()


# --- Top level parsing of the file
# --- Identify several sections and grab their contents
def parseInputFile(args):
    with open(args.out, "w") as fout:
        state = ParserState.Idle
        line_no = 0
        line_base = 0
        with open(args.file) as fin:
            line = fin.readline()
            while line:
                lineStr = line.strip()
                line_no += 1
                if state == ParserState.Idle or state == ParserState.Done:
                    if "SmBegin" == lineStr:
                        state = ParserState.InSmBegin
                        decl_in = ""
                        inp = ""
                    else:
                        print(line, end="", file=fout)
                elif state == ParserState.InSmBegin:
                    if "SmForever" == lineStr:
                        line_base = line_no
                        state = ParserState.InSmForever
                    else:
                        decl_in += line
                elif state == ParserState.InSmForever:
                    if "SmEnd" == lineStr:
                        state = ParserState.InSmEnd
                    else:
                        # allow a flop defintion to be embedded within the
                        # forever block the first portion of the match is
                        # to grab indent level
                        m = re.match(r"(\s*)SmDecl:\s*(.*)", line)
                        if m:
                            ind, rest = m.groups()
                            decl_in += ind + rest + "\n"
                        else:
                            inp += line

                if state == ParserState.InSmEnd:
                    if args.behav:
                        conv = fsm_converter.FsmConverter(args)
                    else:
                        conv = fsm_converter_rtl.FsmConverterRTL(args)
                    conv.extract_initial(decl_in)
                    out = conv.process_block(inp, "", line_base, args.file)
                    print(out, file=fout)
                    state = ParserState.Done

                line = fin.readline()

    if state == ParserState.Idle:
        utils.warning("SmBegin section not found")
    elif state == ParserState.InSmBegin:
        utils.error("SmCombo/SmForever section not found")
    elif state == ParserState.InSmForever:
        utils.error("SmEnd not found")
