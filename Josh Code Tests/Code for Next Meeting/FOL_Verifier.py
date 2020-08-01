# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 18:25:16 2020

@author: joshc
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 17:52:25 2020

@author: joshc

Summary of BPF Functions:
    add_two_values:
        This is the general function used to implement the various versions of
        the BPF_ADD opcode.  It handles reg/reg, and reg/imm value additions.
        The function also adds in automatic overflow and underflow protection
        every time it is called.  This logic should be extendable to most
        arithmetic functions (SUB, MULT, DIV) with only minor changes.
    
    mov_to_reg:
        Handles the logic of setting a register to a specific value, be it from 
        another register, or passed in as an immediate value.
        
    extend_the_nums:
        This function is the guarantee that any value used inside the model will
        match the size of the register.  If the number is greater than 0, this
        function will zero extend the bitvector representation, and if the original
        value is below 0, it will perform a proper sign extension.
        
    get_the_locations_and_extend:
        This function deals with gathering the names of registers used in other
        calulations, and will automatically check any immediate values passed in
        to see whether they are valid numbers for the specific size of the register
        and also to zero/sign extend any value so it matches the bit size of the
        register.

Ease of Use and Output Functions:
    print_current_register_state:
        Queries the z3 model to find the current values assigned to any register.
        Will report if a register has not been used yet in the current run of the program.
    
    translate_to_bpf_in_c:
        Does an instruction by instruction translation into the C language macros
        used in BPF-Step to allow easier checking of sample programs for output accuracy

"""
import itertools, copy, time
from z3 import *

# Internal representation for one instance of a register
class Register_Info:
    def __init__(self, name, reg_bit_size,  reg_type = ""):
        # Not using this yet, because just dealing with arithmetic on numbers, not pointers
        # self.reg_type = reg_type

        self.name = BitVec(name, reg_bit_size)
        self.reg_name = name 

#Holds all information relevant to one branch of the program
class Individual_Branch:
    def __init__(self, num_Regs, reg_bit_width):
        self.num_Regs = num_Regs
        self.reg_bit_width = reg_bit_width
        self.solver_object = Solver()
        
        # On creation, the following aren't used
        self.register_history = [[]]
        self.instruction_list = [""]
        self.instruction_number = 0
        self.problem_flag = 0
        self.skip_flag = 0
    
    def __str__(self):
        print()
        print("The current contents of this branch are:")
        print("\tRegister Bit Width: %d"%self.reg_bit_width)
        print("\tCurrent Instruction Number is: %d"%self.instruction_number)
        print("\tProblem Flag's Value': %d"%self.problem_flag)
        print("\tThe register history looks like: \n")
        r_h = self.register_history
        for reg in r_h:
            for reg_instance in reg:
                print("\t" + reg_instance.reg_name, end = " ")
            print()
        return "\n"

        
# General helper functions for ease of use
def extend_the_number(value, value_bit_size, register_state_helper):
    """
    If a number is passed into another function that is not the size of the register
        to which it will be assigned, this will extend the BitVec representation 
        of that value to have the correct Bit Width, ie that of the destination register,
        while maintaining signed properties of the original number as needed.

    Parameters
    ----------
    value : TYPE : Int
        The integer representation of the number to be extended
        
    value_bit_size : TYPE : int
        How large the input number was assumed to be before calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    Returns
    -------
    extended_value : TYPE : BitVecValue with a size matching the registers of the program
        The number passed in as "value" turned into a properly sign extended or zero extended BitVector

    """
    valueBV = BitVecVal(value, value_bit_size)
    
    delta_bit_size = register_state_helper.reg_bit_width - value_bit_size
    
    if delta_bit_size > 0:
        if value >= 0:
            extended_value = ZeroExt(delta_bit_size, valueBV)
        else:
            extended_value = SignExt(delta_bit_size, valueBV)
            
    elif delta_bit_size == 0:
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)
                                   
    else:
        print("How did you get this branch to happen? How is your imm value bigger than the reg size of the program?")
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)
        
    return extended_value

def get_the_locations(source_reg, register_state_helper, destination_reg = -1):
    """
    Simplify getting of register names for operations
    
    Parameters
    ----------        
    source_reg : TYPE : int
        Location where data will taken from before calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    destination_reg : TYPE : int, optional
        Location where data will be stored after calculation if dealing with a two register operation

    Returns
    -------
    list_of_locations : TYPE : List of BitVector Objects
        # list_of_locations = [source_val, destination_old_val, destination_new_val]
        Information specifying what locations will need to be used in the main formulas
    
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """    
    r_s_h = register_state_helper
    s_r = source_reg
    source_val = r_s_h.register_history[s_r][-1].name        
    
    
    # For Single Register Operations, destination register is the source register
    # Uses the default val from the function to indicate single reg operation
    if destination_reg == -1:
        d_r = s_r
        destination_old_val = source_val
    else:
        d_r = destination_reg
        destination_old_val = r_s_h.register_history[d_r][-1].name

    r_s_h.register_history[d_r].append(\
               Register_Info("r%d_%d"%(d_r, r_s_h.instruction_number),\
                             r_s_h.reg_bit_width))
    
    destination_new_val = r_s_h.register_history[d_r][-1].name
    
    # Formatting the return output for simplicity
    list_of_locations = [source_val, destination_old_val, destination_new_val]
    
    return list_of_locations, r_s_h

def get_the_locations_and_extend(input_value, target_reg, register_state_helper, source_reg, extension_length):
    """
    Sets up properly sized inputs and returns the register locations to put them

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    list_of_locations : TYPE : List of BitVector Objects
        # list_of_locations = [source_val, destination_old_val, destination_new_val]
        Information specifying what locations will need to be used in the main formulas
        If function called on a outside value (imm4, imm8 variants) source_val will 
        hold a BitVecVal constant, not a named register location
    
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instructon

    """
    r_s_h = register_state_helper
    
    # Two Register Operation
    if source_reg:
        list_of_locations, r_s_h = get_the_locations(input_value, r_s_h, target_reg)
    
    # Adding an imm value to a register
    else:
        list_of_locations, r_s_h = get_the_locations(target_reg, r_s_h)
        
        # Check that any imm value can fit inside the bit size of the register, 
        # because z3 extend functions also auto apply a modulo operator to force the fit
        # and that defeats the purpose of limiting the bitsize
        if input_value > 2 ** (r_s_h.reg_bit_width - 1) - 1 or input_value < -1 * (2 ** (r_s_h.reg_bit_width - 1)):
            r_s_h.problem_flag = r_s_h.instruction_number * -1
        
        else:
            if extension_length != 0:
                list_of_locations[0] = extend_the_number(input_value, extension_length, r_s_h)
            else:
                list_of_locations[0] = BitVecVal(input_value, r_s_h.reg_bit_width)
                
    return list_of_locations, r_s_h

# Add Instructions
def add_two_values(input_value, target_reg, register_state_helper, source_reg, extension_length):
    """
    Generic function to combine two numbers and check for overflows    

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    add_function : Type : z3 equation
        Holds the combination of all constraints due to the add instruction
        
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper

    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    output_function = list_of_locations[2] == list_of_locations[1] + list_of_locations[0]
    
    no_overflow = BVAddNoOverflow(list_of_locations[0], list_of_locations[1], True)
    no_underflow = BVAddNoUnderflow(list_of_locations[0], list_of_locations[1])
    
    add_function = And(output_function, no_overflow, no_underflow)
    
    return add_function, r_s_h

def mov_to_reg(input_value, target_reg, register_state_helper, source_reg, extension_length):
    """
    Generic function to move a value into a register    

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    mov_function : Type : z3 equation
        Holds the combination of all constraints due to the mov instruction
        
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h

def jump_command(input_value, target_reg, offset, register_state_helper, source_reg, extension_length):
    """
    Generic function to execute the two paths of a jump instruction    

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    offset : Type : Int
        How many instructions to jump if the comparison fails
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    jump_constraints : Type : z3 equation
        Holds the combination of all constraints due to the jump instruction, the execution
        of the branches, and the combination of the paths after
        
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    del r_s_h.register_history[target_reg][-1]
    
    # This is specifically for jumps with equality, but should be modularized to deal with different jump conditions
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    comparison_statement = list_of_locations[0] == list_of_locations[1]
    
    next_ins = r_s_h.instruction_number + 1
    next_ins_with_offset = next_ins + offset

    before_jump_reg_names = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    
    # Execute all the instructions between jump and offset
    jump_constraints = True
    for instruction_number, instruction in enumerate(r_s_h.instruction_list[next_ins:next_ins_with_offset], next_ins):
        
        # A jump command has independently executed some instructions, do not execute this instruction
        if register_state_helper.skip_flag > instruction_number:
            continue
        
        r_s_h.instruction_number += 1
        instruction_constraints , r_s_h = \
            create_new_constraints_based_on_instruction_v2(r_s_h.instruction_list[instruction_number], register_state_helper)
        jump_constraints = And(instruction_constraints, jump_constraints)
    
    after_branch_reg_names = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    
    # Create a new instance of every register, using an if then else clause to assign it the value based on which branch was taken
    for reg_number, reg_list in enumerate(r_s_h.register_history):
        
        # The register hasn't been initalized yet
        if len(reg_list) == 1:
            continue
        
        name = f'r{reg_number}_{next_ins_with_offset}_after_jump'
        reg_list.append(Register_Info(name, r_s_h.reg_bit_width))
        
        # If (compare, is_true, is_false)
        name_constraints = If(comparison_statement, reg_list[-1].name == after_branch_reg_names[reg_number].name,\
                              reg_list[-1].name == before_jump_reg_names[reg_number].name)
        
        jump_constraints = And(name_constraints, jump_constraints)

    r_s_h.skip_flag = max(next_ins_with_offset, r_s_h.skip_flag)

    return jump_constraints, register_state_helper

def exit_instruction(register_state_helper):
    exit_ins = Bool("exit_%d"%(register_state_helper.instruction_number))
    return exit_ins, register_state_helper 

# Program Setup and Output Functions
def check_and_print_model(register_state_helper):
    """
    Parameters
    ----------
    register_state_helper: Type : Individual_Branch
        Contains the solver object, program instructions, and problem flag information
    Returns
    -------
    None.
    """
    s = register_state_helper.solver_object
    instruction_list = register_state_helper.instruction_list
    problem_flag = register_state_helper.problem_flag
    if problem_flag == 0:
        problem_flag = register_state_helper.instruction_number
    
    if s.check() == sat:
        print("\nThe last instruction attempted was #%d:\n"%(abs(problem_flag)))
        if problem_flag == (len(instruction_list) - 1):
            print("Program successfully added all instructions")
        else:
            print("Program didn't successfully add all given instructions")
        print("The stored model contains the following variable states")
        print(s.model())
    else:
        """Since we're forcing the main program executor to only pass solver objects 
        which have executed the full program to a point where there is a solution, or 
        stopped just before something caused an unsat to show up, getting to this branch
        would mean you've let a bug slip through one of the instruction sub functions.  
        
        You should probably go find that bug."""
        
        print("You screwed something up if this ever gets printed")
    
    print_current_register_state(register_state_helper)
    print()
    
def print_current_register_state(register_state_helper):
    """
    Quick print function to return the most recent values stored in each register
    """
    print()
    
    r_s_h = register_state_helper
    r_s_h.solver_object.check()
    current_reg_states = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    print("The register values are currently:")
    for j, register in enumerate(current_reg_states):
        print("\tRegister %d:\t"%j, end = " ")
        if "start" in register.reg_name:
            print("Not Initalized")
        else:
            try:
                print(r_s_h.solver_object.model()[register.name])
            except Z3Exception:
                print("oops, z3 said nope! wonder why...")
    print()

def translate_to_bpf_in_c(program_list):
    """
    Simplify the testing of a program in bpf_step using our current accessible keywords
        and the libbpf.h functions.  No error checking added, assuming formating of input strings
        is valid.
        
    This function will output a list of strings containing the translated versions ready to be
        copied right into sock_example.c
        
    Example:
        program_list =
        	0:	movI8 4 1
        	1:	movI8 3 2
        	2:	addR 1 2
        	3:	jneI8 5 2 2
        	4:	addR 1 1
        	5:	addI4 3 2
        	6:	addR 1 2
        	7:	addR 2 1
        	8:	exit 0 0
        
        would print the following to the console:
            
            BPF_MOV64_IMM(BPF_REG_1, 4), BPF_MOV64_IMM(BPF_REG_2, 3), 
            BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1), BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 5, 2), 
            BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1), BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, 3), 
            BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1), BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2), 
            BPF_EXIT_INSN(), 
    """
    print("The full program in Python keyword format is:\n")
    for number, ins in enumerate(program_list):
        print ("\t"+ str(number) + ":\t" + ins)
    
    output = ""

    for instruction in program_list:
        split_ins = instruction.split(" ")
        keyword = split_ins[0]
        value = split_ins[1]
        target_reg = split_ins[2]
        
        if len(split_ins) == 3:
        # Add Instuctions
            if keyword == "addI4":
                instruction = f'BPF_ALU32_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addI8":
                instruction = f'BPF_ALU64_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addR":
                instruction = f'BPF_ALU64_REG(BPF_ADD, BPF_REG_{target_reg}, BPF_REG_{value})'
            
        # Mov Instructions
            elif keyword == "movI4" or keyword == "movI8":
                instruction = f'BPF_MOV64_IMM(BPF_REG_{target_reg}, {value})'
            elif keyword == "movR":
                instruction = f'BPF_MOV64_REG(BPF_REG_{target_reg}, BPF_REG_{value})'

        # Exit command
            elif keyword == "exit":
                instruction = "BPF_EXIT_INSN()"

        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            
            if keyword == "jneI4" or keyword == "jneI8":
                instruction = f'BPF_JMP_IMM(BPF_JNE, BPF_REG_{target_reg}, {value}, {offset})'
            elif keyword == "jneR":
                instruction = f'BPF_JMP_REG(BPF_JNE, BPF_REG_{target_reg}, BPF_REG_{value}, {offset})'
        
        output += instruction + ", "
    
    print("\nThis program would be written as the following for BPF in C:\n")        
    print(output)
    
def create_register_list(numRegs, register_state_helper):
    """
    Purpose: Create the register history list used to hold all register changes 
    for SSA naming and assignment scheme

    Parameters
    ----------
    numRegs : TYPE: (int)
        The number of registers the user wishes to model
        
    register_state_helper : Type (Individual_Branch)
        generic container holding program variables for referencing

    Returns
    -------
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction
        
    --------------------------------
    This creates a 2D List to hold info about the names and types of registers,
              and allow for growing sublists related to specific registers
    
    The initial state looks like [[r0_start], [r1_start], ..., [rNumRegs_start]], to hold the initial named objects
        containing info about each register, with each individual sublist able to be have future register
        changes appended due to changes on that specific register's held values.
          
     The list will be expanded as specific program instructons make changes to certain registers,
         but since it will only add one reg onto one sublist per instruction,
         space complexity is O(numRegs + numInstructionsToProgram)

     Register Changes tracked over time:
        register_list[0][0] is the inital state of r0 (ie uninitialized, but availible to be used)
        register_list[1][1] is the name of the state of register r1 after a change was made to it
            the name stored in register_list[1][1] might be r1_3.  This would indicate that the first
            change made on register 1 occured in the 3rd instruction of the program
    ***This doesn't mean that three changes have been made, just that instruction 3 made the first change on reg1
                    
    This way, you can maintain a history of register changes, use each individual entry
        as a new bitvec variable in the solver, and possibly trace back to a specific instruction
        which caused a problem
    """      
    register_state_helper.register_history = \
        [[Register_Info("r"+str(i) + "_start", register_state_helper.reg_bit_width)] for i in range(numRegs)]
    
    return register_state_helper  

def incorrect_instruction_format(instruction, register_state_helper):
    """
    Formating error occured when trying to read an instruction in create_new_constraints

    Parameters
    ----------
    instruction: Type : String
        Specific keyword sequence to indicate which instruction, and what values, are to be used
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program

    Returns
    -------
    new_constraints : Type : z3 equation
        Poision pill constraint to force solver to unsat
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction
    """
    print("\nIncorrect instruction format for instruction number: %d"%register_state_helper.instruction_number)
    print("Please retype the following instruction: \n\t-->  %s  <--"%instruction)
    register_state_helper.problem_flag = register_state_helper.instruction_number * -1
    new_constraints = False
    
    return new_constraints, register_state_helper
   
def create_new_constraints_based_on_instruction_v2(instruction, register_state_helper):
    """
    Parameters
    ----------
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_list, instruction_counter, problem_flag information,
        and bit_size for the registers on this specific branch of the program
   
    Returns
    -------
    new_constraints : TYPE : z3 Boolean
        Collection of new conjunctions to use with the main function
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction
        
    ------------------------
    Keywords added so far:
        mov Commands:               movI4 / movI8 / movR
        add Commands:               addI4 / addI8 / addR
        Jump if not equal Commands: jneI4 / jneI8 / jneR
        exit Command:               exit
        
    Keyword format for add/mov/exit (3 space seperated tokens):
        (treated as a string)   first: instruction name
        (treated as an int)     second: either the imm value or the source register location
        (treated as an int)     third: target register to be changed
        
    Keyword format for jump (4 space seperated tokens):
        (treated as a string)   first: instruction name
        (treated as an int)     second: either the imm value or the source register location
        (treated as an int)     third: register location to be compared against
        (treated as an int)     fourth: offset of instructions if comparison fails

    ***Will probably need to rewrite this depending on additions/changes to the basic instruction set***
    """
    
    print("Attempting to combine solver with instruction #%d: %s"%(register_state_helper.instruction_number, instruction))



    split_ins = instruction.split(" ")
    
    if len(split_ins) < 3 or len(split_ins) > 4:
        new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)

    else:
        keyword = split_ins[0]
        value = int(split_ins[1])
        target_reg = int(split_ins[2])
        
        # Format for add, mov, and exit commands
        if len(split_ins) == 3:
            
            # Add Instuctions
            if keyword == "addI4":
                new_constraints, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 4)
            elif keyword == "addI8":
                new_constraints, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 0)
            elif keyword == "addR":
                new_constraints, register_state_helper = add_two_values(value, target_reg, register_state_helper, True, 0)
            
            # Mov Instructions
            elif keyword == "movI4":
                new_constraints, register_state_helper = mov_to_reg(value, target_reg, register_state_helper, False, 4)
            elif keyword == "movI8":
                new_constraints, register_state_helper = mov_to_reg(value, target_reg, register_state_helper, False, 0)
            elif keyword == "movR":
                new_constraints, register_state_helper = mov_to_reg(value, target_reg, register_state_helper, True, 0)
                
            # Exit command
            elif keyword == "exit":
                new_constraints, register_state_helper = exit_instruction(register_state_helper)
             
            # Keyword doesn't match known functions
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)

                
        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            
            if keyword == "jneI4":
                new_constraints , register_state_helper = \
                    jump_command(value, target_reg, offset, register_state_helper, False, 4)
            elif keyword == "jneI8": 
                new_constraints , register_state_helper = \
                    jump_command(value, target_reg, offset, register_state_helper, False, 0)
            elif keyword == "jneR": 
                new_constraints , register_state_helper = \
                    jump_command(value, target_reg, offset, register_state_helper, True, 0)
         
            # Keyword doesn't match known functions
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)
    # Debugging helpers
    # print(register_state_helper)
    # print_current_register_state(register_state_helper)    
    return new_constraints, register_state_helper

def execute_program_v2(register_state_helper):
 
    for instruction_number, instruction in enumerate(register_state_helper.instruction_list):
        register_state_helper.instruction_number = instruction_number
        
        # A jump command has independantly executed some instructions, do not execute this instruction
        if register_state_helper.skip_flag > instruction_number:
            continue
        
        new_constraints, register_state_helper = \
            create_new_constraints_based_on_instruction_v2(instruction, register_state_helper)
        
        # Special register_state_helper.problem_flag returns:
            # problem_flag < 0 --> an instruction caused an unsat solution
            # problem_flag > instruction_number --> a jump instruction is pushing the list forward
        
        register_state_helper.solver_object.push()
        register_state_helper.solver_object.add(new_constraints)
                
        # Debug just in case
        # print(register_state_helper)

        if register_state_helper.solver_object.check() == unsat:
            
            register_state_helper.solver_object.pop()
            register_state_helper.problem_flag = register_state_helper.instruction_number * -1
            
            if register_state_helper.instruction_number == 0:
                register_state_helper.problem_flag = -1

        if register_state_helper.problem_flag < 0:
            print("\nThe program encountered an error on instruction #%s"%abs(register_state_helper.problem_flag))
            print("\t-->  " + register_state_helper.instruction_list[abs(register_state_helper.problem_flag)] + "  <--")
            print("The last viable solution before the problem instruction is shown below:")
            break
        
    # Enable this for outputs from egregiously long programs so you don't get the full program printouts
    # print_current_register_state(register_state_helper)
        
    # The usual prinouts, for non insanely long programs
    check_and_print_model(register_state_helper)
    translate_to_bpf_in_c(register_state_helper.instruction_list)    
          
def create_program(program_list = "", num_Regs = 4, reg_bit_width = 8):
    """
    Purpose: Start up the ebpf program, see how far it can run, and what the end results are
    
    Parameters
    ----------
    program_list : Type(List of Strings)
        Using special keyword number string instructions, gives a list of the instructions to be attempted by the solver
        If left blank, will use built in test program, as opposed to user input
        
    num_Regs : Type : Int
        Defines how many registers the program has access to.  Default value is 4
        
    reg_bit_width : Type : Int
        Defines how large each register is.  Default value is 8 bits

    Returns
    -------
    None.

    ***Description of valid keywords in create_new_constraints_based_on_instruction_v2***
    """   
    start_time = time.time()
    if program_list == "":
        program_list = ["movI8 4 1", "movI8 3 2", "addR 1 2", "jneI8 5 2 2", "addR 1 1", "addI4 3 2", "addR 1 2", "addR 2 1", "exit 0 0"]
    
    # Setting up the container for holding register history, register sizes, and instruction counter
    register_state_helper = Individual_Branch(num_Regs, reg_bit_width)
    register_state_helper = create_register_list(num_Regs, register_state_helper)
    register_state_helper.instruction_list = program_list
    
    execute_program_v2(register_state_helper)    
    end_time = time.time()
    print('\n\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))