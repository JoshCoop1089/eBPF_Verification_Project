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
        variable naming scheme:
            set up a 2d list which is created based on number of registers needed
                where every entry in first list will be a history tape for the specific changes to that register
                ie - 
                    register_list[0][0] is the inital state of r0
                    register_list[1][2] is the state of register r1 after 
                        2 changes have been made to it (initial would be in r_l[1][0],
                                                        first change in r_l[1][1])
            This way, you can maintain a history of register changes, use each individual entry
                as a new bitvec variable in the solver, and possibly trace back to a specific instruction
                which caused a problem
            
        All bitvecs (for now) will model unsigned values holding numbers representing floats, not pointers
        
        bpf_add:
            assumptions:
                adding two positive numbers together
            inputs:
                src register value
                dest register value
            requirments added to solver:
                dst_new = src + dst
                dst_new >= dst
                    this assumption should deal with the overflow problem, 
                    since 0xf + 0xf = 0xd  in a 4 bit container

"""
from z3 import *

s = Solver()

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

#Eventually these values will all be defined by user input to the command line
number_of_registers = 4
register_bit_width = 4
# number_of_program_commands = 4

# Dynamic Creation of Variable storage for SSA attempts
register_list = [[BitVec("r"+str(i) + "_0", register_bit_width)] 
                  for i in range(number_of_registers)]
print(register_list)


def clear_solver_reset_register_history(solver, numRegs, regBitWidth):
    reg_list = [[BitVec("r"+str(i) + "_0", register_bit_width)] 
                  for i in range(number_of_registers)]
    solver.reset()
    return solver, reg_list
def add_two_registers(source_reg, destination_reg, solver, reg_history):
    """
    Parameters
    ----------
    source_reg : Type: Int
        Which register to take the inital value from to reference the reg_history list
    
    destination_reg : Type: Int
        Which register to take the second value from, and what sublist to append
            the result of the computation to
            
    solver : Type: z3 Solver object
        Stores all the FOL choices made so far, will be modified due to 
            requiremnts of add and passed back out of function
            
    reg_history : Type: List of List of z3 bitVectors
        Holds all previous values for all registers in the program, used to 
            allow for SSA representation of register values.  Will be modified with new value
            for whatever comes out of the add calculation, to be appended to the destination_reg
            sublist

    Returns
    -------
    solver:  Modified to include the new value of the destination register, 
        and a overflow check on the calculation
    reg_history: Additional value appended to the destinaton_reg sublist holding the new value.
        --Note--
        The value will be calculated and added to the list regardless of overflow possibilities
            right now, unsure how this will play out in future versions

    """
    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(d_l), register_bit_width))
    
    #Adding the two registers, and including the overflow constraint
    s.add(reg_history[d_r][d_l] == reg_history[d_r][d_l-1] + reg_history[s_r][s_l-1])
    s.add(UGE(reg_history[d_r][d_l], reg_history[d_r][d_l-1]))
    return solver, reg_history

# Arbitrary test values for checking add function
s.add(register_list[0][0] == 7)
s.add(register_list[1][0] == 8)
s.add(register_list[2][0] == 15)
s.add(register_list[3][0] == 15)

# Add Test 1: Add register 0 and 1 (0x7 + 0x8 = 0xF, 15 stored in r1_1)
s, register_list = add_two_registers(0, 1, s, register_list) 
if s.check() == sat:
    print(s.model())
else:
    print(register_list)

# Add Test 2: Add register 2 and 3 (0xF + 0xF = 0xD because of forced 4 bit width)
                    # this test should fail due to UGE constraint, but the list should still be updated)
s, register_list = add_two_registers(2, 3, s, register_list)     
if s.check() == sat:
    print(s.model())
else:
    print(register_list)
    
s,register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
print(register_list)
# s.add(register_list[0][0] == 0)
# for num, bigListoReg in enumerate(register_list):
#     for reg in register_list[num]:
#         print(reg)
# # s.add(reg)