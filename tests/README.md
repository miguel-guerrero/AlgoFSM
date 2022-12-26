
## Guide to the tests provided in this directory:


* **`motor`**: a simple garage door motor controller (a classic FSM example)

* **`matmul1`**: simple matrix x vector multiplication using nested
              while loops and tasks for memory requests

* **`matmul2`**: as above but using do/while loops and macros for memory requests. Also math in a separate controller to avoid dead cycles (higher throughput)

* **`matmul3`**: as above

* **`for1`**: for loop test (similar to `tpg` set of tests). Exercises 2 nested loops with clocks within.
* **`for2`**: exercises 3 do/while loops nested implementing similar functionality to for loops.
* **`for3`**: simular to `for2` but using macros that make the idea more clear.
* **`for4`**: variation of the macros defined in `for3`

* **`test_seq1`**: Initializes a matrix in memory with a specific pattern using a while loop.
* **`test_seq2`**: Similar to `test_seq1` with 2 nested while loops.

* **`tpg1`**: video test pattern generator, generates syncs and pixels contents
* **`tpg2`**: as above small variation of the timing of the y incfrement
* **`tpg3`**: as above but using a couple of nested for loops instead of do/while's.


Experimental/In-progress:
-------------------------
**`spi-s`**: SPI slave controller
**`ahb-lite-m`**: AHB master controller
