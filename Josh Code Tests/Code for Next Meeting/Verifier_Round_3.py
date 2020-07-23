# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 17:52:25 2020

@author: joshc
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 15:38:07 2020

@author: joshc
"""

"""
Thursday Meeting Plan

1) Create sample eBPF program as guide
    -- Program has the following elements finished--
    a) Register to Register Addition (signed values)
    b) Immediate to Register Addition (signed values)
    c) Setting one register to the value of another register
    d) Setting a register to an immediate value

        --Since we need to account for values that might not be the full size of the register, 
        we can use the ZeroExt() and SignExt() z3 functions to fill the register in if needed
    
    -- In progress -- 
    e) Branching
        -- Using JNE, split the possible function conditions
        -- One branch will have an early exit condition
"""
import itertools, copy
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
        self.branch_number = 0
    
    def __str__(self):
        print("The current contents of the helper_bundle are:")
        print("\tRegister Bit Width: %d"%self.reg_bit_width)
        print("\tThe Current Instruction Number is: %d"%self.instruction_number)
        print("\tProblem Flag's Value is': %d"%self.problem_flag)
        print("\tThe register history looks like: \n")
        r_h = self.register_history
        for reg in r_h:
            for reg_instance in reg:
                print("\t" + reg_instance.reg_name, end = " ")
            print()
        return "\n"

    def copy_branch(self, old_branch):
        self.solver_object.add(old_branch.solver_object.assertions())
        self.register_history = copy.deepcopy(old_branch.register_history)
        self.instruction_list = copy.deepcopy(old_branch.instruction_list)
        self.instruction_number = old_branch.instruction_number
        self.problem_flag = old_branch.problem_flag
    
# Any time there is a jump command, a new branch will need to be evaluated.  This will aid in storage and organization
class Branch_Container:
    """
    This will hold a list of Individual_Branch objects, which will represent all needed 
        branches of the program as dictated by any jump conditions.  Branch pruning 
        will be attempted based on equivalent register values occuring after an instruction
        has been executed across all branches
    """
    
    def __init__(self, main_branch):
        # Main list holding all the Individual_Branch for each branch needed
        # Main branch is the program path assuming all jumps aren't taken (ie it executes every instruction in the program)
        self.branch_list = [main_branch] 
        
        """
        If self.list[2] exists, self.instruction_causing_split[2] will hold the jump conditions 
        instruction number from the main list.  All branches added will assume the jump occured
        """
        self.instruction_causing_split = [0]
        
    # A jump condition created a new branch to follow
    def add_branch(self, new_branch, counter):
        self.branch_list.append(new_branch)
        self.instruction_causing_split.append(counter)
        
    # A branch either matched with another branch and became unneeded, or became unsat
    def delete_branch(self, branch_to_delete):
        del self.branch_list[branch_to_delete]
        del self.instruction_causing_split[branch_to_delete]
        
        
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
    
    # Find out how much we need to extend the number
    delta_bit_size = register_state_helper.reg_bit_width - value_bit_size
    
    if delta_bit_size > 0:
        if value >= 0:
            extended_value = ZeroExt(delta_bit_size, valueBV)
        else:
            extended_value = SignExt(delta_bit_size, valueBV)
            
    # Somehow this function was incorrectly called, and the input bit size match the register bit size?
    elif delta_bit_size == 0:
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)
                                   
    # If this branch is trigger something really went wrong, because now the input number is bigger than the register size
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
    
    # Get the source register names to be used in the solver
    s_r = source_reg
    
    #Now holds a bitVec variable to be passed into the solver
    source_val = r_s_h.register_history[s_r][-1].name        
    
    # Get the destinaton values
    
    # For Single Register Operations, destination register is the source register
    # Uses the default val from the function to indicate single reg operation
    if destination_reg == -1:
        d_r = s_r
        destination_old_val = source_val
        
    # For Two Register Operations
    else:
        d_r = destination_reg
        destination_old_val = r_s_h.register_history[d_r][-1].name

    #Extending the destination register sublist to include the new register name
    # Previous if/else clause was to make this line work for one and two reg operations
    r_s_h.register_history[d_r].append(\
               Register_Info("r%d_%d"%(d_r, r_s_h.instruction_number - 1),\
                             r_s_h.reg_bit_width))
    
    # Since the destination subreg list was extended, this references the last element in the extended sublist
    destination_new_val = r_s_h.register_history[d_r][-1].name
    
    # Formatting the return output for simplicity
    list_of_locations = [source_val, destination_old_val, destination_new_val]
    
    return list_of_locations, r_s_h

def get_the_locations_and_extend(input_value, target_reg, register_state_helper, destination_reg, extension_length):
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
        
    destination_reg : TYPE : boolean
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
    if destination_reg:
        list_of_locations, r_s_h = get_the_locations(input_value, r_s_h, target_reg)
    
    # Adding an imm value to a register
    else:
        list_of_locations, r_s_h = get_the_locations(target_reg, r_s_h)
        
        # Resize the imm value to the size of the target_reg if needed
        if extension_length != 0:
            print("\tExtending the smaller bitVector value to match reg size")
            list_of_locations[0] = extend_the_number(input_value, extension_length, r_s_h)
            
        else:
            list_of_locations[0] = BitVecVal(input_value, r_s_h.reg_bit_width)
            
    return list_of_locations, r_s_h

def get_register_values(branch_A):
    # Get the last known names of all registers in the branch
    current_reg_A = [branch_A.register_history[i][-1] for i in range(branch_A.num_Regs)]
    
    # Get the values from z3 for those register names
    branch_A_values = [branch_A.solver_object.model()[current_reg_A[i].name] for i in range(len(current_reg_A))]
    
    return branch_A_values
    
def registers_are_equal(branch_A, branch_B):
    """
    Finds the most recent version of all registers in two different branches and compares them

    Parameters
    ----------
    branch_A : TYPE : Individual_Branch
        A single branch of the program after a specific instruction
    branch_B : TYPE : Individual_Branch
        A different branch of the program after a specific instruction

    Returns
    -------
    TYPE : Boolean
        Compares the two values of the distinct branches

    """
    branch_A_values = get_register_values(branch_A)
    branch_B_values = get_register_values(branch_B)
    # print(branch_A)
    # print_current_register_state(branch_A)
    # print(branch_B)
    # print_current_register_state(branch_B)
    
    return branch_A_values == branch_B_values

# Add Instructions
def add_two_values(input_value, target_reg, register_state_helper, destination_reg, extension_length):
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
        
    destination_reg : TYPE : boolean
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

    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    # Perform the addition
    output_function = list_of_locations[2] == list_of_locations[1] + list_of_locations[0]
    
    # Guarantee no overflow
    no_overflow = BVAddNoOverflow(list_of_locations[0], list_of_locations[1], True)
    
    # Guarantee no underflow
    no_underflow = BVAddNoUnderflow(list_of_locations[0], list_of_locations[1])
    
    # Composition of the conditions
    add_function = And(output_function, no_overflow, no_underflow)
    
    return add_function, r_s_h

# Mov Instructions
def mov_to_reg(input_value, target_reg, register_state_helper, destination_reg, extension_length):
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
        
    destination_reg : TYPE : boolean
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
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h

def exit_instruction(register_state_helper):
    exit_ins = Bool("exit_%d"%(register_state_helper.instruction_number - 1))
    return exit_ins, register_state_helper 

# Program Setup and Output Functions
def check_and_print_model(instruction_list, register_state_helper):
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
    # print("\nThe full program is:")
    # for number, ins in enumerate(instruction_list):
    #     print (str(number) + ":\t" + ins)
    
    s = register_state_helper.solver_object
    problem_flag = register_state_helper.problem_flag
    print(f'\n--> Output for Branch {register_state_helper.branch_number} <--')    
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
   
    # print("\nThis program would be written as the following for BPF in C:\n")        
    # translate_to_bpf_in_c(register_state_helper.instruction_list)
    
    # Print out the final values of the registers in the program
    print_current_register_state(register_state_helper)
    print()
    
def print_current_register_state(register_state_helper):
    """
    Quick print function to return the most recent values stored in each register of a branch
    """
    print()
    r_s_h = register_state_helper
    # print(r_s_h)
    current_reg_states = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    print("The register values are currently:")
    for j, register in enumerate(current_reg_states):
        print("Register %d:\t"%j, end = " ")
        if "start" in register.reg_name:
            print("Not Initalized")
        else:
            try:
                # print(r_s_h.solver_object)
                num = r_s_h.solver_object.model()[register.name]
                print(num)
            except Z3Exception:
                print("oops, z3 said nope! wonder why...")
    print()

def translate_to_bpf_in_c(program_list):
    """
    Simplify the testing of a program in bpf_step using our current accessible keywords
        and the libbpf.h functions.  No error checking added, assuming formating of input strings
        is valid.
        
    This function will output a list of strings containing the translated versions ready to be
        copied right into sock_example.c, with a little maintence to remove the '' marks when python 
        prints out a string.
        
    Example:
        program_list =
        ["movI8 0 0", "movI8 0 0", 
         "movI8 1 2" , "movI8 3 3", 
         "addR 2 3", "movI8 -1 1", 
         "addR 2 1", "addI4 -3 2"]
        
        would print the following to the console:
            
        ['BPF_MOV64_IMM(BPF_REG_0, 0)', 'BPF_MOV64_IMM(BPF_REG_0, 0)', 
         'BPF_MOV64_IMM(BPF_REG_2, 1)', 'BPF_MOV64_IMM(BPF_REG_3, 3)', 
         'BPF_ALU64_REG(BPF_ADD, BPF_REG_3, BPF_REG_2)', 'BPF_MOV64_IMM(BPF_REG_1, -1)', 
         'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2)', 'BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, -3)']
    """
    output = []

    for instruction in program_list:
        split_ins = instruction.split(" ")
        keyword = split_ins[0]
        value = split_ins[1]
        target_reg = split_ins[2]
        
        if len(split_ins) == 3:
        # Add Instuctions
            # Adding an undersized outside value to a register value
            if keyword == "addI4":
                instruction = f'BPF_ALU32_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            # Adding a register sized outside value to a register value
            elif keyword == "addI8":
                instruction = f'BPF_ALU64_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
                
            # Adding a register value to a register value (value variable is being treated as the location of the source_register)
            elif keyword == "addR":
                instruction = f'BPF_ALU64_REG(BPF_ADD, BPF_REG_{target_reg}, BPF_REG_{value})'
            
        # Mov Instructions
            # Moving an outside value into a register (there is no mov32_imm definied in libbpf.h in bpf_step)
            elif keyword == "movI4" or keyword == "movI8":
                instruction = f'BPF_MOV64_IMM(BPF_REG_{target_reg}, {value})'

            # Moving a register value into another register (value variable is being treated as the location of the source_register)
            elif keyword == "movR":
                instruction = f'BPF_MOV64_REG(BPF_REG_{target_reg}, BPF_REG_{value})'

            # Exit command located
            elif keyword == "exit":
                instruction = "BPF_EXIT_INSN()"

        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            
            # Comparing an outside value to a register value (there is no jmp_imm_32 in bpf_step)
            if keyword == "jneI4" or keyword == "jneI8":
                instruction = f'BPF_JMP_IMM(BPF_JNE, BPF_REG_{target_reg}, {value}, {offset})'
            
            # Comparing a register value to a register value
            elif keyword == "jneR":
                instruction = f'BPF_JMP_REG(BPF_JNE, BPF_REG_{target_reg}, BPF_REG_{value}, {offset})'
        output.append(instruction)
        
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
    """
    
    """This creates a 2D List to hold info about the names, bit widths, and types of registers,
              and allow for growing sublists related to specific registers
    
    The initial state looks like [[r0_0], [r1_0], ..., [rNumRegs_0]], to hold the initial named objects
        containing info about each register, with each individual sublist able to be have future register
        changes appended due to changes on that specific register's held values.
          
     The list will be expanded as specific program instructons make changes to certain registers,
     but since it will only add one reg onto one sublist per instruction,
     space complexity is O(numRegs + numInstructionsToProgram)

     Register Changes tracked over time:
        register_list[0][0] is the inital state of r0
        register_list[1][1] is the state of register r1 after a change was made to it
        the Name stored in r_l[1][1] might be r1_3.  This would indicate that the first change made
            on register 1 occured in the 3rd instruction of the program
    ***This doesn't mean that three changes have been made, just that instruction 3 made a change on reg1
                    
    This way, you can maintain a history of register changes, use each individual entry
        as a new bitvec variable in the solver, and possibly trace back to a specific instruction
        which caused a problem

    Naming convention on printed output will be r0_0, r0_1, r0_2, ...
        with incrementing values after the underscore indicating which instruction caused the change
    """      

    # Update register_state_helper to contain the actual starting reg list, which will now be passed into execute_program
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
    new_constraints = And(True, False)
    
    return new_constraints, register_state_helper
   
def create_new_constraints_based_on_instruction_v2(register_state_helper, counter):
    """
    Parameters
    ----------
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_list, instruction_counter, problem_flag information,
        and bit_size for the registers on this specific branch of the program

    counter: Type : Int
        Which instruction in r_s_h.instruction_list to use
   
    Returns
    -------
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    Keywords added so far:
        mov Commands:               movI4 / movI8 / movR
        add Commands:               addI4 / addI8 / addR
        Jump if not equal Commands: jneI4 / jneI8 / jneR
        exit Command:               exit
        
    Keyword format for add/mov/exit (3 space seperated tokens):
        (treated as a string)   first: instruction name
        (treated as an int)     second: either the imm value or the source register location ()
        (treated as an int)     third: target register to be changed
        
    Keyword format for jump (4 space seperated tokens):
        (treated as a string)   first: instruction name
        (treated as an int)     second: either the imm value or the source register location
        (treated as an int)     third: register value to be compared against
        (treated as an int)     fourth: offset of instructions if comparison fails

    ***Will probably need to rewrite this depending on additions/changes to the basic instruction set***
    """
    instruction = register_state_helper.instruction_list[counter]
    print(f'Attempting to combine Branch {register_state_helper.branch_number} with instruction #{counter}: {instruction}')

    split_ins = instruction.split(" ")
    
    # Incorreclty sized instruction string
    if len(split_ins) < 3 or len(split_ins) > 4:
        new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)

        
    else:
        keyword = split_ins[0]
        value = int(split_ins[1])
        target_reg = int(split_ins[2])
        
        # Format for add, mov, and exit commands
        if len(split_ins) == 3:
            
            # Add Instuctions
            # Adding an undersized outside value to a register value
            if keyword == "addI4":
                new_constraints, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 4)
                
            # Adding a register sized outside value to a register value
            elif keyword == "addI8":
                new_constraints, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 0)
                
            # Adding a register value to a register value (value variable is being treated as the location of the source_register)
            elif keyword == "addR":
                new_constraints, register_state_helper = add_two_values(value, target_reg, register_state_helper, True, 0)
            
    
            # Mov Instructions
            # Moving an undersized outside value into a register
            elif keyword == "movI4":
                new_constraints, register_state_helper = mov_to_reg(value, target_reg, register_state_helper, False, 4)
    
            # Moving a register sized outside value into a register 
            elif keyword == "movI8":
                new_constraints, register_state_helper = mov_to_reg(value, target_reg, register_state_helper, False, 0)
    
            # Moving a register value into another register (value variable is being treated as the location of the source_register)
            elif keyword == "movR":
                new_constraints, register_state_helper = mov_to_reg(value, target_reg, register_state_helper, True, 0)
                
            # Exit command located
            elif keyword == "exit":
                new_constraints, register_state_helper = exit_instruction(register_state_helper)
             
            # Keyword doesn't match known functions
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)

                
        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            
            # Jump instructions all return a problem flag higher than the instruction counter, 
            # telling the program to create a new branch.  Since we're adding all branches, the actual comparison doesn't matter
            if keyword == "jneI4" or keyword == "jneI8" or keyword == "jneR":
                new_constraints = True
                register_state_helper.problem_flag = register_state_helper.instruction_number + offset
                               
            # Keyword doesn't match known functions
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)
        
    return new_constraints, register_state_helper

def execute_program_v3(all_branches):
    """
    Parameters
    ----------
    all_branches : TYPE :Branch_Container
        Will hold a list of all created branches for the program.  
        Each branch will be a Individual_Branch type maintaining its own z3 solver and problem flags

    Returns
    -------
    A whole bunch of shiny print statements telling the outcome of attempting to add all instructions
        and take all branches.


    Some bugs to be aware of:
        jump commands aren't checked to see if the offset is within the valid numbers for the instruction list
    """
    total_number_of_instructions = len(all_branches.branch_list[0].instruction_list)
    instruction_to_execute = -1
    while instruction_to_execute < total_number_of_instructions - 1:
        instruction_to_execute += 1
        prune_list = set()
        new_branch_made = False
        
        # Given a branch_container object, iterate through the list of branches, and execute a single instruction on each branch
        for branch_number, branch_of_program in enumerate(all_branches.branch_list):
            branch_of_program.instruction_number += 1
            print(f'\nLooking at Branch {branch_number}')
            
            # A previous jump instruction made this branch need to skip some instructions
            if branch_of_program.problem_flag > instruction_to_execute:
                new_branch_made = True
                # branch_of_program.solver_object.check()
                print(f'\tSkipping instruction {instruction_to_execute} due to jump condition\n')
                # check_and_print_model(branch_of_program.instruction_list, branch_of_program)        
                # print_current_register_state(branch_of_program)
                continue
            
            # Otherwise, execute the next instruction on this particular branch
            else:

                new_constraints, branch_of_program = \
                    create_new_constraints_based_on_instruction_v2(branch_of_program, instruction_to_execute)
                    
                # This will be triggered if the instruction just attempted was a jump command
                if branch_of_program.problem_flag > instruction_to_execute:
                    print("\n--> Creating a new branch starting at instruction #%d <--\n"%instruction_to_execute)
                    # Create a new branch with the problem flag set as the large value
                    # This will represent the branch taken when the jump is executed
                    new_branch = Individual_Branch(branch_of_program.num_Regs, branch_of_program.reg_bit_width)
                    new_branch.copy_branch(branch_of_program)
                    new_branch.branch_number = len(all_branches.branch_list)
                    new_branch_made = True
                    
                    # Reset problem flag in branch_list[0] to 0 to allow it to progress normally
                    branch_of_program.problem_flag = instruction_to_execute + 1
                    
                    # Add the new branch to the total list of branches with the instruction counter
                        # to show when the branch was created
                    all_branches.add_branch(new_branch, instruction_to_execute)
                    
                    # Exit the for loop to reset the internal values looping over all_branches
                    break
                 
                # Non jump instruction executed, check for viable model after new instruction added
                else:
                    # #Allow for rollback in event of problematic addition
                    # branch_of_program.solver_object.push()
                    
                    # Finally put the constraints from the instruction into the solver
                    branch_of_program.solver_object.add(new_constraints)
                    # print(f'Branch {branch_number} Problem Flag after Instruction {instruction_to_execute}: {branch_of_program.problem_flag}')
                    # check_and_print_model(branch_of_program.instruction_list, branch_of_program)        
                   
                    # Always check a solution before continuing
                    if branch_of_program.solver_object.check() == unsat:
                        
                        # # Roll back the solver to a version before the problematic instructions
                        # branch_of_program.solver_object.pop()
                    
                        # Special return value to tell the main test program that an error has occured
                        branch_of_program.problem_flag = branch_of_program.instruction_number * -1
                        
                        # Corner case if it fails on the first instruction (ie instruction 0)
                        if branch_of_program.instruction_number == 0:
                            branch_of_program.problem_flag = -1
                    else:
                        branch_of_program.problem_flag = instruction_to_execute
                # Now this branch has been either show to be viable or unsat
                # If it is unsat, send a message back to the main console indicating 
                    # which branch isn't viable, and where on the branch it failed
                if branch_of_program.problem_flag < 0:
                    jump_location = all_branches.instruction_causing_split[branch_number]
                    
                    print(f'\nBranch {branch_number} failed to find a viable solution.  \
                        \nThis branch came from the jump at instruction #{jump_location} \
                        \nThe specific jump instruction was {all_branches.branch_list[0].instruction_list[jump_location]}')
                    prune_list.add(branch_number)
        
        # Only check branches after regular instructions, since after immediately after a jump, the branches haven't diverged yet 
        if not new_branch_made:
            # Check the current register values of all branches to see if any of them can be combined
            branch_pairs = itertools.permutations(all_branches.branch_list, 2)
            
            for (branch_A, branch_B) in branch_pairs:
                if branch_A.solver_object.check() == sat and branch_B.solver_object.check() == sat \
                    and registers_are_equal(branch_A, branch_B):
                    
                    # Delete the most recently added branch of the pair
                    prune_list.add(max(branch_A.branch_number, branch_B.branch_number))
    
    
            # After a full runthrough of a single instruction on all branches, prune the list before re-entering the for loop
            for branch_number in prune_list:
                all_branches.delete_branch(branch_number)
    
    for branch in all_branches.branch_list:
        check_and_print_model(branch.instruction_list, branch)
           
def create_program(program_list = ""):
    """
    Purpose: Start up the ebpf program and see how far it can run.
    Current Default Conditions make 4 registers, each with a bitWidth of 8 to allow
        our output numbers to be easy to check
    
    Parameters
    ----------
    program_list : Type(List of Strings)
        Using special keyword number string instructions, gives a list of the instructions to be attempted by the solver
        If left blank, will use built in test program, as opposed to user input

    Returns
    -------
    None.

    """
    
    # Define the number and size of the registers in the program
    # Future update will change this to be defined by user input to cmd line
    num_Regs = 4
    reg_bit_width = 8
    
    # Setting up the container for holding register history, register sizes, and instruction counter
    register_state_helper = Individual_Branch(num_Regs, reg_bit_width)
    
    # Set up the inital list of registers and z3 solver, to be modified in execute_program
    register_state_helper = create_register_list(num_Regs, register_state_helper)

    
    """ 
    Keywords added so far:
        mov Commands:               movI4 / movI8 / movR
        add Commands:               addI4 / addI8 / addR
        Jump if not equal Commands: jneI4 / jneI8 / jneR
        Exit Commands:              exit
    
    Keyword format for add/mov (3 space seperated tokens):
        (treated as a string)   first: instruction name
        (treated as an int)     second: either the imm value or the source register location ()
        (treated as an int)     third: target register to be changed
        
    Keyword format for jump (4 space seperated tokens):
        (treated as a string)   first: instruction name
        (treated as an int)     second: either the imm value or the source register location
        (treated as an int)     third: register value to be compared against
        (treated as an int)     fourth: offset of instructions if comparison fails
        
    The example program below cooresponds to the following sequence of instructions:
        0) Set the inital value of register 1 to 3        (movI8 4 1)   /* r0 = 1   */
        1) Set the inital value of register 1 to 3        (movI8 3 1)   /* r1 = 3   */
        2) Add the value of register 0 into register 1    (addR 0 1)    /* r1 += r0 */
        3) Set the initial value of register 2 to -1      (movI4 -1 2)  /* r2 = -1  */
        4) Add the value of register 2 into register 1    (addR 2 1)    /* r1 += r2 */
        5) Add a 4 bit wide -3 to register 2              (addI4 -3 2)  /* r2 += -3 */
    
    
    And it does (actual program output):

    """   
    if program_list == "":
        program_list = ["movI8 4 1", "movI8 3 2", "addR 1 2", "jneI8 5 2 2", "addR 1 1", "addI4 3 2", "addR 1 2", "addR 2 1", "exit 0 0"]
        # program_list = ["movI8 1 0" , "movI8 3 1", "addR 0 1", "movI4 -1 2", "addR 2 1", "addI4 -3 2", "exit 0 0"]
    
    # Loading the program into r_s_h for use in jump commands if needed
    register_state_helper.instruction_list = program_list
    
    # Making the main holder of any distinct branches that need to be evaluated for the program
    all_branches = Branch_Container(register_state_helper)
    
    execute_program_v3(all_branches)
    
# create_program()