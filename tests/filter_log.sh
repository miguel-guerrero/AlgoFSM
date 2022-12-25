#!/bin/bash

# normalize a log file by removing minor variations in them 
# across behavioral/rtl/gls simulations to simplify comparison

# remove comments | remove VCD dump info | and VCD warnings
grep -v "^#" "$1" | grep -v "^VCD info"  | grep -v "^VCD warning" 
