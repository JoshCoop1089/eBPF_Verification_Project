# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 16:03:04 2020

@author: joshc
"""


"""
Given a specific ebpf opcode, how do you take it and model it as an FOL equation 
    to put into z3?

First Thoughts:
    set up bitvec variables to model the values held in a register
    use size 4 bitvecs to test in beginning, can set bitvec size as a variable
        to use different sizes in the future
        
    All bitvecs (for now) will model unsigned values holding numbers representing floats, not pointers
        Reasoning:
            a) simpler to model, no odd sign extensions and shifts to think about at first
            b) forces me to dig into the z3Py function database to find replacements for
                the usual numerical operators, since those are all defined as signed operations

Functions to Model:
    bpf_add
    bpf_left_shift
    bpf_and
    
Register Changes tracked over time:
    set up a 2d list which is created based on number of registers needed
        where every entry in first list will be a history tape for the specific changes to that register
        ie - 
            register_list[0][0] is the inital state of r0
            register_list[1][2] is the state of register r1 after 
                2 changes have been made to it (initial would be in register_list[1][0],
                                                first change in register_list[1][1])
                
    This way, you can maintain a history of register changes, use each individual entry
        as a new bitvec variable in the solver, and possibly trace back to a specific instruction
        which caused a problem
        
    Naming convention on printed output will be r0_0, r0_1, r0_2, ... 
        with incrementing values after the underscore indicating which instruction cause the change
    

bpf_add:
    assumptions:
        adding two positive numbers together
    inputs:
        src register
        dest register
    requirments added to solver:
        dst_new = src + dst
        dst_new >= dst
            this assumption should deal with the overflow problem, 
            since 0xF + 0xF = 0xD  in a 4 bit container (arbitrary chosen size
            for ease of testing, not required by hardcoding), and since we're
            limiting the size, we cannot have events like 0x3+0x11 = 0x4,
            where dst_new would be more than dst_original, even with the overflow,
            since the second number (0x11) wouldn't be allowed in our size 4 bitVec
            
bpf_left_shift:
    assumptions:
        left shift value must be smaller than bit width of register
    inputs:
        single register
    requirments for solver:
        reg_new = reg_old << shift_val
        register_bit_width > shift_val
        reg_new >> shift_val <= reg_new
            this one might get wonky depending on how i implemement the right shift, 
            need to find the unsigned right shift operator function
            

"""
from z3 import *

def check_and_print_model(s, register_list, changes = ""):
    """
    Parameters
    ----------
    s : Type(z3 Solver Object)
        Contains the current model to be evaluated and possibly returned
    
    register_list : Type(List of List of bitVec Variables)
        Holds the current history of changes to registers based on most recent model
        
    changes : TYPE(string)
        Allows for descriptions of test cases. The default is "".
    

    Returns
    -------
    None.
    """
    print("\n" + changes)
    print(s.check())
    
    #Either the model is valid, or I want to see how far the history recorder went before it broke.
    # printing the register list is a error check method for add, but is not required in add_v2
    if s.check() == sat:
        print(s.model())
    else:
        print(register_list)
    print()
        
        
def clear_solver_reset_register_history(solver, numRegs, regBitWidth):
    """
    Purpose: Reset solver, wipe register change history recorder

    Parameters
    ----------
    solver : Type(z3 Solver Object)
        Holds all current FOL considerations, but will be wiped and passed back out of function
    
    numRegs : Type(int)
        Specifies the length of the register_history list of lists

    regBitWidth : Type(int)
        Specifies the size of a BitVector variable in bits for the register history list

    Returns
    -------
    solver : Type(z3 Solver Object)
        A completely reset Solver, no constraints

    reg_list : Type(List of Lists of BitVec variables)
        Clean slate to allow for a look at the progress of a new collection of bpf commands,
        and their effects on register values
    """
    
    # This creates a 2D List to hold all registers and any changes to their values,
    #           and allow for growing sublists related to specific registers
    # The initial state looks like [[r0_0], [r1_0], ..., [rNumRegs_0]], to hold the initial values of
    #       each register, with each individual sublist able to be have future register changes appended
    #       due to changes on that specific register's held values.
    reg_list = [[BitVec("r"+str(i) + "_0", regBitWidth)] 
                  for i in range(numRegs)]
    solver.reset()
    return solver, reg_list


def add_two_registers(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
    """
    Purpose: Given two registers, add their values together and output new constraints to the solver
    
    Parameters
    ----------
    source_reg: Type(int)
        Which register to take the inital value from, referencing the last element in the
        specific sublist of the reg_history list
    
    destination_reg: Type(int)
        Which register to take the second value from, and what sublist to append the 
        result of the computation to
            
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, will be modified due to requirments
        of add and passed back out of function
            
    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous values for all registers in the program, used to allow for 
        SSA representation of register values.  Will be modified with new value for whatever 
        comes out of the add calculation, to be appended to the destination_reg sublist
        
    instruction_counter: Type(int)
        Which instruction of the program is currently being executed, allows for tracing of problematic function calls
        
    register_bit_width: Type(int)
        How large the registers should be

    Returns
    -------
    solver:  Type(z3 Solver Object)
        Modified to include the new value of the destination register, and a overflow check on the calculation
        
    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value.
        --Note--
        The value will be calculated and added to the list regardless of overflow possibilities
            right now, unsure how this will play out in future versions

    """
    #Quick variables to access specific indexes in the register history lists
    # (ie, the most recent versions of the two registers involved in this add)
    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
        
    source_val = reg_history[s_r][s_l-1]
    destination_old_val = reg_history[d_r][d_l-1]
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))  
    destination_new_val = reg_history[d_r][d_l]

    #Adding the two registers, and including the overflow constraint assuming unsigned ints in the register
    solver.add(destination_new_val == destination_old_val + source_val)
    solver.add(UGE(destination_new_val, destination_old_val))
    return solver, reg_history

def add_two_registers_v2(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
    """
    Purpose: Given two registers, add their values together and output new constraints to the solver
    
    v2: Should a specific add cause an overflow, return the instruction counter to cause a break in main program execution
    
    Parameters
    ----------
    source_reg: Type(int)
        Which register to take the inital value from, referencing the last element in the
        specific sublist of the reg_history list
    
    destination_reg: Type(int)
        Which register to take the second value from, and what sublist to append the 
        result of the computation to
            
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, will be modified due to requirments
        of add and passed back out of function
            
    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous values for all registers in the program, used to allow for 
        SSA representation of register values.  Will be modified with new value for whatever 
        comes out of the add calculation, to be appended to the destination_reg sublist
        
    instruction_counter: Type(int)
        Which instruction of the program is currently being executed, allows for tracing of problematic function calls
    
    register_bit_width: Type(int)
        How large the registers should be

    Returns
    -------
    solver:  Type(z3 Solver Object)
        Modified to include the new value of the destination register, and a overflow check on the calculation
        
    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value.
            
    instruction_counter: Type(int)
        This will always return the instruction value of the last correctly completed instruction.
        In the event of an unsat solution, this return will force a check in the main program to halt continuned execution
        by returning the problematic instruction as a negative int (there is a check in the main function for this return
                                                                    always being positive)

    """
    #Quick variables to access specific indexes in the register history lists
    # (ie, the most recent versions of the two registers involved in this add)
    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
    
    source_val = reg_history[s_r][s_l-1]
    destination_old_val = reg_history[d_r][d_l-1]
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    destination_new_val = reg_history[d_r][d_l]
    
    #v2 Change to allow for rollback in event of problematic addition
    """Does having this occur every time the instruction is called, even on valid
    adds, somehow pollute the solver with unneeded checks?  Efficiency question for later."""
    solver.push()  
    
    #Adding the two registers, and including the overflow constraint assuming unsigned ints in the register
    solver.add(destination_new_val == destination_old_val + source_val)
    solver.add(UGE(destination_new_val, destination_old_val))
    
    """I assume this will be horribly inefficient on larger runs of this, but 
    this is my current thought for stopping the program 
    execution when it encounters a problem instruction"""
    
    # v2 Change to always check a solution before returning to the main function
    if solver.check() == unsat:
        # Roll back the solver to a version before the problematic add instructions
        solver.pop()
        
        # Remove the register change because it causes a problem
        throwaway = reg_history[d_r].pop(d_l)
        
        # Special return value to tell the main test program that an error has occured
        instruction_counter *= -1
        
        print("\n\nModel becomes unsat after instruction: " + str(instruction_counter*-1))
        print("Printing the valid model up to, but not including, the broken instruction")
        
    return solver, reg_history, instruction_counter

def left_shift_register_value(source_reg, shift_val, solver, reg_history, instruction_counter, register_bit_width):
    """
    
    Purpose:  Model what occurs when you attempt a left shift on the value stored in source_reg

    Parameters
    ----------
    source_reg : TYPE(int)
        DESCRIPTION. The specific register holding the value in question.  Used to access reg_history list
    
    shift_val : TYPE(int)
        DESCRIPTION. How many bits to shift the value in source_reg
    
    solver : TYPE(z3 Solver Object)
        DESCRIPTION. Current state of the model
    
    reg_history : TYPE(List of List of z3 BitVec variables)
        DESCRIPTION. Keeps track of how many changes have occured on all registers, but not what values are held in the registers
        
    instruction_counter: Type(int)
        Which instruction of the program is currently being executed, allows for tracing of problematic function calls
        
    register_bit_width: Type(int)
        How large the registers should be

    Returns
    -------
    solver : TYPE(z3 Solver Object)
        DESCRIPTION. Current state of the model, after updates from function
    
    reg_history : TYPE(List of List of z3 BitVec variables)
        DESCRIPTION. Keeps track of how many changes have occured on all registers, but not what values are held in the registers
        Added on an additional variable to account for change in source_reg

    """
    s_r = source_reg
    s_l = len(reg_history[s_r])
    
    # Current Value held in register
    old_val = reg_history[s_r][s_l-1]
    
    #Extending the source_register sublist to include the new updated register value
    reg_history[s_r].append(BitVec("r"+str(s_r) + "_" + str(instruction_counter), register_bit_width))  
    new_val = reg_history[s_r][s_l]
    
    # Error Condition which should force the return of the special instruction counter value, to be picked up in main function
    if (shift_val >= register_bit_width):
        print("shift_val is larger than register bit width, Instruction %s invalid"%instruction_counter)
        instruction_counter *= -1
        
    else:
        solver.add(new_val == old_val << shift_val)
        
        #Redundancy check that doing a logical right shift on our new value becomes a smaller number
        # TBH I have no idea what could ever possibly break this condition, but hey, another excuse to scour the z3 docs...
        # this keeps breaking my solver attempts, so i'm going to leave it commented out for now.
        # solver.add(new_val >= LShR(new_val, shift_val))

    return solver, reg_history, instruction_counter
    
def and_two_registers(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
    """
    Purpose: given two registers, do a bitwise and operation and store the result in the register given as the second param

    Parameters
    ----------
    source_reg: Type(int)
        Which register to take the inital value from, referencing the last element in the
        specific sublist of the reg_history list
    
    destination_reg: Type(int)
        Which register to take the second value from, and what sublist to append the 
        result of the computation to
            
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, will be modified due to requirments
        of add and passed back out of function
            
    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous values for all registers in the program, used to allow for 
        SSA representation of register values.  Will be modified with new value for whatever 
        comes out of the add calculation, to be appended to the destination_reg sublist
        
    instruction_counter: Type(int)
        Which instruction of the program is currently being executed, allows for tracing of problematic function calls
    
    register_bit_width: Type(int)
        How large the registers should be

    Returns
    -------
    solver:  Type(z3 Solver Object)
        Modified to include the new value of the destination register, and a logical check on the calculation
        
    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value.
            
    instruction_counter: Type(int)
        This will always return the instruction value of the last correctly completed instruction.
        In the event of an unsat solution, this return will force a check in the main program to halt continuned execution
        by returning the problematic instruction as a negative int (there is a check in the main function for this return
                                                                    always being positive)
    """
    #Quick variables to access specific indexes in the register history lists
    # (ie, the most recent versions of the two registers involved in this add)
    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
    
    source_val = reg_history[s_r][s_l-1]
    destination_old_val = reg_history[d_r][d_l-1]
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    destination_new_val = reg_history[d_r][d_l]
    
    solver.add(destination_new_val == destination_old_val&source_val)
    
    return solver, reg_history, instruction_counter
    
def execute_program(program_list, reg_history):
    s = Solver()
    for instruction_number, instruction in enumerate(program_list):
        s, problem_flag = program_instruction_added(instruction, instruction_number, s)
        if problem_flag < 0:
            print("The last attempted instruction caused a problem")
    check_and_print_model(s, reg_history)
    
