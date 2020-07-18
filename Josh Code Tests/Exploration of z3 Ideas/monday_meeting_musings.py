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
        self.solver_object = Solver()
        
        # On creation, the following aren't used
        self.register_history = [[]]
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

# Specific eBPF Commands on the full register size
def mov_reg_to_reg(source_reg, target_reg, register_state_helper):
    return register_state_helper

def mov_imm8_to_reg(target_reg, value, register_state_helper):
    return register_state_helper

# def add_two_registers_signed(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
#     """
#     Purpose: Add two register values together, treating the numbers as signed bitValues
    
#     Parameters
#     ----------
#     source_reg: Type(int)
#         Which register to take the inital value from, referencing the last element in the
#         specific sublist of the reg_history list

#     destination_reg: Type(int)
#         Which register to take the second value from, and what sublist to append the
#         result of the computation to

#     solver: Type(z3 Solver Object)
#         Stores all the FOL choices made so far, will be modified due to requirments
#         of add and passed back out of function

#     reg_history: Type(List of List of z3 bitVectors variables)
#         Holds all previous names for all registers in the program, used to allow for
#         SSA representation of register values.  Will be modified with new register name for whatever
#         comes out of the calculation, to be appended to the destination_reg sublist
   
#     instruction_counter: Type(int)
#         Which instruction of the program is currently being executed, allows for tracing of problematic function calls

#     register_bit_width: Type(int)
#         How large the registers should be

#     Returns
#     -------
#     solver:  Type(z3 Solver Object)
#         Modified to include the new value of the destination register, and a overflow check on the calculation

#     reg_history: Type(List of lists of BitVec variables)
#         Additional value appended to the destinaton_reg sublist holding the new value.

#     instruction_counter: Type(int)
#         This will always return the instruction value of the last correctly completed instruction.
#         In the event of an unsat solution, this return will force a check in the main program to halt continuned execution
#         by returning the problematic instruction as a negative int (there is a check in the main function for this return
#                                                                     always being positive)
#     """
#     #Quick variables to access specific indexes in the register history lists
#     # (ie, the most recent versions of the two registers involved in this add)
#     list_of_nums, reg_history = \
#         get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg)
    
#     #Allow for rollback in event of problematic addition
#     solver.push()
    
#     #Here there be dragons
#     #Adding the two registers, and including the overflow constraint assuming signed ints in the register
#     # list_of_nums = [source_val, destination_old_val, destination_new_val]
#     solver.add(list_of_nums[2] == list_of_nums[1] + list_of_nums[0])
    
    
#     """What does overflow mean:
#         src pos + dst pos --> dst_new >= dst_old
#             technically 7 is the largest positive in 4 bit 2's comp,
#             so 4 + 4 would overflow, 0100 + 0100 = 1000 (ie 4 + 4 = -8)
#         src pos dst neg --> 7 + -1 --> dst_new >= dst_old
#                         --> 1 + -8 also works as above
#         src neg, dst pos --> -1 + 7 --> dst_old > dst_new
#                         This one cannot be >= because if dst = 0, 
#                         then new cannot be equal to it since negs start at -1
#         src neg, dst neg --> -1 + -5 --> dst_old > dst_new
        
#         So the breaking point is based on the sign of the src register (ie not the one being written into)
        
#         sign(src) = pos -> (dst_new > dst_old)
#         Implies(a,b): a is src_val >= 0, b is dst_new > dst_old
#         sign(src) = neg -> (dst_new <= dst_old)
#         Implies(a,b): a is src_val < 0, b is dst_old >= dst new
#         """
#     # First attempt at signed overflow FOL considerations
#     # list_of_nums = [source_val, destination_old_val, destination_new_val]
    
#     # Source_reg holds 0 or positive number in 2's complement
#     a = list_of_nums[0] >= 0
#     b = list_of_nums[2] > list_of_nums[1]
#     pos_overflow = Implies(a,b)
#     solver.add(pos_overflow)
        
#     # Source_reg holds negative number in 2's complement
#     a = list_of_nums[0] < 0
#     b = list_of_nums[2] <= list_of_nums[1]
#     neg_overflow = Implies(a,b)
#     solver.add(neg_overflow)
    
#     #Here ends dragons
    
    
#     #Always check a solution before returning to the main function
#     if solver.check() == unsat:
#         # Roll back the solver to a version before the problematic add instructions
#         solver.pop()

#         # Remove the register update because it causes a problem
#         del reg_history[destination_reg][-1]

#         # Special return value to tell the main test program that an error has occured
#         instruction_counter *= -1
    
#     return solver, reg_history, instruction_counter


def add_reg_to_reg(source_reg, target_reg, register_state_helper):
    return register_state_helper

def add_imm8_to_reg(target_reg, value, register_state_helper):
    return register_state_helper

def jump_on_not_equal_to_reg(source_reg, target_reg, register_state_helper):
    return register_state_helper

def jump_on_not_equal_to_imm8(source_reg, value, register_state_helper):
    return register_state_helper

def exit_instruction(register_state_helper):
    return register_state_helper 



# Specific eBPF Commands for using smaller input values than the full register size
def mov_imm4_to_reg(target_reg, value, register_state_helper):
    # Resize the imm value to the size of the target_reg
    extended_value = extend_the_number(value, 4, register_state_helper)
    
    # Now that the input value is properly sized, call mov_imm8_to_reg
    register_state_helper = mov_imm8_to_reg(target_reg, extended_value, register_state_helper)
    return register_state_helper

def add_imm4_to_reg(target_reg, value, register_state_helper):
    # Resize the imm value to the size of the target_reg
    extended_value = extend_the_number(value, 4, register_state_helper)

    # Now that the input value is properly sized, call add_imm8_to_reg
    register_state_helper = add_imm8_to_reg(target_reg, extended_value, register_state_helper)
    return register_state_helper

def jump_on_not_equal_to_imm4(source_reg, value, register_state_helper):
    # Resize the imm value to the size of the target_reg
    extended_value = extend_the_number(value, 4, register_state_helper)

    # Now that the input value is properly sized, call jump_on_not_equal_to_imm8
    register_state_helper = jump_on_not_equal_to_imm8(source_reg, extended_value, register_state_helper)
    return register_state_helper


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