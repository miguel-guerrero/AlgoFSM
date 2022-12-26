# AlgoFSM
Make algorithmic (behavioral) style Verilog synthesizable with full control of clock boundaries.


## 1. INTRODUCTION

This tool is capable of generating a synthesizable verilog FSM based on a behavioral description in verilog of the functionality. The input is 
verilog design file where the following state machine declaration has been inserted and once processed by this tool, will be replaced by the generated verilog.
 
    sm_decl :=
        'SmBegin'
             decl+
        'SmForever'
             ...
        'SmEnd'

In what follows we use EBNF notation for the rest of the syntax elements, Ie.

    'terminal'       Represents a terminal expected without the quotes
    :=               Defines a non-terminal on the left-hand side
    []               Indicate enclosing items are optional
    +                One or more repetitions
    item1 item2      Indicates sequencing of items (terminal or not)
    |                Indicates alternatives
 
 The body of each section (represented as `...`) is written in verilog.
 Single line comments `//` style are allowed
 
 The declaration section is used to add `reg` type of variable definitions 
 that can be used on the main functional loop. The syntax for each entry is:
 

    decl := ['local'] ['reg'] [width_decl] var_name ['=' initial_value] ';'

    width_decl := /*empty*/ | '[' integer_expr ':' integer_expr ']'

    varname := VERILOG_IDENTIFIER
 
   - if `local` is specified, the declaration is local to the block generated. `local reg` is equivalent to local
   - if `reg` is speficied, the declaration is made visible outside the block generated to have module scope.

 The `init_value` is used to define the reset value in flops generated.

 `SmForever`/`SmEnd` define the functionality of the block. This block of 
 code is the body of a loop that would repeat forever. This code can be 
 written in sequential / behavioral style, AlgoFSM will unwrap the sequential (non-synthesizable) code into FSM  style RTL that implements the same functionality but is now synthesizable.
 
 The tool can also generate a wrapper for the behvioral code given to allow 
 behavioral simulation. Both representations (behavioral with wrapper and FSM) are equivalent in functionality and can replace each other in a higher level simulation. The FSM representation is the only one synthesizable by 
 conventional tools, whereas the behavioral one is simply a wrapper of the
 code provided by the user (which gets copied verbatim) and is intended to:

 - Allow initial testing / debugging of the intent or algorithm.
 - Provide a golden reference to which the generated synthesizable code
   can be functionally compared against.


## 2. DEPENDENCIES


The tool is written in python3 and tested in MacOs/Linux. Uses only the 
standard python library. Few tools are assumed to be present in order to
allow the tests provided to run.

**`iverilog`**   - verilog simulator which is used also as verilog pre-processor

     MacOS:  brew install icarus-verilog
     Ubuntu: sudo apt-get install iverilog

  if another tools is used as a preprocessor (expand macros `ifdefs etc.
  on the verilog source file) please modify vlog_prep.sh accordingly

optional: **`gtkwave`** (waveform viewer, used only for design debug)

     MacOS:  brew install --cask gtkwave
     Ubuntu: sudo apt-get install gtkwave

optional: **`yosys`** (code synthesizer)

  We use yosys to ensure generated code from FSM (RTL style) is synthesizable.
  To check this, Makefiles have a target (`gls`) that when invoked will run
  RTL simulation, synthesis through yosys into low level equations (no target
  library), Then we run simulation of this representation, and a comparison 
  that the output of both runs for a match (RTL run vs. lower level / gls style)

     MacOS:  brew install yosys
     Ubuntu: sudo apt-get install yosys


## 3. GETTING STARTED

Few examples are given under `tests/` directory. The file `design.v` on each of
them contains a verilog module where at least one `SmBeing/SmEnd` is included.

Under each test/<testname> directory:
 
    $ make
 
 Will generate 2 files:
 
 `out_beh.v` : behavioral code in `design.v` with wrapper logic. Note how an 
             infinite loop with a clock in between iterations has been inserted 
             along with logic to react to reset. This code is simulable by any 
             verilog simulator but not synthesizable. Its main property is that
             its main body is a direct copy of what the user enters between
             `SmForever/SmEnd` without tool transformations, hence ideal to
             iterate on it until the desired behavior is obtained.
 
 `out_sm.v` :  FSM style generated code. Equivalent to `out_beh.v` but is also 
             synthesizable. The style of this FSM is not very conventional but
             is synthesizable.
 
 Note that a clock event (wait for clock edge) is represented with the macro

    `tick; 
 
 on the input representation. This abstraction also handles the possibility of
 a reset at any point of the program input.
 
 The testbench `tb.v` performs a simple test of the code. 
 Executing `make` will run a test for both representations and compare them 
 respective logs among themselves (some tests also perform a built-in check of the result
 in tb.v)

 Multiple state machines can be generated in a single file. Their *id* starts
 with 0 and increments per instance. This *id* is included to all identifiers
 generated by that state machine.


## 4. CONTROL


 The tool provides command line options to define reset name, polarity and
 whether is synchronous or asynchronous with the -rst option.

    ~ prefix indicates active low
    : suffix indicates synchronous


* asynchronous / active low   -> example `"-rst ~rst_n"` (default)
* asynchronous / active high  -> example `"-rst  rst"`

* synchronous / active low    -> example `"-rst ~rst_n:"`
* synchronous / active high   -> example `"-rst  rst:"`
 
 
 Similarly the name of the clock signal and its polarity can be given
 with the -clk option

    ~ prefix indicates active on negedge (reversed polarity)

* active high -> example `"-clk  clk"`
* active low  -> example `"-clk ~clk"`

 An **enable** signal per state machine generated can also be created, so that
 state advances are gated by it. If a signal name is provided with **-ena** option
 e.g. `"-ena sm_enable"` then a signal like `sm_emable0` (where 0 is the instance or
 id number of the sm generated on present file) will be generated to control the advance of the FSM and the user can assing to it the desired logic.
 
 Other options are available to control the name of the following items:

* FSM state variable : `-state <string>`
* Generated block name seed : `-name <string>`
* Prefix for state constants : `-prefix <string>`

 For a description of all the options do: 

      $ algo_fsm.py -help


 The output is FSM style by default. To produce behavioral code with a 
 wrapper, use `-behav` option.

 Full set of command line options (`./algo_fsm.py -h`)

```
    usage: algo_fsm.py [-h] [-out OUT] [-behav] [-clk CLK] [-rst RST] [-ena ENA]
                       [-sd SD] [-prefix PREFIX] [-state STATE] [-name NAME]
                       [-indent INDENT] [-state_suffix STATE_SUFFIX] [-dbg DBG]
                       file

    positional arguments:
      file                  filename of the Input file to process. Give - for
                            stdin

    optional arguments:
      -h, --help            show this help message and exit
      -out OUT              generated output filename (default: /dev/stdout)
      -behav                output is behavioral. By default is synthesizable
                            (default: False)
      -clk CLK              clock signal name. Prefix with ~ for negedge active
                            (default: clk)
      -rst RST              reset signal name. Prefix with ~ for negedge active,
                            suffix with : for sync (default: ~rst_n)
      -ena ENA              if provided the FSM enable will advance controlled by
                            this active high signal (with FSM number appended)
                            (default: )
      -sd SD                if you want a delay for <= assignements, e.g. 1 for
                            #1. Enter 0 for no delay added (default: 0)
      -prefix PREFIX        prefix for localparam state constants (default: SM)
      -state STATE          name of state variable generated (default: state)
      -name NAME            prefix used to derive block name etc. (default:
                            algofsm)
      -indent INDENT        number of spaces used to indent (default: 4)
      -state_suffix STATE_SUFFIX
                            suffix for flopped state variables (default: _r)
      -dbg DBG              debug Level. More detailed for higher numbers
                            (default: 0)
```

## 5. DESCRIPTION OF TESTS DIRECTORY


Description of the files under `tests/<testname>/` directory
All the tests provided follow the same naming convention to allow reusing
the build rules under `common/include.mk`. This is the structure of one/any of
these tests.

* Input files:
  * `Makefile`: mostly an inclusion of `../../common/include.mk` with overrides
  
  * `design.v`: the input design containing at least a `SmBegin/SmEnd` section
  * `tb.v`: test bench for this design

* Generated files:

  * Behavioral
    * `design_out.beh.v`: generated from design.v invoking `algo_fsm.py` with `-behav` option. It generates code that is not synthesizable but that follows user's input verbatim (with appropriate wrappers)
    * `sim.beh.log`: simulation log of running the simulation of `tb.v` and `design_out.beh.v`
    * `tb.beh.vcd`: signal dump of running the simulation of `tb.v` and `design_out.beh.v`

  * RTL
    * `design_out.sm.v`: generated from `design.v` invoking `algofsm.py` without `-behav` option. It generates code that is synthesizable (FMS style) 
    * `sim.sm.log`: simulation log of running the simulation of `tb.v` and `design_out.sm.v`
    * `tb.sm.vcd`: signal dump of running the simulation of `tb.v` and `design_out.sm.v`

  * Gate Level
    * `syn.log`: synthesis log (running `yosys` synthesizer over `design_out.sm.v`)
    * `design_out.sm.vg`: synthesis result (running `yosys` synthesizer over `design_out.sm.v`). We don't target any specific library. this just contains low level equations akin to a gate level netlist
    * sim.gls.log: simulation log of running the simulation of `tb.v` and `design_out.sm.vg`
    * `tb.gls.vcd`: signal dump of running the simulation of `tb.v` and `design_out.sm.vg`

  * `sim.x`: Icarus Verilog compilation output that can be run with icarus `vvp`. Corresponds to the most recent simulation run


## 6. CONTACT

 Please report any bugs along with an input sample file the helps to reproduce 
 the bug and command line used to allow its reproduction to:

    miguel.a.guerrero@gmail.com

 And include `algo_fsm` on the subject line. Suggestions for improvement are most 
 welcome.

