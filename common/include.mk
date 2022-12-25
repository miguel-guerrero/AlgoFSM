SHELL := /bin/bash
#SIM=vcs -R
PREPRO=../../vlog_prep.sh
COMP=iverilog -o sim.x
SIM=vvp sim.x
CURR=$(shell pwd)
ALGOFSM=../../algo_fsm.py
TOFSMOPTS?=    # -sd 1 
EXTRA_MODS?=


test: sim.beh.log sim.sm.log
	@diff <(../filter_log.sh sim.beh.log) <(../filter_log.sh sim.sm.log) && echo TEST COMPARISON PASSED || \
            echo TEST COMPARISON FAILED

gls: sim.sm.log sim.gls.log
	@diff <(../filter_log.sh sim.sm.log) <(../filter_log.sh sim.gls.log) && echo TEST COMPARISON PASSED || \
            echo TEST COMPARISON FAILED

clean:
	rm -f design_out.*.v *.log *.vcd sim.x design_out.sm.vg *.dot *.dbg *.dot.pdf

#----------------------------------------------------------
# convert from AlgoFsm sequential code to synthesizable RTL
design_out.sm.v : design.v $(ALGOFSM)
	@echo -----------------------------------------------------------
	@echo     compiling design.sm.v into a state machine design_out.sm.v
	@echo -----------------------------------------------------------
	$(PREPRO) $< - | $(ALGOFSM) $(TOFSMOPTS) -out design_out.sm.v -

# invoke generated RTL FSM code simulation and dump results to sim.sm.log
sim.sm.log : design_out.sm.v tb.v
	@echo -----------------------------------------------------------
	@echo     running example tb including RTL design_out.sm.v
	@echo -----------------------------------------------------------
	$(COMP) -g2001 design_out.sm.v tb.v $(EXTRA_MODS)
	$(SIM) | tee sim.sm.log 2>&1


#----------------------------------------------------------
# make AlgoFsm sequential simulatable as behavioral verilog
design_out.beh.v : design.v $(ALGOFSM)
	@echo -----------------------------------------------------------
	@echo     compiling design.beh.v into behavioral design_out.beh.v
	@echo -----------------------------------------------------------
	$(PREPRO) $< - -DBEHAV | $(ALGOFSM) $(TOFSMOPTS) -behav -out design_out.beh.v -

# invoke behavioral FSM code simulation and dump results to sim.beh.log
sim.beh.log : design_out.beh.v tb.v
	@echo -----------------------------------------------------------
	@echo     running example tb including behavioral design_out.beh.v
	@echo -----------------------------------------------------------
	$(COMP) -g2005-sv -D BEHAV=1 design_out.beh.v tb.v $(EXTRA_MODS)
	$(SIM) | tee sim.beh.log 2>&1


#----------------------------------------------------------
# synthesize RTL FSM code using yosys
design_out.sm.vg: design_out.sm.v
	yosys -p "read_verilog design_out.sm.v; proc; opt; write_verilog design_out.sm.vg" > syn.log

# simulate synthesized code and generate simulation log file
sim.gls.log: design_out.sm.vg tb.v
	@echo -----------------------------------------------------------
	@echo     running example tb including RTL design_out.sm.v
	@echo -----------------------------------------------------------
	$(COMP) -g1995 -D GLS=1 design_out.sm.vg tb.v $(EXTRA_MODS)
	$(SIM) | tee sim.gls.log 2>&1


dot:
	dot *.dot -Tpdf -O
fdp:
	fdp *.dot -Tpdf -O
twopi:
	twopi *.dot -Tpdf -O
circo:
	circo *.dot -Tpdf -O
