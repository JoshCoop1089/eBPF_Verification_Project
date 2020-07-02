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

"""
"""       
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
        
        --Dunno if i'm going to need/use this idea, but keeping it in comments just in case--
        type  (will be either a 1 or a 2, to indicate int type (1) or ptr type (2))
        
    Any program command which changes the min/max value will be modelled by s.add(new constraint)
        but, in reality, we would need to figure out a way to change the constraint already loaded,
        since the internal tree would get gigantic if we keep adding on extraneous nodes to cover 
        int_max changing from 99, to 98, to 97 and so on.
        
        
****** Big Note! **********
I'm not sure how to handle multiple assignments to the same register over a period of time.
    Using the way I'm currently doing it, i would be adding multiple equivalence statements, which would
    automatically make it unsat.  Current workaround will be resetting the instance every time we do an add/mov'

"""

from z3 import *

# Define the variables for ranges and value in the two registers
    # int_value and ptr_value will be the two variables we check as our "inputs"
    # if we have a value for these two which would put it out of the range, will force a false
    
# source_type = Int("source_type")

source_int_min = Int("source_int_min")
source_int_max = Int("source_int_max")
source_int_value = Int("source_int_value")

source_ptr_min = Int("source_ptr_min")
source_ptr_max = Int("source_ptr_max")
source_ptr_value = Int("source_ptr_value")

# destination_type = Int("destination_type")

destination_int_min = Int("destination_int_min")
destination_int_max = Int("destination_int_max")
destination_int_value = Int("destination_int_value")

destination_ptr_min = Int("destination_ptr_min")
destination_ptr_max = Int("destination_ptr_max")
destination_ptr_value = Int("destination_ptr_value")

s = Solver()

# Setting proper ints for easy changing of baselines
intMin = 0
intMax = 99
ptrMin = 100
ptrMax = 199

def check_And_Print_Model(s, changes = ""):
    print("\n\nChecking new model based on recent changes")
    print("Changes were: " + changes)
    print(s.check())
    if s.check() == sat:
        print(s.model())
        
def reset_To_Basics(s):
    '''
    Function will clear all conditions added to the s solver, 
        and reset it to a set of basic logical and limiting factors.
    Will allow for quick and clean baseline changes
    '''
    # Clear all the added conditions in Solver s
    s.reset()
    
    # Add the basic defined constraints
    # s.add(source_type == 1)
    s.add(source_int_min == intMin)
    s.add(source_int_max == intMax)
    s.add(source_ptr_min == ptrMin)
    s.add(source_ptr_max == ptrMax)
    
    # s.add(destination_type == 1)
    s.add(destination_int_min == intMin)
    s.add(destination_int_max == intMax)
    s.add(destination_ptr_min == ptrMin)
    s.add(destination_ptr_max == ptrMax)
    
    # Logic about the internal values and min/max
    s.add(source_int_max >= source_int_min)
    s.add(source_ptr_max >= source_ptr_min)
    s.add(source_int_value >= source_int_min)
    s.add(source_int_value <= source_int_max)
    s.add(source_ptr_value >= source_ptr_min)
    s.add(source_ptr_value <= source_ptr_max)
    
    s.add(destination_int_max >= destination_int_min)
    s.add(destination_ptr_max >= destination_ptr_min)
    s.add(destination_int_value >= destination_int_min)
    s.add(destination_int_value <= destination_int_max)
    s.add(destination_ptr_value >= destination_ptr_min)
    s.add(destination_ptr_value <= destination_ptr_max)
    
    # Now we have a clean s without any added conditions
    return s

# Initialization of model for sat check
# s = reset_To_Basics(s)
# check_And_Print_Model(s)

# Now we start messing around with the model, should make model unsat
# s.add(source_ptr_value == 300)
# check_And_Print_Model(s)

    
# Checking to see if reset filters out the above unsat
# s = reset_To_Basics(s)
# check_And_Print_Model(s)

    
# Setting the values of a register
def set_Register_Int_Values(s, value, reg):
    
    if(reg == 's'):
        s.add(source_int_value == value)    
    elif(reg == 'd'):
        s.add(destination_int_value == value)
        
    return s

def set_Register_Ptr_Values(s, value, reg):
    
    if(reg == 's'):
        s.add(source_ptr_value == value)
    elif(reg == 'd'):
        s.add(destination_ptr_value == value)
    
    return s
    
        
#Trying to define the bpf_add function
def int_add(s):
    # Prototype would be dst += src
    # How do you extract the values from source and dest ints...
    # Ahha! s.model()[varname]!
    value = s.model()[source_int_value] + s.model()[destination_int_value]
    old_source_int = s.model()[source_int_value]
    
    # This failed the first test (where is was just set_reg by itself without the reset before)
        # because the d_int_val had two competing settings (ie d before, and d after the add)
    s = reset_To_Basics(s)
    
    #Reset the src register to the previously held value for reasons?
    s = set_Register_Int_Values(s, old_source_int, 's')
    s = set_Register_Int_Values(s, value, 'd')
    
    # s = update_register_bounds(s, "int", value)
    return s

# Baby add checks!
s = reset_To_Basics(s)
s = set_Register_Int_Values(s, 1, 's')
s = set_Register_Int_Values(s, 2, 'd')
check_And_Print_Model(s, "setting s_int = 1, d_int = 2")

s = int_add(s)
check_And_Print_Model(s, "adding s_int to d_int, d_int should be 3")

# Breaking int max bound on add check
s = reset_To_Basics(s)
s = set_Register_Int_Values(s, 99, 's')
s = set_Register_Int_Values(s, 99, 'd')
check_And_Print_Model(s, "setting s_int and d_int to 99")

s = int_add(s)
check_And_Print_Model(s, "adding s_int to d_int, should produce unsat since outside intMax range")



#bpf_mov
#pointer arithmetic
def pointer_Offset(s, offset):
    '''
    Changing dst register ptr value based on some defined offset

    Parameters
    ----------
    s : z3 Solver
    offset : int, defined outside function

    Returns
    -------
    s : z3 Solver

    '''
    
    new_ptr = s.model()[destination_ptr_value] + offset
    s = reset_To_Basics(s)
    s = set_Register_Ptr_Values(s, new_ptr, 'd')
    return s

# Checking whether ptr bounds work
s = reset_To_Basics(s)
s = set_Register_Ptr_Values(s, 100, 'd')
check_And_Print_Model(s, "d_ptr = 100")

s = pointer_Offset(s, 5)
check_And_Print_Model(s, "pushing d_ptr up by 5, should give d_ptr = 105")

# Checking negative offsets breaking ptr_min
s = reset_To_Basics(s)
s = set_Register_Ptr_Values(s, 100, 'd')
check_And_Print_Model(s, "d_ptr = 100")

s = pointer_Offset(s, -5)
check_And_Print_Model(s, "pushing d_ptr down by 5, should give unsat, since below ptr_min")

def pointer_pointer_Math(s):
    '''
    Since adding two pointers isn't logical, should return a int in the dst register
    '''
    s_ptr = s.model()[source_ptr_value]
    d_ptr = s.model()[destination_ptr_value]
    new_int = s_ptr+d_ptr
    
    s = reset_To_Basics(s)
    s = set_Register_Ptr_Values(s, s_ptr, 's')
    s = set_Register_Int_Values(s, new_int, 'd')
    
    return s

# Have to change the internal bounds to allow for int number to not freak out on the add
intMin = 100
intMax = 199
ptrMin = 0
ptrMax = 99

# Valid ptr/ptr addition to int
s = reset_To_Basics(s)
s = set_Register_Ptr_Values(s, 55, 's')
s = set_Register_Ptr_Values(s, 55, 'd')
check_And_Print_Model(s, "setting s_ptr and d_ptr to 55")

s = pointer_pointer_Math(s)
check_And_Print_Model(s, "adding two ptrs to get a new d_int value of 110, s_ptr still 55")

# Invalid ptr/ptr addition
s = reset_To_Basics(s)
s = set_Register_Ptr_Values(s, 5, 's')
s = set_Register_Ptr_Values(s, 5, 'd')
check_And_Print_Model(s, "setting s_ptr and d_ptr to 5")

s = pointer_pointer_Math(s)
check_And_Print_Model(s, "adding two ptrs below int_min, so should be unsat")

