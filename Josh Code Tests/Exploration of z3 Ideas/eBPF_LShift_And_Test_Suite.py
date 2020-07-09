# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 23:03:12 2020

@author: joshc
"""


from z3 import *
from Translate_eBPF_Ops_to_FOL import *


s = Solver()

#Eventually these values will all be defined by user input to the command line
number_of_registers = 4
register_bit_width = 4

s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)

# Arbitrary test values for checking functions
s.add(register_list[0][0] == 7)
s.add(register_list[1][0] == 1)
s.add(register_list[2][0] == 15)
s.add(register_list[3][0] == 15)


# Left Shift Tests
s, register_list, instruction_counter = left_shift_register_value(0, 1, s, register_list, 1, register_bit_width)
check_and_print_model(s, register_list, "Test 1: Left shifting 7 by 1 bits, should give 14 as the val in r0_1")

s, register_list, instruction_counter = left_shift_register_value(1, 2, s, register_list, 2, register_bit_width)
check_and_print_model(s, register_list, "Test 2: Left shifting 1 by 2 bits, should give 4 as the val in r1_2")

s, register_list, instruction_counter = left_shift_register_value(2, 1, s, register_list, 3, register_bit_width)
check_and_print_model(s, register_list, "Test 3: Left shifting 15 by 1 bits, should give 14 as the val in r2_3")

s, register_list, instruction_counter = left_shift_register_value(3, 6, s, register_list, 4, register_bit_width)
check_and_print_model(s, register_list, "Test 4: Left shifting 15 by 6 bits, should give unsat as shift is greater than bit_width,\
                      and should not update register history with an r3_4")

# Test 2 and 3 fail when I have         
# solver.add(new_val >= LShR(new_val, shift_val))
# enabled in the function, but passes as expected when the above condition is commented out
# unsure if problem is due to my logic, use of the lshr function, something with how z3 deals
# with the same variable showing up in the add, or something else entirely


# And Operation Tests
s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)

# Arbitrary test values for checking functions
s.add(register_list[0][0] == 6)
s.add(register_list[1][0] == 1)
s.add(register_list[2][0] == 15)
s.add(register_list[3][0] == 15)


s, register_list, instruction_counter = and_two_registers(2, 3, s, register_list, 1, register_bit_width)
check_and_print_model(s, register_list, "Test 1: 15&15, should give 15 as the val in r3_1")

s, register_list, instruction_counter = and_two_registers(0, 1, s, register_list, 2, register_bit_width)
check_and_print_model(s, register_list, "Test 2: 6&1, should give 0 as the val in r1_2")






