# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 19:32:21 2020

@author: joshc

----------------------------------------------        

Instructions for use of Basic_Block_CFG_Creator and FOL_from_BPF

These two files combine to allow for the evaluation of an eBPF program, 
    and the simulation of the internal states of the registers modified by that program.
    
****REQUIRED***
networkX library -- https://networkx.github.io/documentation/stable/install.html
    pip install networkx
    
z3Py library -- https://github.com/Z3Prover/z3
    pip install z3-solver
    
time, copy, re  -- should be included with Python    


----------------------------------------------        

Specifics for each individual file:
    
Basic_Block_CFG_Creator:
    
    This file handles the creation of the control flow representation of the instruction list
    It is based on the networkX library, and as such is very efficient.
    
    As of right now, I have not used phi functions to describe possible values for registers,
        however, I have included the code to locate and name the phi function registers in 
        this file, for when the next person extends this program to a larger scale z3 function interpretation.
        
    Visualization options:
        In the function set_up_basic_block_cfg, there is a commented out portion just before the return statement.
        The nx.draw_planar functions outputs a visual representation of the control flow graph
            for the inputed program list.
            
        You can view it in either individual instruction form, or basic block connector form.
        
FOL_from_BPF:
    
    This handles the interpretation of individual instructions, and the calculation of new values.
    Most of this code I wrote from scratch, and as such it probably has a lot more room to improve
        compared to Basic_Block.
        
    In it's current state, it will take in a list of strings representing an eBPF program, and execute
        said program, returning the results stored in each register.
        
    You can also specify any starting calues you want the registers to hold 
        (ie parameters which would be passed in at runtime) by including a list of ints 
        after the list of strings for the instructions.
        
        It will automatically place those ints in registers 1-5, but currently has no error checking
            for improper or extra inputs.
       
----------------------------------------------        

Input Expectations:
    
There is a specific way that the program will want to see a single instruction.

The general form is:
    
    {keyword}{bit size}{imm/register operation} {destination} {source} {offset if keyword is a jump command}
    
They are currently limited to a specific subset of the eBPF instruction set:

****KEYWORDS*****    
Calculation Instructions:
    
    ADD  (Adding two values)
    MOV  (Moving a value into a register)
    LSH  (Left shifting a value, and placing it in a register)
    RSH  (Arithmetical right shifting of a value, and placing it in a register)
    LRSH (Logical right shifting of a value, and placing it in a register
    
Branching Conditions (Jump instructions):

    JNE  (jump if not equal)
    JEQ  (jump if equal)
    JGT  (jump if greater than or equal)
    JSGT (jump if greater than or equal (signed))

****BIT SIZE****    
Keywords can be used in either full 64 bit instructions (for any immediate/register values)
or 32 bit instructons(for imm/register values) with one exception (ARSH32 is broken as of 9/3/20).

****IMM/REGISTER OPERATION****
To indicate a immediate value to register operation, use XC
To indicate a register to register operation, use XY

***Known Bug***
This program will not do a 32 bit arithmetic rightshift operation correctly.
As of right now, it will reference the 64th bit in the register to check for sign changes,
    not the 32nd bit.  Someone should probably fix this. 

All of the above instructions can be used with immediate integer or hex-valued inputs,
    or can reference a live register that has been activated by the previous instructions 

Examples:
    
    MOV64XC 3 2             --> This moves the 64 bit value '2' into register 3
    MOV32XC 3 0xffffffff    --> This moves the 32 bit value '-1' into register 3
    
    ADD32XY 1 3     --> This will add the lower 32 bits of register 3 to the lower 32 bits of register 1
                            and store the final result in the lower 32 bits of register 1 
                        
    JNE64XC 1 -1 4  --> This compares the value stored in register 1 with the 64 bit value '-1'.
                            If they are not equal, the program skips the next 4 instructions
                        
    ARSH32XY 3 2    --> DON'T DO THIS YET (ARSH32 is broken as of 9/3/20)
                        When this works correctly, it will right shift the lower 32 bits
                            of register 3 by 2 spaces and store the result in the 
                            lower 32 bits of register 3.

----------------------------------------------     
   
Outputs from FOL_from_BPF

Lets use test 1 and test 13 from the smartnic testing suite.  
    (https://github.com/smartnic/superopt/blob/master/src/isa/ebpf/inst_test.cc)
    
I've directly copied it from the code, comments and all, but removed the line breaks only.
    FOL_from_BPF has a small regular expression translator which will strip out superflous
    information and output the string in our prefered keyword strings. 
    It works fine for /**/ comment blocks, but cannot handle // comments yet.

from FOL_from_BPF import *
print("-"*20)
instructions1 = "{inst(MOV64XC, 0, 0xffffffff),  /* mov64 r0, 0xffffffff */                         inst(ADD64XY, 0, 0),           /* add64 r0, r0 */                         inst(EXIT),                    /* exit, return r0 */                        };"
new_inst = translate_smartnic_to_python_stars_comments(instructions1)
create_program(new_inst, 2, 64)
print("-"*20)
instructions13 = "{inst(MOV32XC, 0, -1),         /* r0 = 0xffffffff */                          inst(JGTXC, 0, 0, 1),         /* if r0 <= 0, ret r0 = 0xffffffff */                          inst(EXIT),                          inst(MOV64XC, 1, -1),         /* else r1 = 0xffffffffffffffff */                          inst(JGTXY, 1, 0, 1),         /* if r1 <= r0, ret r0 = 0xffffffff */                          inst(EXIT),                          inst(MOV64XC, 0, 0),          /* else r0 = 0 */                          inst(EXIT),                   /* exit, return r0 */                         };"
new_inst = translate_smartnic_to_python_stars_comments(instructions13)
create_program(new_inst, 2, 64)
print("-"*20)

The program would output the following:

--------------------
Number of Instructions: 3
The full program in Python keyword format is:

	0:	MOV64XC 0 0xffffffff
	1:	ADD64XY 0 0
	2:	EXIT

Adding instructions in block: 0, 1, 2
	Checking Instruction: 0: MOV64XC 0 0xffffffff
	Checking Instruction: 1: ADD64XY 0 0
	Checking Instruction: 2: EXIT

--> Program Results <--
	Model found the following results:
		Final Value for Register 0: 18446744073709551614
		Final Value for Register 1: Not Initialized
--> Total Run Time: 		0.016 seconds <--
--> Time to make CFG: 		0.001 seconds <--
--> Time to create FOL: 	0.002 seconds <--
--> Time to Evaluate: 		0.013 seconds <--
--------------------
Number of Instructions: 8
The full program in Python keyword format is:

	0:	MOV32XC 0 -1
	1:	JGTXC 0 0 1
	2:	EXIT
	3:	MOV64XC 1 -1
	4:	JGTXY 1 0 1
	5:	EXIT
	6:	MOV64XC 0 0
	7:	EXIT

Adding instructions in block: 0, 1
	Checking Instruction: 0: MOV32XC 0 -1
	Checking Instruction: 1: JGTXC 0 0 1
Control moves to block: 3, 4

Adding instructions in block: 3, 4
	Checking Instruction: 3: MOV64XC 1 -1
	Checking Instruction: 4: JGTXY 1 0 1
Control moves to block: 6, 7

Adding instructions in block: 6, 7
	Checking Instruction: 6: MOV64XC 0 0
	Checking Instruction: 7: EXIT

--> Program Results <--
	Model found the following results:
		Final Value for Register 0: 0
		Final Value for Register 1: 18446744073709551615
--> Total Run Time: 		0.067 seconds <--
--> Time to make CFG: 		0.001 seconds <--
--> Time to create FOL: 	0.053 seconds <--
--> Time to Evaluate: 		0.013 seconds <--
--------------------

One caveat is that outputs from the z3Solver are always unsigned intgeger 
    interpretations of the internal 64bit bitVectors, so you might have to 
    do some small algebra to check an output.
"""