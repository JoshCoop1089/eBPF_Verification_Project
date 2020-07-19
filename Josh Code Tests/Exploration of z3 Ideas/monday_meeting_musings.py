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
        -- Using JNE split the possible function conditions
        -- One branch will have an early exit condition
        -- Branching JNE condition will compare the two signed values stored in registers

get-rekt-hardened in 4/8 bit form:
    #define BPF_DISABLE_VERIFIER()                                                   \
	BPF_MOV4_IMM(BPF_REG_2, 0xF),                  /* r2 = (u4)0xF   */   \
	BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 0xF, 2),       /* if (r2 == -1) {        */   \
	BPF_MOV8_IMM(BPF_REG_0, 0),                    /*   exit(0);             */   \
	BPF_EXIT_INSN()                                /* }                      */   \

"""
from z3 import *

# Internal representation for one instance of a register
class Register_Info:
    def __init__(self, name, reg_bit_size,  reg_type = ""):
        self.name = BitVec(name, reg_bit_size)
        
        # Not using this yet, because just dealing with arithmetic on numbers, not pointers
        # self.reg_type = reg_type
        
        # Unsure if I will need to store this on a per register basis
        # self.reg_bit_size = reg_bit_size

# Container to streamline function parameters/returns
class Helper_Info:
    def __init__(self, reg_bit_width):
        self.reg_bit_width = reg_bit_width
        # self.solver_object = Solver()
        
        # On creation, the following aren't used
        self.register_history = [[]]
        self.instruction_list = [""]
        self.instruction_number = 0
        self.problem_flag = -1
        
    def update_helper_info(self, register_history, instruction_number = 0, problem_flag = -1, reg_bit_width = -1):
        
        #Only need to initialize these once at the start of the program
        if reg_bit_width != -1:
            self.reg_bit_width = reg_bit_width
            
        # Keeping track of changes to registers and which instruction was just attempted/caused a problem
        self.register_history = register_history
        self.instruction_number = instruction_number
        self.problem_flag = problem_flag
        
        return self
    
    def __str__(self):
        print("The current contents of the helper_bundle are:")
        print("\tRegister Bit Width: %d"%self.reg_bit_width)
        print("\tTotal Number of Registers: %d"%self.num_regs)
        print("\tThe Current Instruction Number is: %d"%self.instruction_number)
        print("\tProblem Flag's Value is': %d"%self.problem_flag)
        print("\tThe register history looks like: \n")
        print(self.register_history)
        
        return "\n"
    
# General helper functions for ease of use
def extend_the_number(value, value_bit_size, register_state_helper):
    """
    If a number is passed in that is not the size of the register it is being assigned
        to, this will extend the BitVec representation to have the correct Bit Width,
        while maintaining signed properties if needed

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
    extended_value : TYPE
        DESCRIPTION.

    """
    # If the number being added into a register is smaller than the register, 
    # we need to either sign extend or zero extend the bitValue to fit the new reg
    
    # Find out how much we need to extend the number
    delta_bit_size = register_state_helper.reg_bit_width - value_bit_size
    
    if delta_bit_size > 0:
        if value >= 0:
            extended_value = ZeroExt(delta_bit_size, value)
        else:
            extended_value = SignExt(delta_bit_size, value)
            
    # Somehow this function was incorrectly called?
    else:
        extended_value = value
        
    return extended_value

def get_the_locations(source_reg, register_state_helper, destination_reg = -1):
    """
    Purpose: Simplify getting of register names for operations
    
    Parameters
    ----------
    added_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    source_reg : TYPE : int
        Location where data will taken from before calculation
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information
        
    destination_reg : TYPE : int, optional
        Location where data will be stored after calculation if dealing with a two register operation

    Returns
    -------
    list_of_locations : TYPE : List of BitVector Objects
        # list_of_locations = [source_val, destination_old_val, destination_new_val]
        Information specifying what locations will need to be used in the main formulas
    
    r_s_h : TYPE: helper_info
        Holds reg_history, instruction_counter, problem_flag information, now updated from the computation

    """    
    r_s_h = register_state_helper
    
    # Get the source register names to be used in the solver
    s_r = source_reg
    s_l = len(r_s_h.register_history[s_r])
    
    #Now holds a bitVec variable to be passed into the solver
    source_val = r_s_h.register_history[s_r][s_l-1]        
    
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
        d_l = len(r_s_h.register_history[d_r])
        destination_old_val = r_s_h.register_history[d_r][d_l-1]

    #Extending the destination register sublist to include the new register name
    # Previous if/else clause was to make this line work for one and two reg operations
    r_s_h.register_history[d_r].append(\
               Register_Info("r%d_%d"%(d_r, r_s_h.instruction_counter),\
                             r_s_h.reg_bit_width))
    
    # Since the destination subreg list was extended, d_l, which used to be the length of the old sublist,
        # now references the last element in the extended sublist
    destination_new_val = r_s_h.register_history[d_r][d_l]
    
    # Formatting the return output for simplicity
    list_of_locations = [source_val, destination_old_val, destination_new_val]
    
    return list_of_locations, r_s_h

def get_the_locations_and_extend(added_value, target_reg, register_state_helper, destination_reg, extension_length):
    """
    Sets up properly sized inputs and returns the locations to put them

    Parameters
    ----------
    added_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    destination_reg : TYPE : boolean
        States whether to treat added_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    list_of_locations : TYPE : List of BitVector Objects
        # list_of_locations = [source_val, destination_old_val, destination_new_val]
        Information specifying what locations will need to be used in the main formulas
    
    r_s_h : TYPE: helper_info
        Holds reg_history, instruction_counter, problem_flag information, now updated from the computation

    """
    r_s_h = register_state_helper

    # Two Register Operation
    if destination_reg:
        list_of_locations, r_s_h = get_the_locations(added_value, r_s_h, target_reg)
    
    # Adding an imm value to a register
    else:
        list_of_locations, r_s_h = get_the_locations(target_reg, r_s_h)
        
        # Resize the imm value to the size of the target_reg if needed
        if not extension_length:
            print("extending the smaller bitVector value to match reg size")
            list_of_locations[0] = extend_the_number(added_value, extension_length, r_s_h)
            
        else:
            list_of_locations[0] = BitVecVal(added_value, r_s_h.reg_bit_width)
            
    return list_of_locations, r_s_h

# Specific eBPF Commands on the full register size



def exit_instruction(register_state_helper):
    return register_state_helper 


# Add Instructions
def add_two_values(added_value, target_reg, register_state_helper, destination_reg, extension_length):
    """
    Generic function to combine two numbers and check for overflows    

    Parameters
    ----------
    added_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    destination_reg : TYPE : boolean
        States whether to treat added_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    add_function : Type : z3 equation
        Holds the combination of all constraints due to the add instruction
        
    r_s_h : TYPE: helper_info
        Holds reg_history, instruction_counter, problem_flag information, now updated from the computation

    """
    r_s_h = register_state_helper

    list_of_locations, r_s_h = get_the_locations_and_extend(added_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    # Perform the addition
    output_function = list_of_locations[2] == list_of_locations[1] + list_of_locations[0]
    
    # Guarantee no overflow
    no_overflow = BVAddNoOverflow(list_of_locations[0], list_of_locations[1], True)
    
    # Guarantee no underflow
    no_underflow = BVAddNoUnderflow(list_of_locations[0], list_of_locations[1], True)
    
    # Composition of the conditions
    add_function = And(output_function, no_overflow, no_underflow)
    
    # # v2 Plan, move correctness checking into execute_program main functions
    # #Allow for rollback in event of problematic addition
    # r_s_h.solver_object.push()
    # #Always check a solution before returning to the main function
    # if r_s_h.solver_object.check() == unsat:
    #     # Roll back the solver to a version before the problematic  instructions
    #     r_s_h.solver_object.pop()

    #     # Special return value to tell the main test program that an error has occured
    #     r_s_h.problem_flag = r_s_h.instruction_counter * -1
    
    return add_function, r_s_h

# Specific keyword functions from the main program, they all call the add_two_value function with special inputs
def add_reg_to_reg(source_reg, target_reg, register_state_helper):
    
    add_output, register_state_helper = add_two_values(source_reg, target_reg, register_state_helper, True, 0)
    
    return add_output, register_state_helper

def add_imm8_to_reg(value, target_reg, register_state_helper):
    
    add_output, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 0)
    
    return add_output, register_state_helper

def add_imm4_to_reg(value, target_reg, register_state_helper):
    
    add_output, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 4)

    return register_state_helper

# Mov Instructions
def mov_to_reg(added_value, target_reg, register_state_helper, destination_reg, extension_length):
    """
    Generic function to move a value into a register    

    Parameters
    ----------
    added_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : helper_info
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    destination_reg : TYPE : boolean
        States whether to treat added_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    mov_function : Type : z3 equation
        Holds the combination of all constraints due to the mov instruction
        
    r_s_h : TYPE: helper_info
        Holds reg_history, instruction_counter, problem_flag information, now updated from the computation

    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(added_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h

# Specific keyword functions from the main program, they all call the mov_to_reg function with special inputs  
def mov_reg_to_reg(source_reg, target_reg, register_state_helper):
    
    mov_output, register_state_helper = add_two_values(source_reg, target_reg, register_state_helper, True, 0)
    
    return mov_output, register_state_helper

def mov_imm8_to_reg(value, target_reg, register_state_helper):
        
    mov_output, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 0)
    
    return mov_output, register_state_helper

def mov_imm4_to_reg(value, target_reg, register_state_helper):

    mov_output, register_state_helper = add_two_values(value, target_reg, register_state_helper, False, 4)
    
    return mov_output, register_state_helper


# Jump Instructions
def jump_general(source_reg, second_val, offset, register_state_helper, destination_reg, extension_length):
    return register_state_helper

def jump_on_not_equal_to_reg(source_reg, target_reg, offset, register_state_helper):
    return register_state_helper

def jump_on_not_equal_to_imm8(value, target_reg, offset, register_state_helper):
    return register_state_helper

def jump_on_not_equal_to_imm4(value, target_reg, offset, register_state_helper):
    # Resize the imm value to the size of the target_reg
    extended_value = extend_the_number(value, 4, register_state_helper)

    # Now that the input value is properly sized, call jump_on_not_equal_to_imm8
    register_state_helper = jump_on_not_equal_to_imm8(source_reg, extended_value, register_state_helper)
    return register_state_helper
"""
Thoughts on how to operate the jump instruction

Jump creates a defined branch point, where register values should be frozen and 
referenced in case something goes awry

Can we use an offset marker to pass into the jump function, and do something like.

if == then implies next_instruction
if != then implies next_instruction + offset?

"""

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
        elif problem_flag == 0:
            print("Program successfully added an exit instruction.")
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
    reg_list : Type(List of Lists of Register_Info objects)
        Clean slate to allow for a look at the progress of a new collection of 
        bpf commands, and their effects on register values.

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
    reg_list = [[Register_Info("r"+str(i) + "_0", register_state_helper.reg_bit_width)] for i in range(numRegs)]
    
    # Update register_state_helper to contain the actual starting reg list, which will now be passed into execute_program
    register_state_helper.update_helper_info(reg_list)
    
    return register_state_helper  
   
def program_instruction_added(instruction, register_state_helper):
    """
    Will probably need to rewrite this depending on changes to the basic instruction set
    Keywords added so far:
        mov Commands:               movI4 / movI8 / movR
        add Commands:               addI4 / addI8 / addR
        Jump if not equal Commands: jneI4 / jneI8 / jneR
    """
    return register_state_helper

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
        
        # This should allow skipping forward in the ins list without adding skipped instructions
        if register_state_helper.problem_flag >= instruction_number:
            continue
        
        print("Attempting to combine solver with instruction #%d: %s"%(instruction_number, instruction))

        
        # Special register_state_helper.problem_flag returns:
            # 0 --> an early exit instruction was executed
            # problem_flag < 0 --> an instruction caused an unsat solution
            # problem_flag > instruction_counter --> a jump instruction is pushing the list forward
        register_state_helper = program_instruction_added(instruction, register_state_helper)
        
        # Problem_flag = 0 means an exit instruction was successfully reached inside the main program
        if register_state_helper.problem_flag == 0:
            break
        
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
    register_state_helper = Helper_Info(reg_bit_width)
    
    # Set up the inital list of registers and z3 solver, to be modified in execute_program
    register_state_helper = create_register_list(num_Regs, register_state_helper)

    
    """ 
    All individual instructions are a single string of the form:
        'keyword' 'source_register' 'destination_register, shift_val, or initial val'
        
        First keyword is a string identifying the instruction action (addU, and, lshift)
        Second source_reg is an int to say which register will be modifing/contributing a value to the instruction
        Third token is always an int, but its use depends on the first keyword
        
    The example program below cooresponds to the following sequence of instructions:
        0) Set the inital value of register 0 to 1               (init 0 1)   /* r0 = 1*/
        1) Set the inital value of register 1 to 3               (init 1 3)   /* r1 = 3*/
        2) Add the unsigned value of register 0 into register 1  (addU 0 1)   /* r1 += r0*/
        3) Set the initial value of register 2 to -1             (init 2 -1)  /* r2 = -1*/
        4) Add the signed value of register 2 into register 1    (addS 2 1)   /* r1 += r2 */
    """   
    if program_list == "":
        program_list =["init 0 1" , "init 1 3", "addU 0 1", "init 2 -1", "addS 2 1"]
    
    execute_program_v2(program_list, register_state_helper)



    
a = Helper_Info(4, 2, [["r0_0"], ["r1_0"]], 5)
print(a)
a.update_helper_info([["r0_0", "r0_5"], ["r1_0"]], 6)
print(a)