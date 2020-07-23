# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 11:32:54 2020

@author: joshc

Individual Programs Start on line:
    15:  Default Program
    141: Program with no jumps, only add/mov
    217: Program with multiple jumps, all paths satisfiable, no convergence of paths
    364: Program with single jump, both paths converge
"""
from Verifier_Round_3 import *

# # Basic Default Test
# print("-"*25)
# # program_list = ["movI8 4 1", "movI8 3 2", "addR 1 2", "jneI8 5 2 2", "addR 1 1", "addI4 3 2", "addR 1 2", "addR 2 1", "exit 0 0"]
# create_program()
# print("-"*25)

# """ Program Outputs:
# -------------------------

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #0: movI8 4 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #1: movI8 3 2

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #2: addR 1 2

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #3: jneI8 5 2 2

# --> Creating a new branch starting at instruction #3 <--


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #4: addR 1 1

# Looking at Branch 1
# 	Skipping instruction 4 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #5: addI4 3 2
# 	Extending the smaller bitVector value to match reg size

# Looking at Branch 1
# 	Skipping instruction 5 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #6: addR 1 2

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #6: addR 1 2

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #7: addR 2 1

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #7: addR 2 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #8: exit 0 0

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #8: exit 0 0

# --> Output for Branch 0 <--

# The last instruction attempted was #8:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r2_1 = 3,
#  r1_4 = 8,
#  r2_2 = 7,
#  r2_6 = 18,
#  r1_0 = 4,
#  r2_5 = 10,
#  r1_7 = 26,
#  exit_8 = True]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 26
# Register 2:	 18
# Register 3:	 Not Initalized



# --> Output for Branch 1 <--

# The last instruction attempted was #8:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r2_1 = 3,
#  r1_0 = 4,
#  r1_7 = 15,
#  r2_2 = 7,
#  exit_8 = True,
#  r2_6 = 11]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 15
# Register 2:	 11
# Register 3:	 Not Initalized



# The full program in Python keyword format is:
# 0:	movI8 4 1
# 1:	movI8 3 2
# 2:	addR 1 2
# 3:	jneI8 5 2 2
# 4:	addR 1 1
# 5:	addI4 3 2
# 6:	addR 1 2
# 7:	addR 2 1
# 8:	exit 0 0

# This program would be written as the following for BPF in C:

# ['BPF_MOV64_IMM(BPF_REG_1, 4)', 
#  'BPF_MOV64_IMM(BPF_REG_2, 3)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1)', 
#  'BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 5, 2)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#  'BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, 3)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2)', 
#  'BPF_EXIT_INSN()']
# -------------------------
# """

# # Program with no jumps, only add/mov
# print("-"*25)
# program_list = ["movI8 1 0" , "movI8 3 1", "addR 0 1", "movI4 -1 2", "addR 2 1", "addI4 -3 2", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# """ Program Outputs:
# -------------------------

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #0: movI8 1 0

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #1: movI8 3 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #2: addR 0 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #3: movI4 -1 2
# 	Extending the smaller bitVector value to match reg size

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #4: addR 2 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #5: addI4 -3 2
# 	Extending the smaller bitVector value to match reg size

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #6: exit 0 0

# --> Output for Branch 0 <--

# The last instruction attempted was #6:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r1_2 = 4,
#  r1_4 = 3,
#  r0_0 = 1,
#  exit_6 = True,
#  r2_3 = 255,
#  r1_1 = 3,
#  r2_5 = 252]

# The register values are currently:
# Register 0:	 1
# Register 1:	 3
# Register 2:	 252
# Register 3:	 Not Initalized



# The full program in Python keyword format is:
# 0:	movI8 1 0
# 1:	movI8 3 1
# 2:	addR 0 1
# 3:	movI4 -1 2
# 4:	addR 2 1
# 5:	addI4 -3 2
# 6:	exit 0 0

# This program would be written as the following for BPF in C:

# ['BPF_MOV64_IMM(BPF_REG_0, 1)', 
#  'BPF_MOV64_IMM(BPF_REG_1, 3)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_0)', 
#  'BPF_MOV64_IMM(BPF_REG_2, -1)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2)', 
#  'BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, -3)', 
#  'BPF_EXIT_INSN()']
# -------------------------
# """

# # Program with multiple jumps, all paths satisfiable, no convergence of paths
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 2", "addR 1 1", "addR 1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# """ Program Outputs:
# -------------------------

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #0: movI8 1 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #1: jneR 1 1 4

# --> Creating a new branch starting at instruction #1 <--


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #2: addR 1 1

# Looking at Branch 1
#  	Skipping instruction 2 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #3: jneR 1 1 2

# --> Creating a new branch starting at instruction #3 <--


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #4: addR 1 1

# Looking at Branch 1
#  	Skipping instruction 4 due to jump condition


# Looking at Branch 2
#  	Skipping instruction 4 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #5: addR 1 1

# Looking at Branch 1
#  	Skipping instruction 5 due to jump condition


# Looking at Branch 2
#  	Skipping instruction 5 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #6: addR 1 1

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #6: addR 1 1

# Looking at Branch 2
# Attempting to combine Branch 2 with instruction #6: addR 1 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #7: exit 0 0

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #7: exit 0 0

# Looking at Branch 2
# Attempting to combine Branch 2 with instruction #7: exit 0 0

# --> Output for Branch 0 <--

# The last instruction attempted was #7:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r1_6 = 16,
#   r1_2 = 2,
#   r1_0 = 1,
#   r1_4 = 4,
#   r1_5 = 8,
#   exit_7 = True]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 16
# Register 2:	 Not Initalized
# Register 3:	 Not Initalized



# --> Output for Branch 1 <--

# The last instruction attempted was #7:

# Program successfully added all instructions
# The stored model contains the following variable states
# [exit_6 = True, r1_0 = 1, r1_5 = 2]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 2
# Register 2:	 Not Initalized
# Register 3:	 Not Initalized



# --> Output for Branch 2 <--

# The last instruction attempted was #7:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r1_6 = 4, r1_2 = 2, r1_0 = 1, exit_7 = True]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 4
# Register 2:	 Not Initalized
# Register 3:	 Not Initalized



# The full program in Python keyword format is:
# 0:	movI8 1 1
# 1:	jneR 1 1 4
# 2:	addR 1 1
# 3:	jneR 1 1 2
# 4:	addR 1 1
# 5:	addR 1 1
# 6:	addR 1 1
# 7:	exit 0 0

# This program would be written as the following for BPF in C:

# ['BPF_MOV64_IMM(BPF_REG_1, 1)', 
#   'BPF_JMP_REG(BPF_JNE, BPF_REG_1, BPF_REG_1, 4)', 
#   'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#   'BPF_JMP_REG(BPF_JNE, BPF_REG_1, BPF_REG_1, 2)', 
#   'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#   'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#   'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#   'BPF_EXIT_INSN()']
# """

# # Program with single jump, both paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 2", "addI8 1 1", "addI4 -1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# """ Program Outputs
# -------------------------

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #0: movI8 1 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #1: jneR 1 1 2

# --> Creating a new branch starting at instruction #1 <--


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #2: addI8 1 1

# Looking at Branch 1
#  	Skipping instruction 2 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #3: addI4 -1 1
#  	Extending the smaller bitVector value to match reg size

# Looking at Branch 1
#  	Skipping instruction 3 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #4: addR 1 1

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #4: addR 1 1
#  	After Instruction #4, Branch 1 has the same values stored as another branch.
#  	Removing the branch to lighten the calculation load

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #5: exit 0 0

# --> Output for Branch 0 <--

# The last instruction attempted was #5:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r1_2 = 2, r1_0 = 1, exit_5 = True, r1_4 = 2, r1_3 = 1]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 2
# Register 2:	 Not Initalized
# Register 3:	 Not Initalized



# The full program in Python keyword format is:
# 0:	movI8 1 1
# 1:	jneR 1 1 2
# 2:	addI8 1 1
# 3:	addI4 -1 1
# 4:	addR 1 1
# 5:	exit 0 0

# This program would be written as the following for BPF in C:

# ['BPF_MOV64_IMM(BPF_REG_1, 1)', 
#   'BPF_JMP_REG(BPF_JNE, BPF_REG_1, BPF_REG_1, 2)', 
#   'BPF_ALU64_IMM(BPF_ADD, BPF_REG_1, 1)', 
#   'BPF_ALU32_IMM(BPF_ADD, BPF_REG_1, -1)', 
#   'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#   'BPF_EXIT_INSN()']
# -------------------------
# """

# # Program with multiple jumps, some paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 3", "addR 1 1", "jneR 1 1 2", "addI4 -1 1", "addI8 0 1", "addI4 -1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)

# """ Program Outputs:
# -------------------------

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #0: movI8 1 1

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #1: jneR 1 1 3

# --> Creating a new branch starting at instruction #1 <--


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #2: addR 1 1

# Looking at Branch 1
# 	Skipping instruction 2 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #3: jneR 1 1 2

# --> Creating a new branch starting at instruction #3 <--


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #4: addI4 -1 1
# 	Extending the smaller bitVector value to match reg size

# Looking at Branch 1
# 	Skipping instruction 4 due to jump condition


# Looking at Branch 2
# 	Skipping instruction 4 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #5: addI8 0 1

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #5: addI8 0 1

# Looking at Branch 2
# 	Skipping instruction 5 due to jump condition


# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #6: addI4 -1 1
# 	Extending the smaller bitVector value to match reg size

# Looking at Branch 1
# Attempting to combine Branch 1 with instruction #6: addI4 -1 1
# 	Extending the smaller bitVector value to match reg size

# Looking at Branch 2
# Attempting to combine Branch 2 with instruction #6: addI4 -1 1
# 	Extending the smaller bitVector value to match reg size
# 	After Instruction #6, Branch 1 has the same values stored as another branch.
# 	Removing the branch to lighten the calculation load

# Looking at Branch 0
# Attempting to combine Branch 0 with instruction #7: exit 0 0

# Looking at Branch 1
# Attempting to combine Branch 2 with instruction #7: exit 0 0

# --> Output for Branch 0 <--

# The last instruction attempted was #7:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r1_6 = 0,
#  r1_2 = 2,
#  r1_0 = 1,
#  r1_4 = 1,
#  r1_5 = 1,
#  exit_7 = True]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 0
# Register 2:	 Not Initalized
# Register 3:	 Not Initalized



# --> Output for Branch 2 <--

# The last instruction attempted was #7:

# Program successfully added all instructions
# The stored model contains the following variable states
# [r1_6 = 1, r1_2 = 2, r1_0 = 1, exit_7 = True]

# The register values are currently:
# Register 0:	 Not Initalized
# Register 1:	 1
# Register 2:	 Not Initalized
# Register 3:	 Not Initalized



# The full program in Python keyword format is:
# 0:	movI8 1 1
# 1:	jneR 1 1 3
# 2:	addR 1 1
# 3:	jneR 1 1 2
# 4:	addI4 -1 1
# 5:	addI8 0 1
# 6:	addI4 -1 1
# 7:	exit 0 0

# This program would be written as the following for BPF in C:

# ['BPF_MOV64_IMM(BPF_REG_1, 1)', 
#  'BPF_JMP_REG(BPF_JNE, BPF_REG_1, BPF_REG_1, 3)', 
#  'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1)', 
#  'BPF_JMP_REG(BPF_JNE, BPF_REG_1, BPF_REG_1, 2)', 
#  'BPF_ALU32_IMM(BPF_ADD, BPF_REG_1, -1)', 
#  'BPF_ALU64_IMM(BPF_ADD, BPF_REG_1, 0)', 
#  'BPF_ALU32_IMM(BPF_ADD, BPF_REG_1, -1)', 
#  'BPF_EXIT_INSN()']
# -------------------------
# """

# Program with multiple jumps, some paths cause unsat conditions
print("-"*25)
program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 2", "addI8 3000 1", "addR 1 1", "exit 0 0"]
create_program(program_list)
print("-"*25)

# # Program with multiple jumps, some paths cause unsat, some paths converge
# print("-"*25)
# program_list = ["movI8 1 1", "jneR 1 1 4", "addR 1 1", "jneR 1 1 2", "addR 1 1", "addR 1 1", "exit 0 0"]
# create_program(program_list)
# print("-"*25)