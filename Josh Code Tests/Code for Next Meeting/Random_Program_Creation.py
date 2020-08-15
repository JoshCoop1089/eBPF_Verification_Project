# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 19:19:36 2020

@author: joshc

Random_program_creator and translate_to_bpf_in_c will be able to generate any number
    of programs using our currently allowed keywords, simplifying testing both of the Python 
    interpreter, and using bpf_step as official verification for a program.
    
The program_creator enforces three constraints on every program.
    1) The first instruction is a mov command to initialize a register
    2) The second to last instruction cannot be a jump, since the offset would
        make it reference outside the instruction list
    3) The last command is an exit command

It also ensures that any register involved in an instruction has had a value moved into it 
    before attempting to use that register
    
Originally, it allowed for exit instructions to be used as a randomly added instruction, 
    but that lead to an over abundance of exit instructions due to the random choice.
    
    -- Could probably get around this by setting up some type of randomized weighting system
        on a per command basis

Note:
    Should probably figure out a way to force input values to be small to not lead to many different unsat conditions
"""
import random

def get_source_values(register_size, initialized_registers):
    """
    Generate a value or register location to use as a source.

    Parameters
    ----------
    register_size : TYPE : int
        The size of the registers in the program, to enforce that input values will fit in the register
        and allow for use of full sized or half sized values 
        (32/64 bit values for bpf_step, 4/8 bit values for Python Interpreter)

    initialized_registers : TYPE : List of ints
        Holds the values of all registers which could be used to get a value from

    Returns
    -------
    source_value : TYPE : int
        The value or register location to use as the source
    
    source_value_keyword : TYPE : String
        The specific type of value randomly chosen (imm4, imm8, or Register Location)

    """
    source_val_chosen = False   
    while not source_val_chosen:
        source_val_chosen = True
        
        # First, choose if this is an imm4, imm8, or Register as the source value 
        source_val_type = random.randint(0,2)
        
        # imm4
        if source_val_type == 0:
            min_reg_value = -1 * 2 ** (register_size//8 - 1)
            max_reg_value = 2 ** (register_size//8 - 1) - 1
            source_value = random.randint(min_reg_value, max_reg_value)
            source_value_keyword = "I4"
            
        # imm8
        elif source_val_type == 1:
            min_reg_value = -1 * 2 ** (register_size//8 - 1)
            max_reg_value = 2 ** (register_size//8 - 1) - 1
            source_value = random.randint(min_reg_value, max_reg_value)
            source_value_keyword = "I8"
    
        # register source
        elif source_val_type == 2 and len(initialized_registers) != 0:
            source_value = random.choice(initialized_registers)
            source_value_keyword = "R"
        
        # Register source chosen, but no initialized registers yet
        else:
            source_val_chosen = False
            
    return source_value, source_value_keyword

def random_program_creator(number_of_instructions, number_of_registers, register_size):
    """
    Create a randomly created, possibly valid (might not be satisfiable) eBPF instruction
        list formatted for use in FOL_Verifier.py

    Parameters
    ----------
    number_of_instructions : TYPE : int
        How many instructions the program will have
    number_of_registers : TYPE : int
        How many registers the program can manipulate
    register_size : TYPE : int
        How big each register is

    Returns
    -------
    instruction_list : TYPE : List of Strings
        The properly encoded list of instructions ready to be passed into create_program in Verifier_Round_3.py

    """
    initialized_registers = []
    instruction_list = []
    
    # First Instruction must initialize a register to a value using a mov command
    source_value, source_value_keyword = get_source_values(register_size, initialized_registers)
    destination_register = random.randint(0, number_of_registers - 1)
    initialized_registers.append(destination_register)
    instruction_list.append(f'mov{source_value_keyword} {source_value} {destination_register}')

    # Randomly generate the rest of the instructions
    for instruction_number in range(1,number_of_instructions-1):
        
        current_allowed_instructions = ["add", "mov", "jmp"]
        instruction_type = random.choice(current_allowed_instructions)
        
        # Second to last instruction cannot be a jump, since that would automatically make
        # the offset val jump out of the length of the program
        while instruction_number == number_of_instructions - 2 and instruction_type == "jmp":
            instruction_type = random.choice(current_allowed_instructions)

        source_value, source_value_keyword = get_source_values(register_size, initialized_registers)
        
        # mov commands can use any register as the destination
        if instruction_type == "mov":
            destination_value = random.randint(0, number_of_registers - 1)

            if destination_value not in initialized_registers:
                initialized_registers.append(destination_value)
                
        # All other commands can only use initalized registers as destinations
        else:
            destination_value = random.choice(initialized_registers)
        
        instruction = f'{instruction_type}{source_value_keyword} {source_value} {destination_value}'
        
        # Find an offset value for jump instructions that is within the bounds of the total number of instructions
        if instruction_type == "jmp":
            number_of_instructions_left = number_of_instructions - instruction_number - 2
            if number_of_instructions_left == 0:
                offset_val = 1
            else:
                offset_val = random.randint(1, number_of_instructions_left)
            instruction += f' {offset_val}'
            
        instruction_list.append(instruction)
    
    # Last instruction is always an exit
    instruction_list.append("exit 0 0")
    
    # For debugging
    print(instruction_list)
    
    return instruction_list
    
def translate_to_bpf_in_c(program_list):
    """
    Simplify the testing of a program in bpf_step using our current accessible keywords
        and the libbpf.h functions.  No error checking added, assuming formating of input strings
        is valid.
        
    This function will output a list of strings containing the translated versions ready to be
        copied right into sock_example.c, with a little maintence to remove the '' marks when python 
        prints out a string.
        
    Example:
        program_list =
        ["movI8 0 0", "movI8 0 0", 
         "movI8 1 2" , "movI8 3 3", 
         "addR 2 3", "movI8 -1 1", 
         "addR 2 1", "addI4 -3 2"]
        
        would print the following to the console:
            
        ['BPF_MOV64_IMM(BPF_REG_0, 0)', 'BPF_MOV64_IMM(BPF_REG_0, 0)', 
         'BPF_MOV64_IMM(BPF_REG_2, 1)', 'BPF_MOV64_IMM(BPF_REG_3, 3)', 
         'BPF_ALU64_REG(BPF_ADD, BPF_REG_3, BPF_REG_2)', 'BPF_MOV64_IMM(BPF_REG_1, -1)', 
         'BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2)', 'BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, -3)']
    """
    print("\nThe full program in Python keyword format is:")
    for number, ins in enumerate(program_list):
        print (str(number) + ":\t" + ins)
    
    output = ""
    for instruction in program_list:
        split_ins = instruction.split(" ")
        keyword = split_ins[0]
        input_value = split_ins[1]
        target_reg = split_ins[2]
        
        if len(split_ins) == 3:
        # Add Instuctions
            if keyword == "addI4":
                instruction = f'BPF_ALU32_IMM(BPF_ADD, BPF_REG_{target_reg}, {input_value})'
            elif keyword == "addI8":
                instruction = f'BPF_ALU64_IMM(BPF_ADD, BPF_REG_{target_reg}, {input_value})'
            elif keyword == "addR":
                instruction = f'BPF_ALU64_REG(BPF_ADD, BPF_REG_{target_reg}, BPF_REG_{input_value})'
            
        # Mov Instructions
            elif keyword == "movI4" or keyword == "movI8":
                instruction = f'BPF_MOV64_IMM(BPF_REG_{target_reg}, {input_value})'
            elif keyword == "movR":
                instruction = f'BPF_MOV64_REG(BPF_REG_{target_reg}, BPF_REG_{input_value})'

        # Exit command located
            elif keyword == "exit":
                instruction = "BPF_EXIT_INSN()"

        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            if keyword == "jmpI4" or keyword == "jmpI8":
                instruction = f'BPF_JMP_IMM(BPF_JNE, BPF_REG_{target_reg}, {input_value}, {offset})'
            elif keyword == "jmpR":
                instruction = f'BPF_JMP_REG(BPF_JNE, BPF_REG_{target_reg}, BPF_REG_{input_value}, {offset})'
        
        # Formatting a single output string for direct copy into bpf_step
        output += instruction + ", "
    
    print("\nThis program would be written as the following for BPF in C:\n")        
    print(output)
    
    return output

# # Create a program with 16 instructions, and 4 registers of 8 bits each
# prog_list = random_program_creator(16, 4, 8)   
# bpf_list = translate_to_bpf_in_c(prog_list)

# Sample output
"""
['movI8 107 3', 'addR 3 3', 'addI4 4 3', 'jneR 3 3 5', 
 'movI4 6 2', 'jneR 3 2 2', 'movI8 -92 3', 'movR 2 3', 
 'addI4 3 2', 'addI4 0 2', 'addI8 32 3', 'addI8 15 3', 
 'movI4 3 3', 'addR 2 2', 'addR 3 3', 'exit 0 0']

The full program in Python keyword format is:
0:	movI8 107 3
1:	addR 3 3
2:	addI4 4 3
3:	jneR 3 3 5
4:	movI4 6 2
5:	jneR 3 2 2
6:	movI8 -92 3
7:	movR 2 3
8:	addI4 3 2
9:	addI4 0 2
10:	addI8 32 3
11:	addI8 15 3
12:	movI4 3 3
13:	addR 2 2
14:	addR 3 3
15:	exit 0 0

This program would be written as the following for BPF in C:

BPF_MOV64_IMM(BPF_REG_3, 107), BPF_ALU64_REG(BPF_ADD, BPF_REG_3, BPF_REG_3), 
BPF_ALU32_IMM(BPF_ADD, BPF_REG_3, 4), BPF_JMP_REG(BPF_JNE, BPF_REG_3, BPF_REG_3, 5), 
BPF_MOV64_IMM(BPF_REG_2, 6), BPF_JMP_REG(BPF_JNE, BPF_REG_2, BPF_REG_3, 2), 
BPF_MOV64_IMM(BPF_REG_3, -92), BPF_MOV64_REG(BPF_REG_3, BPF_REG_2), 
BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, 3), BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, 0), 
BPF_ALU64_IMM(BPF_ADD, BPF_REG_3, 32), BPF_ALU64_IMM(BPF_ADD, BPF_REG_3, 15), 
BPF_MOV64_IMM(BPF_REG_3, 3), BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_2), 
BPF_ALU64_REG(BPF_ADD, BPF_REG_3, BPF_REG_3), BPF_EXIT_INSN(), 
"""