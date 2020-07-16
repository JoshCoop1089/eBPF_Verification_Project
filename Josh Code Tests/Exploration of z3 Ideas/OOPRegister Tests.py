# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 14:29:11 2020

@author: joshc
"""

from z3 import *
from Translate_eBPF_Ops_to_FOL import *
def BPF_JMP_IMM (opcode, source, value, offset):
    
    """
    How to define a branching instruction:
        The opcode would tell how the function would interact with the source, compared
        to the input value, but for simplicity at the moment, we're only going to model JNE for now
    IE v1 for this function will simply check source_val == value, if yes, it will execute the 
        next instruction in the instruction list, otherwise it will send out a signal to skip
    
    """
    

class Register_Info:
    def __init__(self, name, reg_bit_size,  reg_type = ""):
        self.name = BitVec(name, reg_bit_size)
        self.reg_bit_size = reg_bit_size
        self.reg_type = reg_type
        
        
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
    reg_list : Type(List of Lists of Register_Info objects)
        Clean slate to allow for a look at the progress of a new collection of bpf commands,
        and their effects on register values.

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
    reg_list = [[Register_Info("r"+str(i) + "_0", regBitWidth)] for i in range(numRegs)]
    
    return reg_list   

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
        reg_history[source_reg].append(Register_Info("r"+str(source_reg) + "_" + str(instruction_counter), register_bit_width))
    
    s_r = reg_history[source_reg][-1].name
    
    # Checking to make sure an input value will fit inside the chosen register
    # Accounts for max unsigned possible, and min signed possible values for the specified register
    if register_value < 2 ** register_bit_width and register_value >= (-1) * (2 ** (register_bit_width - 1)): 
        solver.add(s_r == register_value)
    else:
        instruction_counter *= -1
    return solver, instruction_counter   

    
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
    source_val = reg_history[s_r][s_l-1].name        #Now holds a bitVec variable to be passed into the solver
    
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
        destination_old_val = reg_history[d_r][d_l-1].name

    #Extending the destination register sublist to include the new register name
    # Previous if/else clause was to make this line work for one and two reg operations
    reg_history[d_r].append(Register_Info("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    
    # Since the destination subreg list was extended, d_l, which used to be the length of the old sublist,
        # now references the last element in the extended sublist
    destination_new_val = reg_history[d_r][d_l].name
    
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
    list_of_nums, reg_history = \
        get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg)
    
    #Allow for rollback in event of problematic addition
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

    #Always check a solution before returning to the main function
    if solver.check() == unsat:
        # Roll back the solver to a version before the problematic add instructions
        solver.pop()

        # Remove the register update because it causes a problem
        del reg_history[destination_reg][-1]

        # Special return value to tell the main test program that an error has occured
        instruction_counter *= -1

    return solver, reg_history, instruction_counter

def add_two_registers_signed(source_reg, destination_reg, solver, reg_history, instruction_counter, register_bit_width):
    """
    Purpose: Add two register values together, treating the numbers as signed bitValues
    
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
    list_of_nums, reg_history = \
        get_the_nums(reg_history, instruction_counter, register_bit_width, source_reg, destination_reg)
    
    #Allow for rollback in event of problematic addition
    """Does having this occur every time the instruction is called, even on valid
    adds, somehow pollute the solver with unneeded checks?  Efficiency question for later."""
    solver.push()
    
    #Here there be dragons
    #Adding the two registers, and including the overflow constraint assuming signed ints in the register
    # list_of_nums = [source_val, destination_old_val, destination_new_val]
    solver.add(list_of_nums[2] == list_of_nums[1] + list_of_nums[0])
    
    
    """What does overflow mean:
        src pos + dst pos --> dst_new >= dst_old
            technically 7 is the largest positive in 4 bit 2's comp,
            so 4 + 4 would overflow, 0100 + 0100 = 1000 (ie 4 + 4 = -8)
        src pos dst neg --> 7 + -1 --> dst_new >= dst_old
                        --> 1 + -8 also works as above
        src neg, dst pos --> -1 + 7 --> dst_old > dst_new
                        This one cannot be >= because if dst = 0, 
                        then new cannot be equal to it since negs start at -1
        src neg, dst neg --> -1 + -5 --> dst_old > dst_new
        
        So the breaking point is based on the sign of the src register (ie not the one being written into)
        
        sign(src) = pos -> (dst_new > dst_old)
        Implies(a,b): a is src_val >= 0, b is dst_new > dst_old
        sign(src) = neg -> (dst_new <= dst_old)
        Implies(a,b): a is src_val < 0, b is dst_old >= dst new
        """
    # First attempt at signed overflow FOL considerations
    # list_of_nums = [source_val, destination_old_val, destination_new_val]
    
    # Source_reg holds 0 or positive number in 2's complement
    a = list_of_nums[0] >= 0
    b = list_of_nums[2] > list_of_nums[1]
    pos_overflow = Implies(a,b)
    solver.add(pos_overflow)
        
    # Source_reg holds negative number in 2's complement
    a = list_of_nums[0] < 0
    b = list_of_nums[2] <= list_of_nums[1]
    neg_overflow = Implies(a,b)
    solver.add(neg_overflow)
    
    #Here ends dragons
    
    
    #Always check a solution before returning to the main function
    if solver.check() == unsat:
        # Roll back the solver to a version before the problematic add instructions
        solver.pop()

        # Remove the register update because it causes a problem
        del reg_history[destination_reg][-1]

        # Special return value to tell the main test program that an error has occured
        instruction_counter *= -1
    
    return solver, reg_history, instruction_counter

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
    reg_bit_width = 6
    
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
        3) Set the initial value of register 2 to -1             (init 2 -1)  /* r2 = -1*/
        4) Add the signed value of register 2 into register 1    (addS 2 1)   /* r1 += r2 */
        """   
    
    # Arbitrary program to test.  Using specific keyword and dual number pairs will act as ebpf instructions for execute program
    # Future updates will change this to either have a built in example program, or user defined programs able to be added
    if program_list == "":
        program_list =["init 0 1" , "init 1 3", "addU 0 1", "init 2 -1", "addS 2 1"]
    
    execute_program(program_list, s, reg_list, reg_bit_width)
    
create_program()

# s = Solver()
# regBitWidth = 4
# numRegs = 4
# reg_list = [[Register_Info("r"+str(i) + "_0", regBitWidth)] for i in range(numRegs)]
# for i in reg_list:
#     print(i[0].name)
#     print(i[0].reg_type)
    
# a = BitVecVal( 0xF, 8)
# s.add(reg_list[0][-1].name == 4)
# s.add(reg_list[1][-1].name == 9)
# s.add(reg_list[2][-1].name == 65)
# s.add(reg_list[3][-1].name == 0xF)
# s.add(reg_list[3][-1].name == -1)
# print(s.check())
# if s.check():
#     print(s.model())
