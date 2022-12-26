# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
import re
from . import utils


# Base class dumps only a behavioral description of the input which has
# almost no code transformation. Mostly to verify the algorithm
class FsmConverter:

    sm_num = -1

    def __init__(self, args):
        self.args = args
        FsmConverter.sm_num += 1
        self.oname = f"{self.args.name}{self.sm_num}"
        self.ff_local_decl_in = ""
        self.ff_rst_in = ""
        self.ff_update_ffs = ""
        self.ff_rename_ffs = ""
        self.ff_update_ffs_beh = ""
        self.ff_update_nxt = ""
        self.reg_track_init = {}

    # gather some information to build the output FSM
    def extract_initial(self, txt, line_decl_base):
        def get_width_var(width, var):
            m = re.search(r"(\[.*\])\s*(.*)", var)
            if m:
                width, var = m.groups()
                width += " "
            else:
                var = re.sub(r"^\s*", "", var)
            return width, var

        curr = self.args.state_suffix
        sd = self.args.sd
        line_no = line_decl_base
        for line in txt.split("\n"):
            line_no += 1
            line = line.replace(";", "")  # TODO
            line = line.rstrip()

            if line != "":
                init_assings = re.split(",", line)
                width = ""
                local = False
                reg = False
                # walk over each of signal/variables declared in this line
                for init_assign in init_assings:

                    # we expect var = expr
                    try:
                        var, init = re.split(r"\s*\=\s*", init_assign)
                        if var[-1] == "<":
                            utils.error(
                                "Non-blocking assignments shouldn't be used"
                                "in algofsm blocks while processing: "
                                f"{init_assign}"
                            )
                    except ValueError:
                        utils.error(
                            f"'{init_assign}' is missing an initial val. "
                            f"line {line_no}: {line}"
                        )

                    # flag if this is a declaration
                    if re.search("reg", var):
                        reg = True
                        var = re.sub(r"reg\s*", "", var)

                    # flag if this is a local declaration
                    if re.search("local", var):
                        local = True
                        var = re.sub(r"local\s*", "", var)

                    # capture the width, only present on the first var
                    # the others will use it from the first
                    width, var = get_width_var(width, var)

                    self.reg_track_init[var] = init

                    if not (local or reg):
                        utils.error(
                            f"missing local or reg. line {line_no}: {line}"
                        )

                    self.ff_local_decl_in += (
                        f"reg {width}{var}{curr}, {var};\n"
                    )

                    if init != "":
                        if self.args.behav:
                            self.ff_rst_in += f"{var} = {init};\n"
                        else:
                            self.ff_rst_in += f"{var}{curr} <= {sd}{init};\n"

                    self.ff_update_ffs += f"{var}{curr} <= {sd}{var};\n"

                    scope = self.oname + "."
                    self.ff_update_ffs_beh += (
                        f"{scope}{var}{curr} <= {sd}{scope}{var};\n"
                    )

                    self.ff_update_nxt += f"{var} = {var}{curr};\n"

                    if not local:
                        self.ff_rename_ffs += (
                            f"wire {width}{var} = {scope}{var}{curr};\n"
                        )

    def _task_update_ffs(self, ind, oname, out):
        tab = self.args.tab
        out.dump(ind + f"task {oname}_update_ffs;")
        out.dump(ind + tab + "begin")
        out.dump(utils.indent(ind + 2 * tab, self.ff_update_ffs_beh))
        out.dump(ind + tab + "end")
        out.dump(ind + "endtask")

    # behavioral output
    def process_block(self, beh_in, ind, line_base, file_base=""):

        out = utils.Dumper()

        # --- generate code ---
        self.tick, self.tick_no_rst = utils.get_ticks(self.args)
        self.reset_cond, self.not_reset_cond = utils.get_resets(self.args)

        tab = self.args.tab
        ena = ""
        if self.args.ena != "":
            ena = self.args.ena + str(self.sm_num)
        # --- Behavioral output
        out.dump()
        out.dump(f"// AlgoFSM{self.sm_num} {{")
        out.dump()
        if ena == "":
            out.dump(
                ind
                + f"`define tick \\\n"
                + f"    do begin \\\n"
                + f"        {self.oname}_update_ffs; \\\n"
                + f"        {self.tick}; \\\n"
                + f"        if ({self.reset_cond}) \\\n"
                + f"            disable {self.oname}_loop; \\\n"
                + f"    end while (0)"
            )
        else:
            out.dump(
                ind
                + f"`define tick \\\n"
                + f"    do begin \\\n"
                + f"        {self.oname}_update_ffs; \\\n"
                + f"        do {self.tick}; while(~{ena}); \\\n"
                + f"        if ({self.reset_cond}) \\\n"
                + f"            disable {self.oname}_loop; \\\n"
                + f"    end while (0)"
            )

        out.dump()
        self._task_update_ffs(ind, self.oname, out)

        out.dump()
        out.dump(ind + f"always {self.tick} begin : {self.oname}")

        if self.ff_local_decl_in != "":
            out.dump()
            out.dump(ind + tab + "// local declarations")
            out.dump(utils.indent(ind + tab, self.ff_local_decl_in))

        out.dump()
        out.dump(
            ind + tab + f"if ({self.not_reset_cond}) begin // not in reset"
        )
        out.dump(ind + 2 * tab + f"begin : {self.oname}_loop")
        out.dump(ind + 3 * tab + "while (1) begin")
        out.dump(
            ind
            + 4 * tab
            + f"// SmForever verbatim from {file_base}:{line_base}"
        )
        out.dump(utils.indent(ind + 3 * tab, beh_in))
        out.dump(ind + 4 * tab + "// SmEnd verbatim end")
        out.dump(ind + 4 * tab + "`tick;")
        out.dump(ind + 3 * tab + "end")
        out.dump(ind + 2 * tab + "end")
        out.dump(ind + tab + "end")

        if self.ff_rst_in != "":
            out.dump(ind + tab + "// reset behavior")
            out.dump(utils.indent(ind + tab, self.ff_rst_in))
            out.dump(utils.indent(ind + tab, f"{self.oname}_update_ffs;"))

        out.dump(ind + "end")

        out.dump()
        out.dump(ind + "// rename local registered signals dropping suffix")
        out.dump(utils.indent(ind, self.ff_rename_ffs))

        out.dump()
        out.dump(ind + "`undef tick")
        out.dump()
        out.dump(f"// }} AlgoFSM{self.sm_num}\n")
        return out.val()
