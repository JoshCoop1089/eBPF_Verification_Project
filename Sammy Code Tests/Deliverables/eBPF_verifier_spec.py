# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 16:03:04 2020

@author: Sammy Berger (1pwny)

Given a specific ebpf opcode/program, can we translate how it is analyzed in the verifier
    into a FOL formula?

General Organizational Notes:
    
    Large parts of this code are taken from ../Josh Code Tests/Exploration of z3 ideas/Translate_eBPF_Ops_to_FOL.py
    for consistency's sake, and to ensure that we don't have to effectively work with two different code bases.
    
    The key difference is in what condition we check in the methods. Rather than defining our own "oracle"
    safety condition of what we think is required for an operation to be safe, we attempt to encode what
    verifier.c in the linux kernel requires of the operation.

    We can later check the verifier_safety_condition against the oracle_safety_condition and see if there are discrepancies.

    
"""
from z3 import *

# ---->  Helper Functions for all Operations  <----
def get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg = -1):
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
        result of the computation to.  If used for one register operation, default value of -1

    Returns
    -------
    list_of_values : TYPE(List of z3 bitVector Variables)
        Returns a list made of [source_val, destination_old_val, destination_new_val]
        In the case of a one register operation, source_val and destination_old_val will be the same

    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value, unless
            problem has been encountered, then it will just return the original reg_history without alterations

    """
    # Get the source register names to be used in the solver
    s_r = source_reg
    s_l = len(reg_history[s_r])
    source_val = reg_history[s_r][s_l-1]        #Now holds a bitVec variable to be passed into the solver
    
    # Get the destinaton values
    
    # For Single Register Operations, destination register is the source register
    # Uses the default val from the function to indicate single reg operation
    if destination_reg == -1:
        d_r = s_r
        d_l = s_l
        destination_old_val = source_val
        
    # For Two Register Operations
    else:
        d_r = destination_reg
        d_l = len(reg_history[d_r])
        destination_old_val = reg_history[d_r][d_l-1]

    #Extending the destination register sublist to include the new register name
    # Previous if/else clause was to make this line work for one and two reg operations
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    
    # Since the destination subreg list was extended, d_l, which used to be the length of the old sublist,
        # now references the last element in the extended sublist
    destination_new_val = reg_history[d_r][d_l]
    
    # Formatting the return output for simplicity
    list_of_values = [source_val, destination_old_val, destination_new_val]
    
    return list_of_values, reg_history

# ---->  Single Register Operations  <----
def set_initial_values(source_reg, register_value, solver, reg_history, instruction_counter, register_bit_width):
    """
    Purpose: Force the solver to hold some value for a distinct register.
    
    Parameters
    ----------
    
    source_reg: Type(int)
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
    
    #If you're assigning a value to a register midway through a program it is 
        # an instruction call, and needs a new SSA named register
    if len(reg_history[source_reg]) != 1:
        reg_history[source_reg].append(BitVec("r"+str(source_reg) + "_" + str(instruction_counter), register_bit_width))
    
    s_r = reg_history[source_reg][-1]


    #note: There is no actual operation to 'set' a register in BPF; only to move a value into a register. While this
    #       seems like an inconsequential difference, it means that once BPF_MOV is implemented then we won't need
    #       to have this method at all. For now, the code below approximates the restrictions on a move.

    
    # Checking to make sure an input value will fit inside the chosen register
    # Accounts for max unsigned possible, and min signed possible values for the specified register
    if register_value < 2 ** register_bit_width and register_value >= (-1) * (2 ** (register_bit_width - 1)): 
        solver.add(s_r == register_value)
    else:
        instruction_counter *= -1
    return solver, instruction_counter

def left_shift_register_value():
    #TODO - this method

# ---->  Two Register Operations  <----
def add_two_registers_unsigned():
    #TODO

def add_two_registers_signed():
    #TODO

def and_two_registers():
    #TODO

# ---->  Program Creation, Execution, and Display Operations  <----
def check_and_print_model(s, instruction_list, program_flag):
    """
    Parameters
    ----------
    s : Type(z3 Solver Object)
        Contains the current model to be evaluated and possibly returned

    instruction_list : Type (List of Strings)
        Holds all the instructions given to a specific model to be printed out
        
    program_flag : Type (int)
        Gives the number of the last attempted instruction in the program
    Returns
    -------
    None.
    """
    print("\nThe full program is:")
    for number, ins in enumerate(instruction_list):
        print (str(number) + ":\t" + ins)
        
    if s.check() == sat:
        print("\nThe last instruction attempted was #%s:"%(abs(program_flag)))
        if program_flag == (len(instruction_list) - 1):
            print("Program successfully added all instructions")
        else:
            print("Program didn't successfully add all given instructions")
        print(s.model())
    else:
        """Since we're forcing the main program executor to only pass solver objects 
        which have executed the full program to a point where there is a solution, or 
        stopped just before something caused an unsat to show up, getting to this branch
        would mean you've let a bug slip through one of the instruction sub functions.  
        
        You should probably go find that bug."""
        
        print("You screwed something up if this ever gets printed")
        
    print()

def create_register_list(numRegs, regBitWidth):
    """
    Purpose: Create the register history list used to hold all register changes 
    for SSA naming and assignment scheme

    Parameters
    ----------
    numRegs : TYPE: (int)
        The number of registers the user wishes to model
        
    regBitWidth : TYPE: (int)
        How wide all the registers will be.
        
        --Note--
        Future updates should make the register size independent of this start 
        function, and allow for on the fly reg size changes since SSA allows for each register
        to be created when needed but that's a future me problem

    Returns
    -------
    reg_list : Type(List of Lists of BitVec variables)
        Clean slate to allow for a look at the progress of a new collection of bpf commands,
        and their effects on register values

    """
    
    """This creates a 2D List to hold all registers and any changes to their values,
              and allow for growing sublists related to specific registers
    
    The initial state looks like [[r0_0], [r1_0], ..., [rNumRegs_0]], to hold the initial values of
          each register, with each individual sublist able to be have future register changes appended
          due to changes on that specific register's held values.
          
     The list will be expanded as specific program instructons make changes to certain registers,
     but since it will only add one reg onto one sublist per instruction,
     space complexity is O(numRegs + numInstructionsToProgram)

     Register Changes tracked over time:
        register_list[0][0] is the inital state of r0
        register_list[1][1] is the state of register r1 after a change was made to it
        the Name stored in r_l[1][1] might be r1_3.  This would indicate that the first change made
            on register 1 occured in the 3rd instruction of the program
    ***This doesn't mean that two changes have been made, just that instruction 2 made a change on reg1
                    
    This way, you can maintain a history of register changes, use each individual entry
        as a new bitvec variable in the solver, and possibly trace back to a specific instruction
        which caused a problem

    Naming convention on printed output will be r0_0, r0_1, r0_2, ...
        with incrementing values after the underscore indicating which instruction caused the change
    """      
    reg_list = [[BitVec("r"+str(i) + "_0", regBitWidth)] for i in range(numRegs)]
    
    return reg_list

def program_instruction_added(instruction, instruction_counter, solver, reg_history, register_bit_width):
    """
    Valid Keywords:
        addU -- Add two unsigned values
        addS (not yet implemented) -- Add two signed values
        and -- bitwise and between two values
        lshift -- Left Shift a value a certain amount
        
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
    
    # Instruction String of incorrect form
    if len(string_tokens) != 3:
        print("Imporperly formatted program instruction. Please retype the following:")
        print("-->  " + instruction + "  <--")
        instruction_counter *= -1
        
    # Instruction Form is Correct, checking the individual tokens
    # Not an exhaustive type check on tokens, assuming understanding of instruction input params
    else:
        source_reg = int (string_tokens[1])
        
        # Initializing specific registers to values
        if string_tokens[0] == "init":
            register_start_val = int(string_tokens[2])
            solver, instruction_counter = \
                set_initial_values(source_reg, register_start_val, solver, reg_history, 
                                   instruction_counter, register_bit_width)
        
        # Single Register Operations
        elif string_tokens[0] == "lshift":
            shift_val = int(string_tokens[2])
            solver, reg_history, instruction_counter = \
                left_shift_register_value(source_reg, shift_val, solver, reg_history, 
                                          instruction_counter, register_bit_width)

        # Two Register Operations
        elif string_tokens[0] == "addU" or string_tokens[0] == "addS" or string_tokens[0] == "and":
            destination_reg = int(string_tokens[2])
            
            if string_tokens[0] == "addU":
                solver, reg_history, instruction_counter = \
                    add_two_registers_unsigned(source_reg, destination_reg, solver, reg_history, 
                                               instruction_counter, register_bit_width)
            elif string_tokens[0] == "addS":
                solver, reg_history, instruction_counter = \
                    add_two_registers_signed(source_reg, destination_reg, solver, reg_history, 
                                               instruction_counter, register_bit_width)
            
            elif string_tokens[0] == "and":
                solver, reg_history, instruction_counter = \
                    and_two_registers(source_reg, destination_reg, solver, reg_history, 
                                      instruction_counter, register_bit_width)
        
        # Incorrect Name for Function Call
        else:
            instruction_counter *= -1
            
    return solver, reg_history, instruction_counter

def execute_program(program_list, FOLFunction, reg_history, reg_bit_width):
    """
    Purpose: Executes a given eBPF pretend program using limited keywords

    Parameters
    ----------
    program_list : TYPE(List of Strings)
        Using specific keyword strings, gives the instruction order for the program in question
        
    FOLFunction :  Type(z3 Solver Object)
        Stores all the FOL choices that will be made, to be modified on a per instruction basis
        
    reg_history: Type(List of List of z3 bitVectors variables)
        Holds all previous names for all registers in the program, used to allow for
        SSA representation of register values.  Will be modified with new register name for whatever
        comes out of the calculation, to be appended to the destination_reg sublist
        
    register_bit_width: Type(int)
        Maximum size of the registers

    Returns
    -------
    None.

    """

    # Add instructions from the program list to the solver
    for instruction_number, instruction in enumerate(program_list):
        print("Attempting to combine solver with instruction #%s: %s"%(str(instruction_number), instruction))
        
        FOLFunction, reg_history, problem_flag = \
            program_instruction_added(instruction, instruction_number, FOLFunction, reg_history, reg_bit_width)
        
        # A specific instruction has caused an error in the solver, stop adding, and return
        # the bad instruction and the farthest the model got in finding solutions
        if problem_flag < 0:
            print("\nThe program encountered an error on instruction #%s"%abs(problem_flag))
            print("\t-->  " + program_list[abs(problem_flag)] + "  <--")
            print("The last viable solution before the problem instruction is shown below:")
            break
        
    check_and_print_model(FOLFunction, program_list, problem_flag)

def create_program(program_list = ""):
    """
    Purpose: Start up the ebpf program and see how far it can run.
    Current Default Conditions is 4 registers, each with a bitWidth of 4
    
    Future updates will changes the input structure to a commandline, user input for ease of use
    
    Parameters
    ----------
    
    program_list : Type(List of Strings)
        Using special keyword number string instructions, gives a list of the instructions to be attempted by the solver
        If left blank, will use one of the built in test programs, as opposed to user input

    Returns
    -------
    None.

    """
    
    # Define the number and size of the registers in the program
    # Future update will try and allow for disctinct register sizes and changing of reg sizes based on individual instructions
    # Future update will change this to be defined by user input to cmd line
    num_Regs = 4
    reg_bit_width = 4
    
    # Set up the inital list of registers and z3 solver, to be modified in execute_program
    reg_list = create_register_list(num_Regs,reg_bit_width)
    s = Solver()
    

    """ All individual instructions are a single string of the form:
        'keyword' 'source_register' 'destination_register, shift_val, or initial val'
        
        First keyword is a string identifying the instruction action (addU, and, lshift)
        Second source_reg is an int to say which register will be modifing/contributing a value to the instruction
        Third token is always an int, but its use depends on the first keyword
        
    The example program below cooresponds to the following sequence of instructions:
        0) Set the inital value of register 0 to 1               (init 0 1)   /* r0 = 1*/
        1) Set the inital value of register 1 to 3               (init 1 3)   /* r1 = 3*/
        2) Add the unsigned value of register 0 into register 1  (addU 0 1)   /* r1 += r0*/
        3) Left shift the value of register 1 by 1               (lshift 1 1) /* r1 <<= 1 */
        4) And the values in register 0 and 1, and store in r0   (and 1 0)    /* r0 = r0 & r1 */
        """   
    
    # Arbitrary program to test.  Using specific keyword and dual number pairs will act as ebpf instructions for execute program
    # Future updates will change this to either have a built in example program, or user defined programs able to be added
    if program_list == "":
        program_list =["init 0 1" , "init 1 3", "addU 0 1", "lshift 1 1", "and 1 0"]
    
    execute_program(program_list, s, reg_list, reg_bit_width)
    
def get_eBPF_from_Outside_File():
    """
    How to auto get a bpf program from an input file: Musings of an inexperienced coder
    
    File inputs can be read as a string of characters, so need to identify specific
        patterns which would always show up to indicate a general type of instruction, or
        to show that a block of information is a combination of instructions.
        
    Since Python files using BCC use a block of precoded C code anyway, we can focus on ID'ing patterns in C.
    
    Looking at the code for get-rekt and the sock_examples from Srinivas' github, there is the 
    
        struct bpf_ins prog[] = { 
    
    block of code to indicate the start of what is holding the list of instructions, 
        so we can focus on finding that.
        
    However, there might be variations in the name of the array being used to hold the info, but the 
        "struct bpf_ins" portion would always be there, followed by some letters (prog in this example)
        and then " = {", where there could be an unknown number of spaces in between the end of the name,
        the equal sign and the left open curly brace.  Can just throw that in a regex and not make assumptions
        about the code itself.  
    
    Could we assume the next instance of a } would be the end of the array?  Even if we cannot, we can just push
        left brackets onto a stack and then pop them off when right brackets hit, and that'll tell us when we've
        reached the end of the bpf_ins curly braces
        
    Next challenge: Identifying an individual instruction
        MASSIVE ASSUMPTION TIME!
        All bpf instruction macros in C start with "BPF_" and to make an array in C, you have a comma space 
        seperation, so we could use something like 
        
        string.split(", BPF_") 
        
        to tokenize our specific input string that we found after using the bpf_ins {} search.
        
    Now assuming our instructions have all be split up properly (what a wonderful fantasy world I live in)
        we have to identify what each individual instruction is supposed to do.
        
    Since these are all functions, they have the format of function_name followed by (parameter1, parameter2, ...).  
    So we could again split everything before the parens and everything after, and ID the wording in front of 
        the parens against some hardcoded list of eBPF functions, and then use that to match what all the 
        comma seperated parameters after the parentheses are suppseded to be doing.
        
    We would need to account for any kind of BPF_ token which doesn't fall under the usual list, like BPF_MAP_GET
        in the get-rekt program, which is a shortcut to a defined function elsewhere in the file.
        
        Can we assume that #define would precede any user made functions in this kind of file?
            
    We would need to scan through the imported instruction list, identify any keywords which didn't have a
        definition in our "official" dictionary of eBPF, scan back through the file for a #define BPF_whatever
        and then somehow extract the specific BPF instructions from after that point until 
                                                                                     
                                                                                    
    """
    return 0
