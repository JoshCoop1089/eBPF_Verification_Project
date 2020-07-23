# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 13:15:51 2020

@author: joshc
"""


from z3 import *
from Translate_eBPF_Ops_to_FOL import *

s = Solver()
a, b, c = Bools('a b c')
# condition = Or(a,b)
# condition2 = And(a,b)
# func =  And(condition, condition2)
# s.add(Not(condition))
# prove(func)



#Eventually these values will all be defined by user input to the command line
number_of_registers = 3
register_bit_width = 4

# s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)

# # Arbitrary test values for checking add function
# condition = register_list[2][0] == register_list[0][0] + register_list[1][0]
# bounds = [UGE(register_list[2][0], register_list[1][0]), UGE(register_list[2][0], register_list[1][0])]
# # u_bounds = [And(register_list[2][0] >= 0, register_list[2][0] < 3)]
# func = condition
# for i in bounds:
#     func = And(i, func)
# # for i in u_bounds:
# #     func = And(i, func)
# print(func)
# prove(func)

def add_register_values(source_reg, destination_reg, function, reg_history, instruction_counter, register_bit_width):

    s_r = source_reg
    s_l = len(reg_history[s_r])
    d_r = destination_reg
    d_l = len(reg_history[d_r])
    
    source_val = reg_history[s_r][s_l-1]
    destination_old_val = reg_history[d_r][d_l-1]
    
    #Extending the destination register sublist to include the new updated register value
    reg_history[d_r].append(BitVec("r"+str(d_r) + "_" + str(instruction_counter), register_bit_width))
    destination_new_val = reg_history[d_r][d_l]
    

    
    #Adding the two registers, and including the overflow constraint assuming unsigned ints in the register
    condition = destination_new_val == destination_old_val + source_val
    constraint = UGE(destination_new_val, destination_old_val)
    
    check_func = function
    check_func = And(check_func, condition, constraint)
    
    if prove(check_func) != proved:
        instruction_counter *= -1
    else:
        function = check_func
    return function, instruction_counter, reg_history
    
# function = register_list[0][0] == 1
# function, instruction_counter, reg_history = add_register_values(0, 1, function, register_list, 1, 4)
# prove(function)

# numRegs = 3
# reg_list = [[Bool("r"+str(i) + "_0")] for i in range(numRegs)]

# # ((a^b) -> c) <-> (a->(b->c))
# # chunk1 -> chunk2 and chunk 2 -> chunk 1

# chunk1a = And(reg_list[0][0], reg_list[1][0])
# chunk1b = Implies(chunk1a, reg_list[2][0])
# chunk1 = Implies(chunk1a, chunk1b)

# chunk2b = Implies(reg_list[1][0], reg_list[2][0])
# chunk2 = Implies(reg_list[0][0], chunk2b)

# l2r = Implies(chunk1, chunk2)
# r2l = Implies(chunk2, chunk1)

# func = And(l2r, r2l)

# a -> b ^ ~a -> c

func = And(Implies(a, b), Implies(Not(a), c))
# pro1ve(func)
s.check()
try:
    print(s.model()[d])
except Z3Exception:
    print("oops")
    
print(2*3-1)