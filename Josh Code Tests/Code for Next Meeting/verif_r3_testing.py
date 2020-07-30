# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 11:32:54 2020

@author: joshc

Programs Passed:
    Default Program
    Program with no jumps, only add/mov
    Program with single jump, both paths converge
    
Programs Failed, bug identified:
    
Programs Failed, reasons unknown:
    Program with multiple jumps, all paths satisfiable, no convergence of paths
    Program with multiple jumps, some paths converge
    Program with multiple jumps, some paths cause unsat conditions
    Program with multiple jumps, some paths cause unsat, some paths converge
    Program with ~1000 instructions
    
"""
from Verifier_Round_3 import *

# # Basic Default Test
# print("-"*25)
# # program_list = ["movI8 4 1", "movI8 3 2", "addR 1 2", "jneI8 5 2 2", "addR 1 1", "addI4 3 2", "addR 1 2", "addR 2 1", "exit 0 0"]
# create_program()
# print("-"*25)

""" Program Outputs:
-------------------------
Attempting to combine solver with instruction #0: movI8 4 1
Attempting to combine solver with instruction #1: movI8 3 2
Attempting to combine solver with instruction #2: addR 1 2
Attempting to combine solver with instruction #3: jneI8 5 2 2
Attempting to combine solver with instruction #6: addR 1 2
Attempting to combine solver with instruction #7: addR 2 1
Attempting to combine solver with instruction #8: exit 0 0

The last instruction attempted was #8:

Program successfully added all instructions
The stored model contains the following variable states
[r2_1 = 3,
 r1_4 = 8,
 r2_2 = 7,
 r2_6_after_jump = 7,
 r2_6 = 11,
 r1_0 = 4,
 r2_5 = 10,
 r1_7 = 15,
 r1_6_after_jump = 4,
 exit_8 = True]

The register values are currently:
	Register 0:	 Not Initalized
	Register 1:	 15
	Register 2:	 11
	Register 3:	 Not Initalized


The full program in Python keyword format is:

	0:	movI8 4 1
	1:	movI8 3 2
	2:	addR 1 2
	3:	jneI8 5 2 2
	4:	addR 1 1
	5:	addI4 3 2
	6:	addR 1 2
	7:	addR 2 1
	8:	exit 0 0

This program would be written as the following for BPF in C:

BPF_MOV64_IMM(BPF_REG_1, 4), BPF_MOV64_IMM(BPF_REG_2, 3), 
BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1), BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 5, 2), 
BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1), BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, 3), 
BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1), BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2), 
BPF_EXIT_INSN(), 


-->  Elapsed Time: 0.014 seconds  <--
-------------------------
"""

# # Program with no jumps, only add/mov
# print("-"*25)
# program_list = ["movI8 1 0" , "movI8 3 1", "addR 0 1", "movI4 -1 2", "addR 2 1", "addI4 -3 2", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

""" Program Outputs:
-------------------------
Attempting to combine solver with instruction #0: movI8 1 0
Attempting to combine solver with instruction #1: movI8 3 1
Attempting to combine solver with instruction #2: addR 0 1
Attempting to combine solver with instruction #3: movI4 -1 2
Attempting to combine solver with instruction #4: addR 2 1
Attempting to combine solver with instruction #5: addI4 -3 2
Attempting to combine solver with instruction #6: exit 0 0

The last instruction attempted was #0:

Program didn't successfully add all given instructions
The stored model contains the following variable states
[r1_2 = 4,
 r1_4 = 3,
 r0_0 = 1,
 exit_6 = True,
 r2_3 = 255,
 r1_1 = 3,
 r2_5 = 252]

The register values are currently:
	Register 0:	 1
	Register 1:	 3
	Register 2:	 252
	Register 3:	 Not Initalized


The full program in Python keyword format is:

	0:	movI8 1 0
	1:	movI8 3 1
	2:	addR 0 1
	3:	movI4 -1 2
	4:	addR 2 1
	5:	addI4 -3 2
	6:	exit 0 0

This program would be written as the following for BPF in C:

BPF_MOV64_IMM(BPF_REG_0, 1), BPF_MOV64_IMM(BPF_REG_1, 3), 
BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_0), BPF_MOV64_IMM(BPF_REG_2, -1), 
BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2), BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, -3), 
BPF_EXIT_INSN(), 


-->  Elapsed Time: 0.014 seconds  <--
-------------------------
"""

# # Program with single jump, both paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 2", "addI8 1 1", "addI4 -1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

""" Program Outputs:
-------------------------
Attempting to combine solver with instruction #0: movI8 1 1
Attempting to combine solver with instruction #1: jneR 1 1 2
Attempting to combine solver with instruction #4: addR 1 1
Attempting to combine solver with instruction #5: exit 0 0

The last instruction attempted was #5:

Program successfully added all instructions
The stored model contains the following variable states
[r1_2 = 2,
 r1_0 = 1,
 exit_5 = True,
 r1_4_after_jump = 1,
 r1_4 = 2,
 r1_3 = 1]

The register values are currently:
	Register 0:	 Not Initalized
	Register 1:	 2
	Register 2:	 Not Initalized
	Register 3:	 Not Initalized


The full program in Python keyword format is:

	0:	movI8 1 1
	1:	jneR 1 1 2
	2:	addI8 1 1
	3:	addI4 -1 1
	4:	addR 1 1
	5:	exit 0 0

This program would be written as the following for BPF in C:

BPF_MOV64_IMM(BPF_REG_1, 1), BPF_JMP_REG(BPF_JNE, BPF_REG_1, BPF_REG_1, 2), BPF_ALU64_IMM(BPF_ADD, BPF_REG_1, 1), BPF_ALU32_IMM(BPF_ADD, BPF_REG_1, -1), BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1), BPF_EXIT_INSN(), 


-->  Elapsed Time: 0.013 seconds  <--
-------------------------
"""

# # Program with multiple jumps, all paths satisfiable, no convergence of paths
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 2", "addR 1 1", "addR 1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, some paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 3", "addR 1 1", "jneR 1 1 2", "addI4 -1 1", "addI8 0 1", "addI4 -1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, some paths cause unsat conditions
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 2", "addI8 3000 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Program with multiple jumps, some paths cause unsat, some paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 1", "addI8 3000 1", "addI4 -1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# # Stress Test for time and memory allocations
# print("-!"*25)
# program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 2", "addI8 3000 1", "addI4 -1 1", "addI4 -1 1", "exit 0 0"]
# for _ in range(7):
#     program_list.extend(program_list)
# create_program(program_list)