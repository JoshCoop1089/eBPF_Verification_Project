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
# number_of_program_commands = 4

s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
# print(register_list)

# Arbitrary test values for checking add function
s.add(register_list[0][0] == 7)
s.add(register_list[1][0] == 8)
s.add(register_list[2][0] == 15)
s.add(register_list[3][0] == 15)

# Add Test 1: Add register 0 and 1 (0x7 + 0x8 = 0xF, 15 stored in r1_1)
s, register_list = add_two_registers(0, 1, s, register_list, 1) 
check_and_print_model(s, register_list, "Test 1: Single add, no overflow")

# Add Test 2: Add register 2 and 3 (0xF + 0xF = 0xD because of forced 4 bit width)
                    # this test should fail due to UGE constraint, but the list should still be updated)
s, register_list = add_two_registers(2, 3, s, register_list, 2)     
check_and_print_model(s, register_list, "Test 2: Single add, with overflow")
    

# Add Test 3:  Multiple Adds to the same register (without breaking bound condition)
s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
s.add(register_list[0][0] == 1)
s.add(register_list[1][0] == 1)
for i in range(5):
    s, register_list = add_two_registers(0, 1, s, register_list, i+1) 
    
check_and_print_model(s, register_list, "Test 3: Multiple adds, no overflow")

    
# Add Test 4: Multiple Adds to the same register, but causing an overflow
        # Test 4a: No changes made to add function yet, should just produce unsat and print list including r1_0 through r1_7
s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
s.add(register_list[0][0] == 3)
s.add(register_list[1][0] == 1)
for i in range(7):
    s, register_list = add_two_registers(0, 1, s, register_list, i+1) 
check_and_print_model(s, register_list, "Test 4a: Multiple adds, with overflow, no error checks")

    
# Test 4b:  First round of changes to add function, will try to have program stop and report an error
    # and return the problematic instruction number.  Should truncate the output list to only r1_0 through r1_4 as well
s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
s.add(register_list[0][0] == 3)
s.add(register_list[1][0] == 1)
for i in range(1,8):
    s, register_list, instruction_counter = add_two_registers_v2(0, 1, s, register_list, i) 
    if (instruction_counter < 0):
        print("\n\nModel becomes unsat after instruction: " + str(instruction_counter*-1))
        print("Printing the valid model up to, but not including, the broken instruction")
        break
check_and_print_model(s, register_list, "Test 4b: Multiple adds, with overflow, error checks")

# Redo Tests 1-3 with v2 add function
s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)

# Arbitrary test values for checking add function (but now with error checking!)
s.add(register_list[0][0] == 7)
s.add(register_list[1][0] == 8)
s.add(register_list[2][0] == 15)
s.add(register_list[3][0] == 15)

# Add Test 1: Add register 0 and 1 (0x7 + 0x8 = 0xF, 15 stored in r1_1)
    # No changes due to v2Add
s, register_list, instruction_counter = add_two_registers_v2(0, 1, s, register_list, 1) 
check_and_print_model(s, register_list, "Test 1v2: Single add, no overflow")

# Add Test 2: Add register 2 and 3 (0xF + 0xF = 0xD because of forced 4 bit width)
    # Changes due to v2Add: This test should return just the list of the 4 starting register values
s, register_list, instruction_counter = add_two_registers_v2(2, 3, s, register_list, 2) 
check_and_print_model(s, register_list, "Test 2v2: Single add, with overflow")
print("This test should return just the list of the 4 starting register values, and the changes due to test 1")    
    

# Add Test 3:  Multiple Adds to the same register (without breaking bound condition)
    # No changes due to v2Add
s, register_list = clear_solver_reset_register_history(s, number_of_registers, register_bit_width)
s.add(register_list[0][0] == 1)
s.add(register_list[1][0] == 1)
for i in range(5):
    s, register_list, instruction_counter = add_two_registers_v2(0, 1, s, register_list, i+1) 
    
check_and_print_model(s, register_list, "Test 3v2: Multiple adds, no overflow")
