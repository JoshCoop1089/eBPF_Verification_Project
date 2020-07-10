# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 19:29:44 2020

@author: joshc
"""


from z3 import *
from Translate_eBPF_Ops_to_FOL import *

s = Solver()

#Eventually these values will all be defined by user input to the command line
number_of_registers = 4
register_bit_width = 4

# # Redo Tests 1-3 with v2 add function
# s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)

# # Arbitrary test values for checking add function (but now with error checking!)
# s.add(register_list[0][0] == 7)
# s.add(register_list[1][0] == 8)
# s.add(register_list[2][0] == 15)
# s.add(register_list[3][0] == 15)

# # Add Test 1: Add register 0 and 1 (0x7 + 0x8 = 0xF, 15 stored in r1_1)
#     # No changes due to v2Add
# s, register_list, instruction_counter = add_two_registers_unsigned(0, 1, s, register_list, 4, register_bit_width) 
# check_and_print_model(s, register_list, "Test 1v2: Single add, no overflow")

# # Add Test 2: Add register 2 and 3 (0xF + 0xF = 0xD because of forced 4 bit width)
#     # Changes due to v2Add: This test should return just the list of the 4 starting register values
# s, register_list, instruction_counter = add_two_registers_unsigned(2, 3, s, register_list, 5, register_bit_width) 
# print("\nThis test should return just the list of the 4 starting register values, and the changes due to test 1")    
# check_and_print_model(s, register_list, "Test 2v2: Single add, with overflow")


# Using new program loader format to test against old solver method
print("-"*20)
print("\n\n\tNow trying the auto program loader\n")
ins_list = ["init 0 7", "init 1 8", "init 2 15", "init 3 15"]

# Add Test 1
ins_list.append("addU 0 1")

# Add Test 2: This should fail, causing it to oshow the model as it would be following AddTest 1
ins_list.append("addU 2 3")

create_program(ins_list)
print("-"*20)



# # Add Test 3:  Multiple Adds to the same register (without breaking bound condition)
#     # No changes due to v2Add
# s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
# s.add(register_list[0][0] == 1)
# s.add(register_list[1][0] == 1)
# for i in range(5):
#     s, register_list, instruction_counter = add_two_registers_unsigned(0, 1, s, register_list, i+2, register_bit_width)    
# check_and_print_model(s, register_list, "Test 3v2: Multiple adds, no overflow")


# Using new program loader format to test against old solver method
print("-"*20)
print("\n\n\tNow trying the auto program loader\n")
ins_list = ["init 0 1", "init 1 1"]

# Add Test 3: 5 Consectutive adds on same register, no overflow
new_ins = ["addU 0 1" for _ in range(5)]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

# # Test 4b:  First round of changes to add function, will try to have program stop and report an error
#     # and return the problematic instruction number.  Should truncate the output list to only r1_0 through r1_4 as well
# s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
# s.add(register_list[0][0] == 3)
# s.add(register_list[1][0] == 1)
# for i in range(1,8):
#     s, register_list, instruction_counter = add_two_registers_unsigned(0, 1, s, register_list, i, register_bit_width) 
#     if (instruction_counter < 0):
#         break
# check_and_print_model(s, register_list, "Test 4b: Multiple adds, with overflow, error checks, should include up to r1_4")

# Using new program loader format to test against old solver method
print("-"*20)
print("\n\n\tNow trying the auto program loader\n")
ins_list = ["init 0 3", "init 1 1"]

# Add Test 3: 7 Consectutive adds on same register, overflow after 5 adds, should only return the 4th add
new_ins = ["addU 0 1" for _ in range(7)]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)