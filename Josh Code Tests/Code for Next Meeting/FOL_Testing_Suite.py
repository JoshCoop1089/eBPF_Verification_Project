# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 11:32:54 2020

@author: joshc

Programs Executed All Instructions and Matched BPF_Step:
    Default Program
    Program with no jumps, only add/mov
    Program with single jump, both paths converge
    Program with multiple jumps, jumps have overlapping endpoints
    Program with multiple jumps, same endpoint
    Program with multiple jumps, some paths converge

Program Completed, didn't run through eBPF'    
    Program with ~3600 instructions
    
Programs With Unsats that failed correctly:
    Program with multiple jumps, some paths cause unsat conditions
    Program with multiple jumps, some paths cause unsat, some paths converge
    
Programs Failed, reasons unknown:
    
"""
from FOL_from_BPF import *
from FOLTester import *
from Random_Program_Creation import *

# # Basic Default Test
# print("-"*25)
# # program_list = ["movI8 4 1", "movI8 3 2", "addR 1 2", "jmpI8 5 2 2", "addR 1 1", "addI4 3 2", "addR 1 2", "addR 2 1", "exit 0 0"]
# create_program()
# print("-"*25)

# # Program with no jumps, only add/mov
# print("-"*25)
# program_list = ["movI8 1 0" , "movI8 3 1", "addR 0 1", "movI4 -1 2", "addR 2 1", "addI4 -3 2", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with single jump, both paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jmpR 1 1 2", "addI8 1 1", "addI4 -1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, jumps have overlapping endpoints
print("-"*25)
program_list = ["movI8 1 1", "movI8 2 2", "jmpI4 1 1 3", "addR 1 2", "jmpI4 2 1 3", "addI4 4 1", "addI4 -3 1", "addR 1 2", "exit 0 0"]
print("Iterative Full SAT")
create_program(program_list, 3, 64)
print("-"*20+"\nIterative Abridged SAT")
create_program_test(program_list, 3, 64)
print("-"*25)

# # Program with multiple jumps, same endpoint
# print("-"*25)
# program_list = ["movI8 1 1", "jmpR 1 1 4", "addR 1 1", "jmpI4 4 1 2", "addR 1 1", "addR 1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, some paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jmpR 1 1 3", "addR 1 1", "jmpR 1 1 2", "addI4 -1 1", "addI8 0 1", "addI4 -1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, some paths cause unsat conditions
# print("-"*25)
# program_list = ["movI8 1 1", "jmpR 1 1 4", "addR 1 1", "jmpR 1 1 2", "addI8 3000 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, some paths cause unsat, some paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jmpR 1 1 4", "addR 1 1", "jmpR 1 1 1", "addI8 3000 1", "addI4 -1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # 3 Pred Node at end
# print("-"*25)
# program_list = ["movI4 1 1", "jmpI4 1 1 9", "addR 1 1",  "jmpI4 1 1 2", "movI8 1 1", "jmpI8 1 1 5", 
#     "addR 1 1", "jmpI4 2 1 1", "addR 1 1", "addR 1 1", "addI4 1 1", "addI8 1 1"]
# create_program(program_list)
# print("-"*25)

# # Multiple changing registers
# print("-"*25)
# program_list = ["movI8 1 1", "movI8 1 2", "jmpR 1 2 2", "addI4 2 1", "jmpR 2 1 2", "addI8 1 1", "addR 2 2", "addR 2 2", "addR 1 2"]
# create_program(program_list)
# print("-"*25)

# # Literally 70% jumps
# print("-"*25)
# # program_list = ["movI8 1 2", "jmpR 2 2 8",  "jmpR 2 2 5", "jmpI4 1 2 1", "addI4 1 2",
# #                 "jmpI4 1 2 3", "jmpR 2 2 2", "jmpI8 1 2 2", "addR 2 2", "jmpI4 1 2 1", "addR 2 2", "exit 0 0"]
# program_list = ["movI8 1 1", "movI8 1 2", "jmpR 1 2 2", "addI4 2 1", "jmpR 2 1 2", "addI8 1 1", "addR 2 2", "addR 2 2", "addR 1 2"]
# program_list.append("exit 0 0")

# create_program(program_list, 3, 64)
# print("-"*25)

# Stress Test for time and memory allocations (end program has ~3600 instructions)
# # Jump Stress Test hits tail recursion limit in python
# program_list = ["movI8 1 2", "jmpR 2 2 8",  "jmpR 2 2 5", "jmpI4 1 2 1", "addI4 1 2",
#                 "jmpI4 1 2 3", "jmpR 2 2 2", "jmpI8 1 2 2", "addR 2 2", "jmpI4 1 2 1", "addR 2 2"]
# Regular test

# for i in range(11):
#     print("\n"+ "-!- "*15)
#     program_list = ["movI8 1 1", "movI8 1 2", "jmpR 1 2 2", "addI4 2 1", "jmpR 2 1 2", "addI8 1 1", "addR 2 2", "addR 2 2", "addR 1 2"]
#     for _ in range(i+1):
#         program_list.extend(program_list)
#     program_list.append("exit 0 0")
#     print("Iterative Full SAT")
#     create_program(program_list, 3, 64)
#     print("-"*20+"\nIterative Abridged SAT")
#     create_program_test(program_list, 3, 64)
    
# print("\n"+ "-!- "*15)
# program_list.extend(program_list)
# print("-"*20+"\nIterative Abridged SAT")
# create_program_test(program_list, 3, 64)
# print("\n"+ "-!- "*15)
# program_list.extend(program_list)
# print("-"*20+"\nIterative Abridged SAT")
# create_program_test(program_list, 3, 64)
# print("\n"+ "-!- "*15)
# program_list.extend(program_list)
# print("-"*20+"\nIterative Abridged SAT")
# create_program_test(program_list, 3, 64)



# # Random Program time! Who knows if they work, it's a mystery.  But, will they run!?!?!
# print("-"*25)
# num_ins = 100
# num_regs = 4
# reg_size = 8
# # program_list = ['movI8 114 0', 'jmpI4 18 0 1', 'jmpR 0 0 5', 'addR 0 0', 'movI8 -70 1', 'jmpI8 54 0 3', 'movI4 76 7', 'addR 1 0', 'addI4 -98 7', 'exit 0 0']

# program_list = random_program_creator(num_ins, num_regs, reg_size)
# create_program(program_list, num_regs, reg_size)
# print("-"*25)