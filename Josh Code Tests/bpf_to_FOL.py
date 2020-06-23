# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 22:29:46 2020

@author: joshc
"""


"""
So we're trying to come up with some way of codifying how a specific bpf program would be valid on all inputs
This means it has to pass bpf_check.
In bpf_check, it has to follow the following logical route:
    The first two instructions return a specific error code (enomem, for out of memory problems)
    1) is the size of bpf_verifier_ops == 0
    2) is there instruction data fed properly into a bpf_insn_aux_data struct
    3) here there be dragons (Lines 10701 - 10743)
        we're just going to assume all this stuff loaded in properly, cause we don't know what it does yet.
    4) Replace_map_fd_with_map_ptr, env->explored_states are going to be assumed to be true
    5) Check_subprogs
        
Ok, this is getting insane, simplify first to get the hang of z3 with register changes...

        

Round 2!
Simplified Register Recording:
    2 distinct types of register:
        ints (can range from 00 to 99)
        pointers (can range from 100-199)
            By splitting up the allowed values for ptr vs int, can test expected rules without 
            the possiblility of false positives due to one set of rules leaking into the other

    We'll focus on two disctinct registers, called Source and Destination, and make sure that 
        both stay within the bounds described.

    Registers will be described by with the following subproperties:
        int_min (starts at 0)
        int_max (starts at 99)
        ptr_min (starts at 100)
        ptr_max (starts at 199)
        type  (will be either a 1 or a 2, to indicate int type (1) or ptr type (2))
        
    Any program command which changes the min/max value will be modelled by s.add(new constraint)
        but, in reality, we would need to figure out a way to change the constraint already loaded,
        since the internal tree would get gigantic if we keep adding on extraneous nodes to cover 
        int_max changing from 99, to 98, to 97 and so on.

"""

from z3 import *

# Define the variables for ranges and value in the two registers
    # int_value and ptr_value will be the two variables we check as our "inputs"
    # if we have a value for these two which would put it out of the range, will force a false
    
source_type = Int("source_type")

source_int_min = Int("source_int_min")
source_int_max = Int("source_int_max")
source_int_value = Int("source_int_value")

source_ptr_min = Int("source_ptr_min")
source_ptr_max = Int("source_ptr_max")
source_ptr_value = Int("source_ptr_value")

destination_type = Int("destination_type")

destination_int_min = Int("destination_int_min")
destination_int_max = Int("destination_int_max")
destination_int_value = Int("destination_int_value")

destination_ptr_min = Int("destination_ptr_min")
destination_ptr_max = Int("destination_ptr_max")
destination_ptr_value = Int("destination_ptr_value")

# Dunno what I'm going to do with this yet, or if it is even needed.
#  Can we simply use the unsat return to indicate a bad program input?
is_Valid_Program = Bool("is_Valid_Program")

s = Solver()

# Add the basic defined constraints
s.add(source_type == 1)
s.add(source_int_min == 0)
s.add(source_int_max == 99)
s.add(source_ptr_min == 100)
s.add(source_ptr_max == 199)
s.add(source_int_value >= source_int_min)
s.add(source_int_value <= source_int_max)
s.add(source_ptr_value >= source_ptr_min)
s.add(source_ptr_value <= source_ptr_max)

s.add(destination_type == 1)
s.add(destination_int_min == 0)
s.add(destination_int_max == 99)
s.add(destination_ptr_min == 100)
s.add(destination_ptr_max == 199)
s.add(destination_int_value >= destination_int_min)
s.add(destination_int_value <= destination_int_max)
s.add(destination_ptr_value >= destination_ptr_min)
s.add(destination_ptr_value <= destination_ptr_max)

print(s.check())
print(s.model())

