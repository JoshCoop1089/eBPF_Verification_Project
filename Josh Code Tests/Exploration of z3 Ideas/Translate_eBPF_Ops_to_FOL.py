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

def check_and_print_model(s, register_list = "", changes = "", instruction_list = "", problem_flag = 0):
    """
    Parameters
    ----------
    s : Type(z3 Solver Object)
        Contains the current model to be evaluated and possibly returned

    register_list : Type(List of List of bitVec Variables)
        Holds the current history of changes to registers based on most recent model

    changes : TYPE(string)
        Allows for descriptions of test cases. The default is "".

    instruction_list : Type (List of Strings)
        Holds all the instructions given to a specific model, either to be printed out,
        or referenced in case of problematic instruction
        
    problem_flag : Type(int)
        A return value from all functions indicating that an error has occured, will be
        a positive number cooresponding to the instruction which caused the error
        
    Returns
    -------
    None.
    """
    print("\n" + changes)
    
    print("The proposed program is: \n")
    for number, ins in enumerate(instruction_list):
        print (str(number) + ":\t" + ins)
        
        
    s.check()    
    if not problem_flag:
        print("The program completed, and found the following solution:")
    else:
        print("The program encountered an error on instruction%s"%problem_flag)
        if problem_flag >= len(instruction_list):
            print("How is this even possible? What?")
        else:
            print(instruction_list[problem_flag])
            print("The last viable solution to the program before the problem instruction was:")
    print(s.model())
        
    # Old code to support add v1, will probably just delete when i clean up add test suite
    
    # #Either the model is valid, or I want to see how far the history recorder went before it broke.
    # # printing the register list is a error check method for add, but is not required in add_v2
    # if s.check() == sat:
    #     print(s.model())
    # else:
    #     print(register_list)
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

def get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg = 0):
    """
    Purpose: Simplify getting of register names for operations
    
    Parameters
    ----------
    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous names for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new register name for whatever
        comes out of the calculation, to be appended to the destination_reg sublist

    instruction_counter: Type(int)
        Which instruction of the program is currently being executed, allows for tracing of problematic function calls

    register_bit_width: Type(int)
        How large the registers should be
    
    source_reg: Type(int)
        Which register to take the inital value from, referencing the last element in the
        specific sublist of the reg_history list

    destination_reg: Type(int), optional
        Which register to take the second value from, and what sublist to append the
        result of the computation to.  If used for one register operation, default value of 0

    Returns
    -------
    list_of_values : TYPE(List of z3 bitVector Variables)
        Returns a list made of [source_val, destination_old_val, destination_new_val]
        In the case of a one register operation, source_val and destination_old_val will be the same

    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value, unless
            problem has been encountered, then it will just return the original reg_history without alterations

    """
    # Get the source values to be messed with
    s_r = source_reg
    s_l = len(reg_history[s_r])
    source_val = reg_history[s_r][s_l-1]
    
    # Get the destinaton values
    # For Single Register Operations, destination register is the source register
    if destination_reg == 0:
        d_r = s_r
        d_l = s_l
        destination_old_val = source_val
        
    # For Two Register Operations
    else:
        d_r = destination_reg
        d_l = len(reg_history[d_r])
        destination_old_val = reg_history[d_r][d_l-1]

    #Extending the destination register sublist to include the new updated register value
    # Previous if/else clause was to make this line work for one and two reg operations
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    destination_new_val = reg_history[d_r][d_l]
    
    # Formatting the return output for simplicity
    list_of_values = [source_val, destination_old_val, destination_new_val]
    
    return list_of_values, reg_history

def add_two_registers_unsigned(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
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
        Holds all previous names for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new register name for whatever
        comes out of the calculation, to be appended to the destination_reg sublist
   
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
    list_of_nums, reg_history = get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg)
    
    #v2 Change to allow for rollback in event of problematic addition
    """Does having this occur every time the instruction is called, even on valid
    adds, somehow pollute the solver with unneeded checks?  Efficiency question for later."""
    solver.push()

    #Adding the two registers, and including the overflow constraint assuming unsigned ints in the register
    # list_of_nums = [source_val, destination_old_val, destination_new_val]
    solver.add(list_of_nums[2] == list_of_nums[1] + list_of_nums[0])
    solver.add(UGE(list_of_nums[2], list_of_nums[1]))

    """I assume this will be horribly inefficient on larger runs of this, but
    this is my current thought for stopping the program
    execution when it encounters a problem instruction"""

    # v2 Change to always check a solution before returning to the main function
    if solver.check() == unsat:
        # Roll back the solver to a version before the problematic add instructions
        solver.pop()

        # Remove the register update because it causes a problem
        del reg_history[destination_reg][-1]

        # Special return value to tell the main test program that an error has occured
        instruction_counter *= -1

        # print("\n\nModel becomes unsat after instruction: " + str(instruction_counter*-1))
        # print("Printing the valid model up to, but not including, the broken instruction")

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

    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous names for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new register name for whatever
        comes out of the calculation, to be appended to the destination_reg sublist
    
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
    #Quick variables to access specific indexes in the register history lists
    list_of_nums, reg_history = get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg)

    # Error Condition which should force the return of the special instruction counter value, to be picked up in main function
    if (shift_val >= register_bit_width):
        print("shift_val is larger than register bit width, Instruction %s invalid"%instruction_counter)
        instruction_counter *= -1

    else:
        # list_of_nums = [source_val, destination_old_val, destination_new_val]
        solver.add(list_of_nums[2] == list_of_nums[1] << shift_val)

        #Redundancy check that doing a logical right shift on our new value becomes a smaller number
        # TBH I have no idea what could ever possibly break this condition, but hey, another excuse to scour the z3 docs...
        # this keeps breaking my solver attempts, so i'm going to leave it commented out for now.
        # solver.add(new_val >= LShR(new_val, shift_val))

    return solver, reg_history, instruction_counter

def and_two_registers(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
    """
    Purpose: given two registers, do a bitwise and operation and store the result 
        in the register given as the second param

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
        Holds all previous names for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new register name for whatever
        comes out of the calculation, to be appended to the destination_reg sublist

    instruction_counter: Type(int)
        Which instruction of the program is currently being executed, allows for tracing 
        of problematic function calls

    register_bit_width: Type(int)
        How large the registers should be

    Returns
    -------
    solver:  Type(z3 Solver Object)
        Modified to include the new value of the destination register, and a logical
        check on the calculation

    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value.

    instruction_counter: Type(int)
        This will always return the instruction value of the last correctly completed instruction.
        In the event of an unsat solution, this return will force a check in the main program to halt continuned execution
        by returning the problematic instruction as a negative int (there is a check in the main function for this return
                                                                    always being positive)
    """
    #Quick variables to access specific indexes in the register history lists
    # (ie, the most recent versions of the two registers involved in this and)
    list_of_nums, reg_history = get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg)

    # list_of_nums = [source_val, destination_old_val, destination_new_val]
    solver.add(list_of_nums[2] == list_of_nums[1]&list_of_nums[0])

    return solver, reg_history, instruction_counter

def set_initial_values(source_reg, register_value, solver, instruction_counter, register_bit_width):
    """
    Purpose: Force the solver to hold some initial value for a distinct register.
    
    Parameters
    ----------
    
    source_reg: Type(z3 bitVec Variable)
        Which register is being assigned a starting value
        
    register_value: Type(int)
        Value being assigned to source_reg
        
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, will be modified to hold the starting conditions
        
    instruction_counter: Type(int)
        Which instruction in the program is being attempted

    register_bit_width: Type(int)
        Maximum size of the registers
        
    Returns
    -------
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, modified to hold the starting conditions of the specified register
    """
    
    if register_value < 2 ** register_bit_width: 
        solver.add(source_reg == register_value)
    else:
        instruction_counter *= -1
    return solver, instruction_counter

def program_instruction_added(instruction, instruction_counter, solver, reg_history, register_bit_width):
    """
    Valid Keywords:
        addU
        addS (not yet implemented)
        and
        lshift
        
    Purpose: Allow for modular additions to the solver using limited keywords and typing time

    Parameters
    ----------
    instruction : TYPE: (string)
        Specially formatted string to indicate a step in the designated full program
        
    instruction_counter : Type (int)
        Which step in the program is being added
        
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, will be modified due to requirments
        of specific instruction and passed back out of function

    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous values for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new value for whatever
        comes out of the add calculation, to be appended to the destination_reg sublist

    register_bit_width: Type(int)
        How large the registers should be

    Returns
    -------
    solver: Type(z3 Solver Object)
        Stores all the FOL choices made so far, modified due to requirments
        of specific instruction
        
    instruction_counter: Type(int)
        Will either be a positive number indicating the attempted operation was added to 
        the solver successfully, or the negative value of the instruction which failed

    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous values for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new value for whatever
        comes out of the add calculation, to be appended to the destination_reg sublist

    """
    string_tokens = instruction.split(" ")
    
    # Correctly implemented instructions would have three tokens,
    #   0 -> instruction name, 1 -> source reg, 2 -> destination reg, shift value, or init value
    
    # Instruction String of incorrect Length
    if len(string_tokens) != 3:
        instruction_counter *= -1
        
    # String Length is Correct, checking the individual tokens
    else:
        source_reg = string_tokens[1]
        
        # Initializing specific registers to values
        if string_tokens[0] == "init":
            register_start_val = string_tokens[2]
            solver, instruction_counter = set_initial_values(source_reg, register_start_val, solver, instruction_counter, register_bit_width)
        
        # Single Register Operations
        elif string_tokens[0] == "lshift":
            shift_val = string_tokens[2]
            solver, reg_history, instruction_counter = left_shift_register_value(source_reg, shift_val, solver, reg_history, instruction_counter, register_bit_width)

        # Two Register Operations
        elif string_tokens[0] == "addU" or string_tokens[0] == "addS" or string_tokens[0] == "and":
            destination_reg = string_tokens[2]
            
            if string_tokens[0] == "addU":
                solver, reg_history, instruction_counter = add_two_registers_unsigned(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width)
            
            elif string_tokens[0] == "and":
                solver, reg_history, instruction_counter = and_two_registers(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width)
        
        # Incorrect Name for Function Call
        else:
            instruction_counter *= -1
            
    return solver, instruction_counter, reg_history

def execute_program(program_list, FOLFunction, reg_history):

    # Add instructions from the program list to the solver
    for instruction_number, instruction in enumerate(program_list):
        FOLFunction, problem_flag, reg_history = program_instruction_added(instruction, instruction_number, FOLFunction, reg_history, reg_bit_width)
        
        # A specific instruction has caused an error in the solver, stop adding, and return
        # the bad instruction and the farthest the model got in finding solutions
        if problem_flag < 0:
            problem_flag *= -1
            print("The last attempted instruction caused a problem.")
            print("The problem instruction was:\n" \
                  + program_list[problem_flag])
            print("Displaying the model up to just before the instruction.")
            break
    check_and_print_model(FOLFunction, reg_history)

def create_program():
    