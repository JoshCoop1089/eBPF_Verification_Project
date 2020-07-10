# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 19:29:44 2020

@author: joshc
"""


from z3 import *
from Translate_eBPF_Ops_to_FOL import *


# Using new program loader format to test against old solver method
print("-"*20)
print("\n\n\tNow trying the auto program loader\n")
ins_list = ["init 0 7", "init 1 8", "init 2 15", "init 3 15"]

# Add Test 1: Add register 0 and 1 (0x7 + 0x8 = 0xF, 15 stored in r1_1)
ins_list.append("addU 0 1")

# Add Test 2:  Add register 2 and 3 (0xF + 0xF = 0xD because of forced 4 bit width)
    # This should fail, causing it to show the model as it would be following AddTest 1
ins_list.append("addU 2 3")

create_program(ins_list)
print("-"*20)


# Using new program loader format to test against old solver method
print("-"*20)
print("\n\n\tNow trying the auto program loader\n")
ins_list = ["init 0 1", "init 1 1"]

# Add Test 3: 5 Consectutive adds on same register, no overflow
new_ins = ["addU 0 1" for _ in range(5)]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)

# Using new program loader format to test against old solver method
print("-"*20)
print("\n\n\tNow trying the auto program loader\n")
ins_list = ["init 0 3", "init 1 1"]

# Add Test 4: 7 Consectutive adds on same register, overflow after 5 adds, should only return the 4th add
new_ins = ["addU 0 1" for _ in range(7)]
ins_list.extend(new_ins)

create_program(ins_list)
print("-"*20)