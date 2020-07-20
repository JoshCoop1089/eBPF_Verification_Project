# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 15:38:07 2020

@author: joshc
"""

"""
Monday Meeting Plan

1) Create sample eBPF program as guide
    -- Program has the following elements
    a) Register to Register Addition (signed values)
    b) Immediate to Register Addition (signed values)
    c) Setting one register to the value of another register
    d) Setting a register to an immediate value

        --Since we need to account for values that might not be the full size of the register, 
        we can use the ZeroExt() and SignExt() z3 functions to fill the register in if needed
        
    e) Branching
        -- Using JNE, split the possible function conditions
        -- One branch will have an early exit condition

get-rekt-hardened in 4/8 bit form:

#define BPF_DISABLE_VERIFIER()                                                   \
	BPF_MOV4_IMM(BPF_REG_2, 0xF),                  /* r2 = (u4)0xF   */   \
	BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 0xF, 2),       /* if (r2 == -1) {        */   \
	BPF_MOV8_IMM(BPF_REG_0, 0),                    /*   exit(0);             */   \
	BPF_EXIT_INSN()                                /* }                      */   \
    
    And some more instructions i'll make up to be on the NE path from the jump imm command    

"""
from z3 import *

# Internal representation for one instance of a register
class Register_Info:
    def __init__(self, name, reg_bit_size,  reg_type = ""):
        # Not using this yet, because just dealing with arithmetic on numbers, not pointers
        # self.reg_type = reg_type
        
        # Unsure if I will need to store this on a per register basis
        # self.reg_bit_size = reg_bit_size

        self.name = BitVec(name, reg_bit_size)
        self.reg_name = name 

# Container to streamline function parameters/returns
class Helper_Info:
    def __init__(self, num_Regs, reg_bit_width):
        self.num_Regs = num_Regs
        self.reg_bit_width = reg_bit_width
        self.solver_object = Solver()
        
        # On creation, the following aren't used
        self.register_history = [[]]
        self.instruction_list = [""]
        self.instruction_number = 0
        self.problem_flag = 0
    
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
        
    register_state_helper : TYPE : helper_info
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
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    destination_reg : TYPE : int, optional
        Location where data will be stored after calculation if dealing with a two register operation

    Returns
    -------
    list_of_locations : TYPE : List of BitVector Objects
        # list_of_locations = [source_val, destination_old_val, destination_new_val]
        Information specifying what locations will need to be used in the main formulas
    
    r_s_h : TYPE: helper_info
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
               Register_Info("r%d_%d"%(d_r, r_s_h.instruction_number),\
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
        
    register_state_helper : TYPE : helper_info
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
    
    r_s_h : TYPE: helper_info
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
        
    register_state_helper : TYPE : helper_info
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
        
    r_s_h : TYPE: helper_info
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
        
    register_state_helper : TYPE : helper_info
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
        
    r_s_h : TYPE: helper_info
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h

# Jump Instructions
def jump_general(input_value, target_reg, offset, register_state_helper, destination_reg, extension_length):
    """
    Thoughts on how to operate the jump instruction
    
    Jump creates a defined branch point, where register values should be frozen and 
    referenced in case something goes awry
    
    Can we use an offset marker to pass into the jump function, and do something like.
    
    if == then implies next_instruction
    if != then implies next_instruction + offset?
    
    
    If i pass in the instruction list with reg_state_helper, I can use it to create implication 
        statements based on the value of offset
        
    Example Situation:
        jneR with offset of 3, and r0, r1 comparison, is located at instruction 4:
        
            this means that if r0 = r1, instruction 5 is implied
            else, if r0 != r1, instruction 8 is implied
            
        Since we cannot assume instruction 8 is the last instruction, we need to add 
            the smaller branch (ins 5, 6, and 7) to the solver, and then return to 
            execute instruction 9 if needed in the main program
            
    Current plan:
        1) Get the values to be compared
        2) Set up the implication statements for positive and negative results on comparison
            by using create_new_constraint on the single needed instructions
        3) Add the positive implication to the solver and check it.
        3) Snip a portion of instruction list, and pass it into execute_branch.
        4) Execute_branch will act like normal execute_program, moving through the
            instruction sublist, except it will return register_state_helper when completed.
        5) if execute branch returns without a problem, add the negative implication
           
    Problem:
        how to reference the right instances of a register for the second implication if it is changed in the branch
        
    Possible solution:
        create a small array of the last entries in each register list to reference for neg implication?
    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # I don't feel like rewriting get loc and extend to not always add a new reg value on the 
    # destination register list, so i'll just delete it here
    del r_s_h.register_history[target_reg][-1]
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    comparison_statement = list_of_locations[0] == list_of_locations[1]
    
    # Getting the most recent instances of all register values to compare against
    current_reg_states = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
   
    for i in current_reg_states:
        print(i.name)
        
    # These two variables should hold the index of the required instructions
    next_ins = r_s_h.instruction_number + 1
    next_ins_with_offset = r_s_h.instruction_number + 1 + offset

    equal_next_ins , r_s_h = \
        create_new_constraints_based_on_instruction(r_s_h.instruction_list[next_ins], register_state_helper)
    
    # formulas returned from create_new_constraints
    comparison_equal_implication = Implies(comparison_statement, equal_next_ins)
    print(comparison_equal_implication)
    print()
    
    branch_of_program = r_s_h.instruction_list[next_ins:next_ins_with_offset]
    print(branch_of_program)
    for instruction_number,instructon in enumerate(branch_of_program,r_s_h.instruction_number):
        a=b
    
    not_equal_next_ins , r_s_h = \
        create_new_constraints_based_on_instruction(r_s_h.instruction_list[next_ins_with_offset], register_state_helper)
    comparison_not_equal_implication = Implies(Not(comparison_statement), not_equal_next_ins)
    print(comparison_not_equal_implication)
    
    
    # comparison_not_equal_implication = Implies(Not(comparison_statement), next_ins_with_offset)
    comparison_constraints = comparison_statement
    
    
    
    return comparison_constraints, register_state_helper


def exit_instruction(register_state_helper):
    exit_ins = Bool("exit_%d"%register_state_helper.instruction_number)
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
    print("\nThe full program is:")
    for number, ins in enumerate(instruction_list):
        print (str(number) + ":\t" + ins)
    
    s = register_state_helper.solver_object
    problem_flag = register_state_helper.problem_flag
        
    if s.check() == sat:
        print("\nThe last instruction attempted was #%d:"%(abs(problem_flag)))
        if problem_flag == (len(instruction_list) - 1):
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

def create_register_list(numRegs, register_state_helper):
    """
    Purpose: Create the register history list used to hold all register changes 
    for SSA naming and assignment scheme

    Parameters
    ----------
    numRegs : TYPE: (int)
        The number of registers the user wishes to model
        
    register_state_helper : Type (Helper_Info)
        generic container holding program variables for referencing

    Returns
    -------
    register_state_helper : TYPE : helper_info
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
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program

    
    Returns
    -------
    new_constraints : Type : z3 equation
        Poision pill constraint to force solver to unsat
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction
    """
    print("\nIncorrect instruction format for instruction number: %d"%register_state_helper.instruction_number)
    print("Please retype the following instruction: \n\t-->  %s  <--"%instruction)
    register_state_helper.problem_flag = register_state_helper.instruction_number * -1
    new_constraints = And(True, False)
    
    return new_constraints, register_state_helper
   
def create_new_constraints_based_on_instruction(instruction, register_state_helper):
    """
    Parameters
    ----------
    instruction: Type : String
        Specific keyword sequence to indicate which instruction, and what values, are to be used
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program

    
    Returns
    -------
    register_state_helper : TYPE : helper_info
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
            
            # Comparing an undersized outside value to a register value
            if keyword == "jneI4":
                new_constraints, register_state_helper = jump_on_not_equal()

            # Comparing a register sized outside value to a register value
            elif keyword == "jneI8":
                new_constraints, register_state_helper = jump_on_not_equal()
            
            # Comparing a register value to a register value
            elif keyword == "jneR":
                new_constraints, register_state_helper = jump_general(value, target_reg, offset, register_state_helper, True, 0)
                               
            # Keyword doesn't match known functions
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)
        
    return new_constraints, register_state_helper

def execute_branch(program_sub_list, register_state_helper):
    """
    Small version of execute_program to take care of branching conditions in Jump instructions
    
    pro_sub_list will take in a truncated version of the instruction list, focusing on
        the instructions needed if the jump instruction is true, ie start ins number to
        start ins = offset.  Then it will loop through those instructions, adding them 
        as normal, checking for errors and, will pass back the main r_s_h to indicate 
        either successful addition of instructions or problem instructions
    """
    
    return register_state_helper
    
def execute_program_v2(program_list, register_state_helper):
 
    # Add instructions from the program list to the solver
    for instruction_number, instruction in enumerate(program_list):
        
        register_state_helper.instruction_number = instruction_number
        
        # This should allow skipping forward in the ins list without adding skipped instructions
        if register_state_helper.problem_flag > instruction_number:
            continue
        
        print("Attempting to combine solver with instruction #%d: %s"%(instruction_number, instruction))
        new_constraints, register_state_helper = \
            create_new_constraints_based_on_instruction(instruction, register_state_helper)
        
        # Debug just in case
        # print(register_state_helper)
        
        # v2 Plan, move correctness checking into execute_program main functions
        
        #Allow for rollback in event of problematic addition
        register_state_helper.solver_object.push()
        
        # Finally put the constraints from the instruction into the solver
        register_state_helper.solver_object.add(new_constraints)
                
        #Always check a solution before returning to the main function
        if register_state_helper.solver_object.check() == unsat:
            
            # Roll back the solver to a version before the problematic instructions
            register_state_helper.solver_object.pop()
        
            # Special return value to tell the main test program that an error has occured
            register_state_helper.problem_flag = register_state_helper.instruction_number * -1
            
            # Corner case if it fails on the first instruction (ie instruction 0)
            if register_state_helper.instruction_number == 0:
                register_state_helper.problem_flag = -1
            
        else:
            register_state_helper.problem_flag = instruction_number
            
        # Special register_state_helper.problem_flag returns:
            # problem_flag < 0 --> an instruction caused an unsat solution
            # problem_flag > instruction_counter --> a jump instruction is pushing the list forward
        
        # Problem_flag < 0 means that a specific instruction caused a problem, 
        # and we're exiting without finishing all the instructions in the program
        if register_state_helper.problem_flag < 0:
            print("\nThe program encountered an error on instruction #%s"%abs(register_state_helper.problem_flag))
            print("\t-->  " + program_list[abs(register_state_helper.problem_flag)] + "  <--")
            print("The last viable solution before the problem instruction is shown below:")
            break

    check_and_print_model(program_list, register_state_helper)
    
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
    register_state_helper = Helper_Info(num_Regs, reg_bit_width)
    
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
        0) Set the inital value of register 0 to 1        (movI8 1 0)   /* r0 = 1   */
        1) Set the inital value of register 1 to 3        (movI8 3 1)   /* r1 = 3   */
        2) Add the value of register 0 into register 1    (addR 0 1)    /* r1 += r0 */
        3) Set the initial value of register 2 to -1      (movI4 -1 2)  /* r2 = -1  */
        4) Add the value of register 2 into register 1    (addR 2 1)    /* r1 += r2 */
        5) Add a 4 bit wide -3 to register 2              (addI4 -3 2)  /* r2 += -3 */
    
    The output should end up with r0_0 = 1, r1_1 = 3, r1_2 = 4, r2_3 = 255 (-1 in 8 bit), 
        r1_4 = 3, and r2_5 = 252 (-4 in 8 bit)
    
    And it does (actual program output):
        Attempting to combine solver with instruction #0: movI8 1 0
        Attempting to combine solver with instruction #1: movI8 3 1
        Attempting to combine solver with instruction #2: addR 0 1
        Attempting to combine solver with instruction #3: movI4 -1 2
        	Extending the smaller bitVector value to match reg size
        Attempting to combine solver with instruction #4: addR 2 1
        Attempting to combine solver with instruction #5: addI4 -3 2
        	Extending the smaller bitVector value to match reg size
        
        The full program is:
        0:	movI8 1 0
        1:	movI8 3 1
        2:	addR 0 1
        3:	movI4 -1 2
        4:	addR 2 1
        5:	addI4 -3 2
        
        The last instruction attempted was #5:
        Program successfully added all instructions
        [r0_0 = 1,
         r1_2 = 4,
         r2_3 = 255,
         r1_1 = 3,
         r1_4 = 3,
         r2_5 = 252]
    """   
    if program_list == "":
        program_list =["movI8 1 0" , "movI8 3 1", "addR 0 1", "movI4 -1 2", "addR 2 1", "addI4 -3 2"]
    
    # Loading the program into r_s_h for use in jump commands if needed
    register_state_helper.instruction_list = program_list
    
    execute_program_v2(program_list, register_state_helper)


create_program()