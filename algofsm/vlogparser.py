# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# VLOG simplified parsing
# ------------------------------------------------------------------------------
import html
from collections import defaultdict
from enum import Enum
from . import topdown as td
from . import utils


class VlogTokens(Enum):
    # In priority order
    TK_PRSLCOMMENT = td.Token(r"(\/\/\/(.*?)\n)", True)  # preserved comments ///
    TK_SLCOMMENT = td.Token(
        r"(\/\/(.*?)\n)", is_pat=True, is_skip=True
    )  # skip comments //
    TK_WS = td.Token(r"(\s+)(.*)", is_pat=True, is_skip=True)  # skip whitespace
    TK_WHILE = td.Token(r"while\b")
    TK_IF = td.Token(r"if\b")
    TK_ELSE = td.Token(r"else\b")
    TK_FOR = td.Token(r"for\b")
    TK_DO = td.Token(r"do\b")
    TK_CASE = td.Token("case\b")
    TK_ENDCASE = td.Token(r"endcase\b")
    TK_BEGIN = td.Token(r"begin\b")
    TK_END = td.Token(r"end\b")
    TK_TICK = td.Token(r"`tick\b")
    TK_OPEN_PAR = td.Token("\\(")
    TK_SEMICOLON = td.Token(";")
    TK_SN = td.Token(r"(.*?);", is_pat=True)  # catch all sentence
    TK_EOF = td.Token("")


class VlogParser(td.TopDown):
    def __init__(self, inp, line_base, file_base):
        super().__init__(line_base, file_base)
        self.set_tokens(VlogTokens)
        self.set_input(inp)
        self.tick_num = 0

    def start_rule(self):

        # short-cuts
        token_match = self.token_match
        one_or_more = self.one_or_more
        must = self.must

        def rule_sentences():
            return one_or_more(rule_sentence)

        def rule_end():
            return token_match(self.tokens.TK_EOF)

        def rule_sentence():
            return (
                rule_if()
                or rule_while()
                or rule_block()
                or rule_tick()
                or rule_prcomment()
                or rule_for()
                or rule_case()
                or rule_do_while()
                or rule_sn()
            )

        def rule_if():
            if token_match(self.tokens.TK_IF):
                must(rule_pexpr(), "if: Expecting parenthesis expression")
                must(rule_sentence(), "if: Expecting sentence/blk")
                if self.token_ahead() != self.tokens.TK_ELSE:
                    cond, bodyt = self.stk_pop(2)
                    n = self.node_add("if", cond.code, None, [None, bodyt])
                else:
                    token_match(self.tokens.TK_ELSE)
                    must(rule_sentence(), "else: Expecting sentence/blk")
                    cond, bodyt, bodyf = self.stk_pop(3)
                    n = self.node_add(
                        "if", cond.code, None, [None, bodyt, bodyf]
                    )
                self.node_rm(cond)
                return self.stk_push(n)
            return False

        def rule_while():
            if token_match(self.tokens.TK_WHILE):
                must(rule_pexpr(), "while: Expecting parenthesis expression")
                must(rule_sentence(), "while: Expecting sentence/blk")
                cond, body = self.stk_pop(2)
                n = self.node_add("wh", cond.code, None, [None, body])
                self.node_rm(cond)
                return self.stk_push(n)
            return False

        def rule_do_while():
            if token_match(self.tokens.TK_DO):
                must(rule_sentence(), "while: Expecting sentence/blk")
                token_match(self.tokens.TK_WHILE)
                must(rule_pexpr(), "while: Expecting parenthesis expression")
                must(token_match(self.tokens.TK_SEMICOLON), "Expected ;")
                body, cond = self.stk_pop(2)
                n = self.node_add("do", cond.code, None, [None, body])
                self.node_rm(cond)
                return self.stk_push(n)
            return False

        def rule_block():
            if token_match(self.tokens.TK_BEGIN):
                must(rule_sentences(), "Empty block")  # TODO allow empty
                return must(token_match(self.tokens.TK_END), "Expected end")
            return False

        def rule_tick():
            if token_match(self.tokens.TK_TICK):
                self.stk_push(self.node_add("tk", str(self.tick_num)))
                self.tick_num += 1
                return must(
                    token_match(self.tokens.TK_SEMICOLON), "Expected ;"
                )
            return False

        def rule_for():
            if token_match(self.tokens.TK_FOR):
                must(rule_pexpr(), "for: Expecting parenthesis expression")
                must(rule_sentence(), "for: Expecting sentence/blk")
                cond, body = self.stk_pop(2)
                n = self.node_add("fo", cond.code, None, [None, body])
                self.node_rm(cond)
                return self.stk_push(n)
            return False

        def rule_case():
            if token_match(self.tokens.TK_CASE):
                must(rule_pexpr(), "case: Expecting parenthesis expression")
                must(
                    one_or_more(rule_case_statement),
                    "need at least one case statement",
                )
                must(token_match(self.tokens.TK_ENDCASE), "expected endcase")
                cond, body = self.stk_pop(2)
                n = self.node_add("cs", cond.code, None, [None, body])
                self.node_rm(cond)
                return self.stk_push(n)
            return False

        def rule_case_statement():
            if rule_case_expr():
                must(rule_sentence(), "case statement: expecting sentence")
                expr, body = self.stk_pop(2)
                return self.stk_push(
                    self.node_add("csb", expr.code, None, [expr, body])
                )
            return False

        def rule_case_expr():
            backtrack_point = self.parse_consumed
            inner_str = ""
            c = ""
            while c != ":":
                c = self.parse_get_char()
                if c is None or c == ";":
                    self.parse_consumed = backtrack_point
                    return False
                if c not in " \t\n":
                    inner_str += c
            return self.stk_push(self.node_add("case_expr", inner_str))

        # capture a parenthesis expression by keeping track till it closes
        def rule_pexpr():
            if token_match(self.tokens.TK_OPEN_PAR):
                inner_str = ""
                paren_level = 1
                while paren_level > 0:
                    c = self.parse_get_char()
                    if c is None:
                        self.error("Unfinished rule_pexpr")
                    if c == "(":
                        paren_level += 1
                    elif c == ")":
                        paren_level -= 1
                    if paren_level > 0:
                        inner_str += c
                return self.stk_push(self.node_add("pexpr", inner_str))
            return False

        def rule_prcomment():
            if token_match(self.tokens.TK_PRSLCOMMENT):
                return self.stk_push(
                    self.node_add("cm", self.parse_token_text)
                )
            return False

        def rule_sn():
            if token_match(self.tokens.TK_SN):
                self.stk_push(self.node_add("sn", self.parse_token_text))
                if utils.is_nonblocking_assign(self.parse_token_text):
                    utils.error(
                        "non-blocking assignments not allowed "
                        "within an AlgoFSM block, found: "
                        f"{self.parse_token_text}"
                    )
                return must(
                    token_match(self.tokens.TK_SEMICOLON), "Expected ;"
                )
            # elif token_match(self.tokens.TK_SEMICOLON): #TODO
            #   self.stk_push(self.node_add("sn", "/* empty */"))
            #   return True
            return False

        # THE starting rule
        if rule_sentences() and rule_end():
            return self.stk[-1]  # root

        self.error("Expecting rule_sentences")

    # ------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------

    # find out which nodes link to 'dst' node, returning a hash
    # with the modes as keys and they type of link as value (bt/bf/nx)
    def links_to(self, dst):
        to = {}
        for n in self.nodes:
            t = []
            if n.child[1] == dst:
                t.append("bt")
            if n.child[2] == dst:
                t.append("bf")
            if n.nxt == dst:
                t.append("nx")
            if t != []:
                to[n] = list(t)
        return to

    # see if subtree hanging from node 'n' has a typ=="tk" node
    def has_tick(self, n):
        def has_tick_lst(n):
            while n:
                if self.has_tick(n):
                    return True
                n = n.nxt
            return False

        if n:
            if n.typ == "tk":  # base case, we found a "tk" node
                return True
            if n.typ == "wh" or n.typ == "do" or n.typ == "fo":
                return has_tick_lst(n.child[1])
            if n.typ == "if":
                return has_tick_lst(n.child[1]) or has_tick_lst(n.child[2])
            if n.typ == "sn" or n.typ == "cm":
                return False
            if n.typ[:2] == "rm":
                return False
            assert False, f"typ {n.typ} not handled in VlogParser::has_tick"
        return False

    # ------------------------------------------------------------------------------
    # Tree dump routines
    # ------------------------------------------------------------------------------

    def dump_dot(
        self,
        name="tree",
        root=None,
        msg=None,
        hilight=None,
        tab="\t",
        path="./",
    ):
        # used to display cloned nodes at the same level
        def node_ranks(nodes):
            clone_ids = defaultdict(list)
            for n in nodes:
                clone_ids[n.clone_id].append(n.uid)
            return list(clone_ids.values())

        hilight = hilight or []
        with open(path + name + ".dot", "w") as f:
            print(f"digraph _{name}_ " + "{", file=f)
            print(tab + f"shape=circle;", file=f)
            print(tab + f"{root.uid} [style=filled fillcolor=green];", file=f)
            if msg:
                print(
                    tab + f'title [label="{msg}" shape=box style=bold];',
                    file=f,
                )
            for r in node_ranks(self.nodes):
                if len(r) > 1:
                    nodes = ";".join([str(x) for x in r]) + ";"
                    print(tab + "{rank=same; " + nodes + "}", file=f)

            for n in self.nodes:
                if n.typ[:2] != "rm":
                    name = n.uid
                    esc_code = html.escape(n.code)
                    if n.typ == "tk":
                        print(
                            tab
                            + f"{name} [shape=box label=<{name}: "
                            + '<font color="red">'
                            + f"{n.typ} {esc_code}</font>>];",
                            file=f,
                        )
                    else:
                        code = (
                            "" if n.code == "" else f"<br/><b>{esc_code}</b>"
                        )
                        print(
                            tab
                            + f'{name} [label=<{name}: <font color="blue">'
                            + f"{n.typ} </font>{code}>];",
                            file=f,
                        )

                    if n.uid in hilight:
                        print(
                            tab + f"{name} [style=filled fillcolor=yellow];",
                            file=f,
                        )

                    if n.child[0] is not None:
                        print(
                            tab
                            + f"{name} -> {n.child[0].uid} [style=dotted];",
                            file=f,
                        )
                    if n.child[1] is not None:
                        print(tab + f"{name} -> {n.child[1].uid} ;", file=f)
                    if n.child[2] is not None:
                        print(
                            tab
                            + f"{name} -> {n.child[2].uid} "
                            + f"[label=f color=grey];",
                            file=f,
                        )
                    if n.nxt is not None:
                        print(
                            tab + f"{name} -> {n.nxt.uid} [label=nx];", file=f
                        )
            print("}", file=f)
