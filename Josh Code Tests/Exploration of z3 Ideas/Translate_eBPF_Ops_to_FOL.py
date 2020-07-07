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
            
        All bitvecs (for now) will model unsigned values holding numbers representing floats, not pointers
        
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

"""
from z3 import *



# # regChanges = [Int(str(i)) for i in range(4)]
# # regChanges[0] = Int('0')
# # regChanges[1] = Int('1')
# # s.add(regChanges[0] == a)
# r0 = BitVec('r0', 4)
# r1 = BitVec('r1', 4)
# r2 = BitVec('r2', 4)
# # r0 = BitVecVal(15, 4)
# # r1 = BitVecVal(15, 4)
# s.add(r0 == 7)
# s.add(r1 == 8)
# s.add(r2 == r0 + r1)

# # UGE is the z3 unsigned bitvector comparison function saying r2 >= r1
# s.add(UGE(r2, r1))
# s.check()
# print (s.model())



# # Dynamic Creation of Variable storage for SSA test code
# register_list = [[BitVec("r"+str(i) + "_0", register_bit_width)] 
#                   for i in range(number_of_registers)]
# print(register_list)

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
    print("\n\n" + changes)
    print(s.check())
    if s.check() == sat:
        print(s.model())
    else:
        print(register_list)
        
        
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
    reg_list = [[BitVec("r"+str(i) + "_0", regBitWidth)] 
                  for i in range(numRegs)]
    solver.reset()
    return solver, reg_list


def add_two_registers(source_reg, destination_reg, solver, reg_history, instruction_counter):
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
    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    
    #Adding the two registers, and including the overflow constraint
    s.add(reg_history[d_r][d_l] == reg_history[d_r][d_l-1] + reg_history[s_r][s_l-1])
    s.add(UGE(reg_history[d_r][d_l], reg_history[d_r][d_l-1]))
    return solver, reg_history

def add_two_registers_v2(source_reg, destination_reg, solver, reg_history, instruction_counter):
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

    Returns
    -------
    solver:  Type(z3 Solver Object)
        Modified to include the new value of the destination register, and a overflow check on the calculation
        
    reg_history: Type(List of lists of BitVec variables)
        Additional value appended to the destinaton_reg sublist holding the new value.
        --Note--
        The value will be calculated and added to the list regardless of overflow possibilities
            right now, unsure how this will play out in future versions
            
    instruction_counter: Type(int)
        This will always return the instruction value of the last correctly completed instruction.
        In the event of an unsat solution, this return will force a check in the main program to halt continuned execution
        by returning the problematic instruction as a negative int (there is a check in the main function for this return
                                                                    always being positive)

    """
    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    
    #Adding the two registers, and including the overflow constraint
    solver.push()  #v2 Change to allow for rollback of problematic addition
    solver.add(reg_history[d_r][d_l] == reg_history[d_r][d_l-1] + reg_history[s_r][s_l-1])
    solver.add(UGE(reg_history[d_r][d_l], reg_history[d_r][d_l-1]))
    
    # v2 Change to always check a solution before returning to the main function
    if solver.check() == unsat:
        solver.pop()
        throwaway = reg_history[d_r].pop(d_l)
        instruction_counter *= -1
        
    return solver, reg_history, instruction_counter

