# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
import re
import sys


# ------------------------------------------------------------------------------
# Handles parse tree nodes
# ------------------------------------------------------------------------------
class Node:
    cnt = 0
    tab = "\t"

    def __init__(self, typ, code="", nxt=None, child=None, clone_id=None):
        child = child or []
        self.typ = typ
        self.code = code
        self.nxt = nxt
        self.child = child[:]
        self.visited = False
        self.clone_id = clone_id or Node.cnt
        self.uid = Node.cnt
        Node.cnt += 1

    @classmethod
    def reset(cls):
        cls.cnt = 0

    def __str__(self):
        return f"id{self.uid}"

    def clone(self):
        return Node(self.typ, self.code, self.nxt, self.child, self.uid)

    def to_str(self):
        out = Node.tab + f"{self} typ: {repr(self.typ)}" + "\n"
        for k, it in enumerate(self.child):
            if it is not None:
                out += Node.tab + f"ch{k}: {it}" + "\n"
        out += Node.tab + f"code: '{self.code}'" + "\n"
        out += Node.tab + f"nxt: {self.nxt}" + "\n"
        return "{\n" + out + "}"

    def inline_str(self):
        out = f"{self} typ:{repr(self.typ)} code:'{self.code}'"
        for k, it in enumerate(self.child):
            if it is not None:
                out += f" ch{k}:{it}"
        return out + (f" nxt:{self.nxt}" if self.nxt else "")

    def succ(self):
        return len(self.child) > 1 and self.child[1] or self.nxt

    def copy_flds_from(self, n):
        self.typ = n.typ
        self.code = n.code
        self.nxt = n.nxt
        self.child = list(n.child)


# ------------------------------------------------------------------------------
# Describes a lexer token
# ------------------------------------------------------------------------------
class Token:
    def __init__(self, pat, is_pat=False, is_skip=False):
        self.is_pat = is_pat
        self.pat = pat if is_pat else "(" + pat + ")"
        self.is_skip = is_skip
        self.loc_beg = ""
        self.loc_end = ""

    def __str__(self):
        return f"Token(pat={repr(self.pat)}, {self.loc_beg}, {self.loc_end})"


# ------------------------------------------------------------------------------
# Top down parser main class
# ------------------------------------------------------------------------------
class TopDown:
    def __init__(self, line_base, file_base):
        self.parse_in = ""
        self.parse_in_len = 0
        self.parse_last_token = None
        self.parse_consumed = 0
        self.parse_token_text = ""
        self.tokens = None
        self.nodes = []
        self.stk = []
        self.line_base = line_base
        self.file_base = file_base
        Node.reset()

    def set_tokens(self, tokens):
        self.tokens = tokens

    def set_input(self, parse_in):
        self.parse_in = parse_in
        self.parse_in_len = len(parse_in)

    # --------------------------------------------------------------------
    # tree modification related routines
    # --------------------------------------------------------------------
    def node_add(self, typ, code="", nxt=None, child=None):
        child = child or []
        # ensure node has 3 child elements at least
        ln = len(child)
        for i in range(3 - ln):
            child.append(None)
        new = Node(typ, code, nxt, child)
        self.nodes.append(new)
        return new

    # flag a node as removed
    def node_rm(self, node):
        node.typ = "rm" + node.typ

    def node_clone(self, n):
        new = n.clone()
        self.nodes.append(new)
        return new

    def change_links_to(self, new_node, org_node):
        assert org_node is not None
        # anything pointing to org_node should point now to new_node
        for n in self.nodes:
            if n.nxt == org_node:
                n.nxt = new_node
            for i, c in enumerate(n.child):
                if c == org_node:
                    n.child[i] = new_node

    # pre-insert a node before ref_node
    def node_preinsert(self, new_node, ref_node):
        # anything originally pointing to ref_node points to the new_node
        self.change_links_to(new_node, ref_node)
        # link new_node to point to ref_node
        new_node.nxt = ref_node

    def node_deep_clone(self, n):  # not used yet
        if n is None:
            return None
        new = self.node_clone(n)
        new.child = [self.node_deep_clone(c) for c in n.child]
        new.nxt = self.node_deep_clone(n.nxt)
        return new

    def node_find_last(self, n):
        while n.nxt:
            n = n.nxt
        return n

    def reset_visited(self):
        for n in self.nodes:
            n.visited = False

    # --------------------------------------------------------------------
    # GENERAL parsing routines
    # --------------------------------------------------------------------
    def eof(self):
        return self.parse_consumed == self.parse_in_len

    def get_token(self):
        def consume_pattern(pat):
            m = re.match(pat, self.parse_in[self.parse_consumed:], re.S)
            if m:
                self.parse_token_text = m.group(1)
                self.parse_consumed += len(m.group(1))
                return True
            return False

        loc_beg = self.parse_consumed
        tok = None
        while tok is None:
            if self.eof():
                tok = self.tokens.TK_EOF  # end
            else:
                for token_i in list(self.tokens):
                    if consume_pattern(token_i.value.pat):
                        if not token_i.value.is_skip:
                            tok = token_i
                        break
        tok.loc_beg = self.file_base + ":" + str(loc_beg)
        tok.loc_end = self.file_base + ":" + str(self.parse_consumed - 1)
        self.parse_last_token = tok

    def parse_get_char(self):
        if self.eof():
            return None
        c = self.parse_in[self.parse_consumed]
        self.parse_consumed += 1
        return c

    def token_ahead(self):
        if self.parse_last_token is None:
            self.get_token()
        return self.parse_last_token

    def token_match(self, tok):
        if self.token_ahead() == tok:
            self.parse_last_token = None  # consume it
            return True
        return False

    # --------------------------------------------------------------------
    # to build more complex rules
    # --------------------------------------------------------------------

    def must(self, rule_rc, msg):
        if not rule_rc:
            self.error(msg)
        return True

    def optional(self, rule_rc):
        return True

    # arg is the name of the rule as a string
    def one_or_more(self, rule):
        if rule():
            first = self.stk_top()
            while rule():
                prev, last = self.stk_pop(2)
                prev.nxt = last
                self.stk_push(last)
            self.stk_pop(1)
            self.stk_push(first)
            return True
        return False

    # --------------------------------------------------------------------
    # Parse tree related routines
    # --------------------------------------------------------------------
    def st_show_all(self, hdr):
        print(f"--- {hdr} ---")
        for node in self.nodes:  # TODO sorted
            print(node.inline_str())

    def st_show_from_node(self, name, root, path="./"):
        def sub_pr_st(ind, n, f):
            if n.visited:
                return
            n.visited = True
            print(ind + n.inline_str(), file=f)
            for it in n.child:  # follow links
                if it:
                    sub_pr_st(ind + Node.tab, it, f)
            if n.nxt:
                sub_pr_st(ind, n.nxt, f)

        self.reset_visited()
        with open(path + name + ".dbg", "w") as f:
            sub_pr_st("", root, f)

    # --------------------------------------------------------------------
    # parse stack management
    # --------------------------------------------------------------------
    # arg is item to push
    # stk[-1] contains the head of the stack (last item pushed)
    # stk[-2] contains the previous to the head of the stack
    # (previously pushed item)

    # push one item into the stack
    def stk_push(self, item):
        self.stk.append(item)
        return True

    # cnt is how many to pop. Returns list with popped items
    def stk_pop(self, cnt=1):
        popped = self.stk[-cnt:]
        self.stk = self.stk[:-cnt]
        return popped

    # return item located deeper into stack without popping it
    # depth=1 top, depth=2 top-1 etc
    def stk_top(self, depth=1):
        return self.stk[-depth]

    # print an error with some contextual info on input text
    # and stack trace of the code
    def error(self, msg):
        lines = self.parse_in[: self.parse_consumed].split("\n")
        nlines = len(lines)
        print(
            f"ERROR: {self.file_base}:{self.line_base+nlines}: {msg}\n",
            file=sys.stderr,
        )
        # give few previous lines of context
        i = nlines - 4
        if i < 0:
            i = 0
        curr_line = self.parse_in[self.parse_consumed:].split("\n")[0]
        for line in lines[i:]:
            print(
                "%4d: %s" % (self.line_base + i + 1, line),
                file=sys.stderr,
                end="",
            )
            if i == nlines - 1:
                print(" <-- %s" % curr_line, file=sys.stderr, end="")
            print("", file=sys.stderr)
            i += 1
        la = self.token_ahead()
        print(f"\nBut got {la}" + "\n", file=sys.stderr)

        import traceback

        traceback.print_stack()
        sys.exit(1)
