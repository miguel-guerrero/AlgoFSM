// wait for condition consuming at least one clock cycle
`define wait1(cond)                  `tick; while(!(cond)) `tick 

// wait for condition consuming 0 or more cycles
`define wait0(cond)                         while(!(cond)) `tick 

// increment a variable (by 1 if amount omitted)
`define incr(x, amnt=1'b1)            x = x + amnt

// use as:
// `loop(i, 0)
//    ... body ...
// `next(i, 10)

`define loop(var, val='b0)            var = val; do begin
`define next(var, limit, inc=1'b1)    var = var + inc; end while(var != limit)
