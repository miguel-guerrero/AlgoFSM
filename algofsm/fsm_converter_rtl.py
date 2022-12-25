# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
from collections import defaultdict
from . import fsm_converter
from . import dag_utils
from . import utils
from . import vlogparser


# Derived class takes care of transforming the code into a
# synthesizable RTL version.
class FsmConverterRTL(fsm_converter.FsmConverter):
    def __init__(self, args):
        super().__init__(args)
        self.rename_state = {}
        self.parser = None
        self.root = None

    def _expand_input(beh_in):
        # Expand the input to have an infinite loop around it
        inp = "while(1) begin\n"
        inp += "`tick;\n"
        inp += beh_in
        inp += "end\n"
        return inp

    # RTL output
    def process_block(self, beh_in, ind, line_base, file_base=""):
        self.oprefix = f"{self.args.prefix}{self.sm_num}_"
        self.ostate = f"{self.args.state}{self.sm_num}"

        # --- generate code ---
        self.tick, self.tick_no_rst = utils.get_ticks(self.args)
        self.reset_cond, self.not_reset_cond = utils.get_resets(self.args)

        # Start transformations and output generation
        inp = FsmConverterRTL._expand_input(beh_in)

        # Start VLOG parsing
        if self.args.dbg >= 3:
            print("--- input ---\n")
            print(inp)
            print("-------------\n")

        # parse the code and build a syntax tree
        self.parser = parser = vlogparser.VlogParser(inp, line_base, file_base)
        self.root = root = parser.start_rule()

        # --- state machine (RTL) output
        if self.args.dbg > 0:
            with open("algofsm.dbg", "w") as f:
                print("-- before source --", file=f)
                print(f"{inp}", file=f)
            parser.st_show_from_node(f"{self.sm_num}_00_before", root)
            parser.dump_dot(f"{self.sm_num}_00_before", root)

        # do some conversions at tree level
        dag_utils.expand_tree_structs(
            parser, root, root, ind, self.sm_num, self.args.dbg
        )
        if self.args.dbg > 0:
            parser.st_show_from_node(
                f"{self.sm_num}_02_after_expand_struct", root
            )
            parser.dump_dot(f"{self.sm_num}_02_after_expand_struct", root)

        # convert the syntax tree into a DAG which when read will generated
        # the right FSM
        dag_utils.convert_to_dag(
            parser, root, root, ind, self.sm_num, self.args.dbg
        )
        if self.args.dbg > 0:
            parser.st_show_from_node(
                f"{self.sm_num}_04_after_convert_to_dag", root
            )
            parser.dump_dot(f"{self.sm_num}_04_after_convert_to_dag", root)

        # eliminate redundant states in the DAG (they produce identical code)
        self.merge_states(parser, root, ind)
        if self.args.dbg > 0:
            parser.st_show_from_node(
                f"{self.sm_num}_09_after_merge_states", root
            )
            parser.dump_dot(f"{self.sm_num}_09_after_merge_states", root)

        # walk the DAG to produce RTL output
        return self.dump_dag_sm(parser, root, ind, line_base, file_base)

    # --------------------------------------------------------------------
    # DAG modification related routines
    # --------------------------------------------------------------------
    def merge_states(self, p, root, ind):

        iter_cnt = 0
        some_merged = True
        while some_merged:
            some_merged = False
            tk_nodes = [node for node in p.nodes if node.typ == "tk"]

            for mode in ("abs", "rel"):
                tknodes_by_code = defaultdict(list)

                # dump graph from each "tk" node
                for tknode in tk_nodes:
                    visited = set()
                    codegen = self.dump_subdag_sm(
                        tknode.succ(), ind + "      ", mode, tknode, visited
                    )
                    # keep track of how many tknodes generate same code
                    tknodes_by_code[codegen].append(tknode)

                # see which tknode's generated identical code
                for codegen, tknodes in tknodes_by_code.items():
                    if len(tknodes) > 1:
                        some_merged = FsmConverterRTL.merge_ids(p, tknodes)
                        break

                if some_merged:
                    if self.args.dbg > 1:
                        p.st_show_from_node(
                            f"{self.sm_num}_05_during_merging{iter_cnt}", root
                        )
                        p.dump_dot(
                            f"{self.sm_num}_05_during_merging{iter_cnt}", root
                        )
                        iter_cnt += 1
                    break
            # end for mode
        # end while some_merged

    @staticmethod
    def merge_ids(p, nodes_to_merge):
        node_a = nodes_to_merge[0]
        for node_b in nodes_to_merge[1:]:
            FsmConverterRTL.merge_keeping_first(p, node_a, node_b)
        return True

    @staticmethod
    def merge_keeping_first(p, node_a, node_b):
        link_type_given_node = p.links_to(node_b)
        nodes_linking_to_b = list(link_type_given_node.keys())  # TODO sort
        # anything pointing to b should now point to a
        for node_from in nodes_linking_to_b:
            link_types = link_type_given_node[node_from]
            for t in link_types:
                if t == "bt":
                    node_from.child[1] = node_a
                if t == "bf":
                    node_from.child[2] = node_a
                if t == "nx":
                    node_from.nxt = node_a

        p.node_rm(node_b)  # tk removed
        # make the id of the new tk node the combination of both
        lst = sorted((node_a.code, node_b.code))
        node_a.code = "_".join(lst)

    # --------------------------------------------------------------------
    # code generation
    # --------------------------------------------------------------------
    @staticmethod
    def find_first_tk(p, node):
        def find_first_tk_sub(node):
            if node is None or node.visited:
                return
            node.visited = True
            if node.typ == "tk":
                return node
            lst = (node.child[1], node.child[2], node.child[0], node.nxt)
            for n in lst:
                ntk = find_first_tk_sub(n)
                if ntk is not None:
                    return ntk

        p.reset_visited()
        node = find_first_tk_sub(node)
        if node is not None:
            return node
        utils.error("Cannot determine initial state (no `tick at all found)")

    def state_name(self, node):
        st_name = f"{self.oprefix}S{node.code}"
        if self.args.rename_states:
            renamed = self.rename_state.get(node)
            if renamed is not None:
                st_name = f"{self.oprefix}{renamed}"
        return st_name

    staticmethod

    def _compute_state_bits(tks_by_code):
        state_bits_m1 = 0
        max_state = 2
        for i, _ in enumerate(tks_by_code):
            if i >= max_state:
                max_state *= 2
                state_bits_m1 += 1
        return state_bits_m1

    # compute localparam state definition and rename_state dict
    def _compute_localpars(self, tks):
        par_out = utils.Dumper()
        for i, code in enumerate(sorted(tks.keys())):
            tknode = tks[code]
            self.rename_state[tknode] = i
            st_name = self.state_name(tknode)
            par_out.dump(f"localparam {st_name} = {i};")
        return par_out.val()

    # dump graph as an FSM
    def dump_dag_sm(self, p, root, ind, line_base, file_base):
        sd = self.args.sd
        tab = self.args.tab
        curr = self.args.state_suffix

        ena_guard = ""
        if self.args.ena != "":
            ena = self.args.ena + str(self.sm_num)
            ena_guard = f"if ({ena}) "

        tks_by_code = {node.code: node for node in p.nodes if node.typ == "tk"}

        state_bits_m1 = FsmConverterRTL._compute_state_bits(tks_by_code)
        par_out = self._compute_localpars(tks_by_code)

        init_state_node = FsmConverterRTL.find_first_tk(p, root)
        init_state = self.state_name(init_state_node)

        out = utils.Dumper()

        out.dump()
        out.dump(f"// AlgoFSM{self.sm_num} {{\n")
        out.dump(f"// state constant definition")
        out.dump(utils.indent(ind, par_out))

        # SINGLE BLOCK STYLE
        out.dump()
        out.dump(ind + f"always {self.tick} begin : {self.oname}")

        if self.ff_local_decl_in != "":
            out.dump()
            out.dump(ind + tab + "// local flop declarations")
            out.dump(utils.indent(ind + tab, self.ff_local_decl_in))

        out.dump(
            ind
            + tab
            + f"reg [{state_bits_m1}:0] {self.ostate}{curr}, "
            + f"{self.ostate};"
        )

        out.dump()
        out.dump(ind + tab + f"if ({self.reset_cond}) begin")
        if self.ff_rst_in != "":
            out.dump(utils.indent(ind + 2 * tab, self.ff_rst_in))

        out.dump(ind + 2 * tab + f"{self.ostate}{curr} <= {sd}{init_state};")
        out.dump(ind + tab + "end")
        out.dump(ind + tab + f"else {ena_guard}begin")
        out.dump(ind + 2 * tab + "// set defaults for next state ")
        out.dump(utils.indent(ind + 2 * tab, self.ff_update_nxt))
        out.dump(ind + 2 * tab + f"{self.ostate} = {self.ostate}{curr};")
        out.dump()
        out.dump(ind + 2 * tab + "// SmForever")
        out.dump(ind + 2 * tab + f"case ({self.ostate}{curr})")

        for code in sorted(tks_by_code.keys()):
            visited = set()
            node = tks_by_code[code]
            st_name = self.state_name(node)
            out.dump(ind + 3 * tab + f"{st_name}: begin")
            out.dump(
                self.dump_subdag_sm(
                    node.succ(), ind + 4 * tab, "rel", node, visited
                )
            )
            out.dump_nonl(ind + 3 * tab + f"end")

        out.dump(ind + 2 * tab + "endcase")
        out.dump(ind + 2 * tab + "// SmEnd")
        out.dump()
        out.dump(ind + 2 * tab + f"// Update state registers")
        out.dump(utils.indent(ind + 2 * tab, self.ff_update_ffs))
        out.dump(ind + 2 * tab + f"{self.ostate}{curr} <= {sd}{self.ostate};")
        out.dump(ind + tab + "end")
        out.dump(ind + "end")

        out.dump()
        out.dump(ind + "// rename local state registers dropping suffix")
        out.dump(utils.indent(ind, self.ff_rename_ffs))

        out.dump()
        out.dump(f"// }} AlgoFSM{self.sm_num}\n")
        return out.val()

    def dump_subdag_sm(self, node, ind, mode, state_node, visited_in):

        stay_txt = "// stay in state"
        visited = set(visited_in)  # make a value copy

        def flag_visited(node):
            visited.add(node.uid)

        def build_if_else(cond, true_blk, false_blk):
            out = ""
            if (
                false_blk is not None
                and utils.is_only_stay(stay_txt, true_blk)
            ):
                out += ind + f"if ({utils.negate(cond)}) begin" + "\n"
                out += false_blk
                out += ind + "end\n"
            else:
                out += ind + f"if ({cond}) begin" + "\n"
                out += true_blk
                out += ind + "end\n"
                if false_blk is not None:
                    out += ind + "else begin\n"
                    out += false_blk
                    out += ind + "end\n"
            return out

        tab = self.args.tab
        out = ""
        while node:
            if node.uid in visited:
                visited_str = ", ".join([str(x) for x in visited])
                self.parser.st_show_from_node(f"error", self.root)
                self.parser.dump_dot(
                    f"error",
                    self.root,
                    msg="loop within " + visited_str,
                    hilight=list(visited),
                )
                utils.error(
                    f"SM{self.sm_num} There is a loop path without `tick "
                    f"within the set of nodes {visited_str}. Currently "
                    f"@{node.uid}. See error.dot/.dbg"
                )

            nx, ch1, ch2 = node.nxt, node.child[1], node.child[2]

            if node.typ == "eif":
                flag_visited(node)
                cond = node.code
                if utils.is_one(cond):
                    out += self.dump_subdag_sm(
                        ch1, ind, mode, state_node, visited
                    )
                elif utils.is_zero(cond):
                    n = ch2 if ch2 else nx
                    if n:
                        out += self.dump_subdag_sm(
                            n, ind, mode, state_node, visited
                        )
                else:
                    true_blk = self.dump_subdag_sm(
                        ch1, ind + tab, mode, state_node, visited
                    )
                    n = ch2 if ch2 else nx
                    false_blk = None
                    if n:
                        false_blk = self.dump_subdag_sm(
                            n, ind + tab, mode, state_node, visited
                        )
                    out += build_if_else(cond, true_blk, false_blk)

                node = None
            elif node.typ == "if":
                flag_visited(node)
                cond = node.code
                if utils.is_one(cond):
                    out += self.dump_subdag_sm(
                        ch1, ind, mode, state_node, visited
                    )
                elif utils.is_zero(cond):
                    out += self.dump_subdag_sm(
                        ch2, ind, mode, state_node, visited
                    )
                else:
                    true_blk = self.dump_subdag_sm(
                        ch1, ind + tab, mode, state_node, visited
                    )
                    false_blk = None
                    if ch2:
                        false_blk = self.dump_subdag_sm(
                            ch2, ind + tab, mode, state_node, visited
                        )
                    out += build_if_else(cond, true_blk, false_blk)
                node = nx
            elif node.typ == "fo":
                flag_visited(node)
                cond = node.code
                out += ind + f"for ({cond}) begin" + "\n"
                out += self.dump_subdag_sm(
                    ch1, ind + tab, mode, state_node, visited
                )
                out += ind + "end\n"
                node = nx
            elif node.typ == "wh":
                flag_visited(node)
                cond = node.code
                out += ind + f"while ({cond}) begin" + "\n"
                out += self.dump_subdag_sm(
                    ch1, ind + tab, mode, state_node, visited
                )
                out += ind + "end\n"
                node = nx
            elif node.typ == "sn":
                flag_visited(node)
                out_code = node.code
                out += ind + f"{out_code};\n"
                node = node.succ()
            elif node.typ == "cm":
                out += ind + f"{node.code}"
                node = node.succ()
            elif node.typ == "cs":
                flag_visited(node)
                cond = node.code
                out += ind + f"case ({cond})" + "\n"
                out += self.dump_subdag_sm(
                    ch1, ind + tab, mode, state_node, visited
                )
                out += ind + "endcase\n"
                node = nx
            elif node.typ == "csb":
                flag_visited(node)
                expr = node.code
                out += ind + f"{expr} begin" + "\n"
                out += self.dump_subdag_sm(
                    ch1, ind + tab, mode, state_node, visited
                )
                out += ind + "end\n"
                node = nx
            elif node.typ == "tk":
                if mode == "rel" and node == state_node:
                    out += ind + stay_txt + "\n"
                else:
                    state_name = self.state_name(node)
                    out += ind + f"{self.ostate} = {state_name};\n"
                node = None
            else:
                out += (
                    ind
                    + f"// Ignoring node={node} typ={node.typ} "
                    + f"code='{node.code}'"
                    + "\n"
                )
                node = node.succ()
        return out
