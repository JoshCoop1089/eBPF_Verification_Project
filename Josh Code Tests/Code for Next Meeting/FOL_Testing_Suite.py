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
# print("-"*25)
# program_list = ["movI8 1 1", "movI8 2 2", "jmpI4 1 1 3", "addR 1 2", "jmpI4 2 1 3", "addI4 4 1", "addI4 -3 1", "addR 1 2", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

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

# # Multiple variables need phi functions
# print("-"*25)
# program_list = ["movI8 1 1", "movI8 1 2", "jmpR 1 2 2", "addI4 2 1", "jmpR 2 1 2", "addI8 1 1", "addR 2 2", "addR 2 2", "addR 1 2"]
# create_program(program_list)
# print("-"*25)

# Stress Test for time and memory allocations (end program has ~3600 instructions)
print("-!"*25)
program_list = ["movI8 1 1", "jmpR 1 1 4", "addI8 1 1", "jmpR 1 1 2", "addI4 -1 1", "addI8 1 1", "addI4 -1 1"]
for _ in range(9):
    program_list.extend(program_list)
program_list.append("exit 0 0")
create_program(program_list)

