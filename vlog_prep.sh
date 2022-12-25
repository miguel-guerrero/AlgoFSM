#!/bin/bash
# ------------------------------------------------------------------------------
# Apache 2.0. See LICENSE file on root folder.
#
# Copyright (c) 2022-Present Miguel A. Guerrero
#
# Please send bugs and suggestions to: miguel.a.guerrero@gmail.com
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# script that acts as a wraper of icarus verilog to use it as a preprocessor
# it also includes the processing of the macro `tick, which should not be
# replaced by any definition (just left as-is) when undefined
# ------------------------------------------------------------------------------

if [ "$1" == "" ] || [ "$2" == "" ]; then
    echo "Preprocess a SystemVerilog file"
    echo "Usage: $0 src dst [pass_down_options]"
    exit 1
fi

src=$1
dst=$2
shift
shift
args=$*
dst_is_stdout=0

if [ "$dst" == "-" ]; then
    dst_is_stdout=1
    dst=/tmp/vlod_prep.v.$$
fi

ivl=$(which iverilog 2> /dev/null)

if [ -f "$src" ]; then
    if [ -x "$ivl" ]; then
        grep -q __ALGOFSM_TICK__ $src
        if [ $? == 0 ]; then
            echo "Error, file includes reserved __ALGOFSM_TICK__ keyword"
            exit 1
        fi
        $ivl $args -Dtick=__ALGOFSM_TICK__ -I. -I$(dirname $src) -E -o $dst $src
    else
        echo "ERROR: No preprocessor found in path (checked for iverilog)"
        echo "please install or add it to the path"
        exit 1
    fi
    if [ $? != 0 ]; then
        echo "# Error pre-processing $src, skipping it"
        exit 1
    fi
    perl -api -e "s/__ALGOFSM_TICK__/\`tick/g" $dst
else
    echo "# Warning: skipping $src, not found"
    exit 1
fi

if [ "$dst_is_stdout" == "1" ]; then
    cat $dst
    rm -f $dst
fi
