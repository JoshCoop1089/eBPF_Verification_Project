# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 19:29:44 2020

@author: joshc
"""


from z3 import *
from Translate_eBPF_Ops_to_FOL import *


# Using new program loader format to test solver method
print("-"*20)

# create_program default function test
create_program()
print("-"*20)

# Setting the start values for tests 1 and 2
ins_list = ["init 0 7", "init 1 8", "init 2 15", "init 3 15"]

print("Add Test 1: Add register 0 and 1 (0x7 + 0x8 = 0xF, 15 stored in r1_4)")
ins_list.append("addU 0 1")

print("Add Test 2:  Add register 2 and 3 (0xF + 0xF = 0xD because of forced 4 bit width)")
print("This should fail, causing it to show the model as it would be following AddTest 1\n")
ins_list.append("addU 2 3")

create_program(ins_list)
print("-"*20)

print("Test 3: 5 Consectutive adds on same register, no overflow\n")

# Setting the start values for test 3
ins_list = ["init 0 1", "init 1 2"]

# Creating the add instructions
new_ins = ["addU 0 1" for _ in range(5)]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

print("Add Test 4: 7 Consectutive adds on same register, overflow after 5 adds, should " +\
          "return up to and including the 4th add\n")

# Setting the start values for test 4
ins_list = ["init 0 3", "init 1 1"]

# Creating the add instructions
new_ins = ["addU 0 1" for _ in range(7)]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

 # Due to the output of z3 Solver object, it seems to always be reporting an unsigned 
 # representation of the bitVec.  It's still correct in 2's complement, but might be 
 # useful to figure out how to change the output characteristics of the model
print("Test 5: Signed addition of two positives, no overflow\n")

# Setting the start values for test 3
ins_list = ["init 0 1", "init 1 2"]

# Creating the add instructions
new_ins = ["addS 0 1"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

# Signed Addition Tests
print("Test 6: Signed addition of two negatives, no overflow\n")

ins_list = ["init 0 -1", "init 1 -2"]
new_ins = ["addS 0 1"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

print("Test 7: Signed addition of source pos, destination neg, no overflow\n")

ins_list = ["init 0 1", "init 1 -2"]
new_ins = ["addS 0 1"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

print("Test 8: Signed addition of source neg, destination pos, no overflow\n")

ins_list = ["init 0 -1", "init 1 2"]
new_ins = ["addS 0 1"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

# Overflow testing time
print("Test 9: Signed addition of two positives, overflow\n")

ins_list = ["init 0 4", "init 1 4"]
new_ins = ["addS 0 1"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

print("Test 10: Signed addition of two negatives, overflow\n")

ins_list = ["init 0 -5", "init 1 -5"]
new_ins = ["addS 0 1"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

# Combo Signed/unsigned Tests
print("Test 11: Funky Test Time.  Combination of Signed and Unsigned addition, no overflow\n")

ins_list = ["init 0 -5", "init 1 -5", "init 2 3"]
# 3 + 3 -> 6 + -5 -> 1 + 11 -> 12 in r2_5
new_ins = ["addS 2 2", "addS 0 2", "addU 1 2"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

print("Test 12: Funky Test Time.  Combination of Signed and Unsigned addition, high positive overflow\n")

ins_list = ["init 0 -5", "init 1 -5", "init 2 3"]
# 3 + 3 -> 6 + -5 -> 1 + 11 -> 12 in r2_5, because it will attempt 11 + 12 and fail to make r2_6
new_ins = ["addS 2 2", "addS 0 2", "addU 1 2", "andU 1 2"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

print("Test 12: Funky Test Time.  Combination of Signed and Unsigned addition, low negative overflow\n")

ins_list = ["init 0 -5", "init 1 -5", "init 2 3"]
# 3 + 3 -> 6 + -5 -> 1 + 11 -> 12 in r2_5, because it will attempt -5 + -4 and fail to make r2_6
new_ins = ["addS 2 2", "addS 0 2", "addU 1 2", "addS 1 2"]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

