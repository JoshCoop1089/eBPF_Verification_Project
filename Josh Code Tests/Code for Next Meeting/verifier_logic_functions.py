# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 19:52:24 2020

@author: joshc

***Not designed to be run, used as quick reference***

Collecting all the logical functions for the verifier in a smaller easier to read file.

Functions Currently Modeled:
    
    add_two_values:
        BPF_ALU32_IMM           //set source_reg to False and extension_length to 32
        BPF_ALU64_IMM           //set source_reg to False and extension_length to 0
        BPF_ALU64_REG           //set source_reg to True and extension_length to 0

    mov_to_reg:
        BPF_MOV32_IMM           //set source_reg to False and extension_length to 32
        BPF_MOV64_IMM           //set source_reg to False and extension_length to 0
        BPF_MOV64_REG           //set source_reg to True and extension_length to 0
        
    jump_command: (Currently only set up for JNE version)
        BPF_JMP_IMM (32 bits)   //set source_reg to False and extension_length to 32
        BPF_JMP_IMM (64 bits)   //set source_reg to False and extension_length to 0
        BPF_JMP_REG             //set source_reg to True and extension_length to 0
        
    extend_the_number:
        Guarantees any value passed into the solver is a bitvector of the proper size 
        (ie matching the register size)
        
    exit_instructon:
        Exit instruction doesn't really do anything yet beside add an exit variable and set it to True
        Was supposed to be used with Jump commands, but given that I havent figured out jump commands yet...
"""
from z3 import *

# Add Instructions
def add_two_values(input_value, target_reg, register_state_helper, source_reg, extension_length):
    """
    Generic function to combine two numbers and check for overflows    

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    add_function : Type : z3 equation
        Holds the combination of all constraints due to the add instruction
        
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper

    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    # Perform the addition
    output_function = list_of_locations[2] == list_of_locations[1] + list_of_locations[0]
    
    # Guarantee no overflow
    no_overflow = BVAddNoOverflow(list_of_locations[0], list_of_locations[1], True)
    
    # Guarantee no underflow
    no_underflow = BVAddNoUnderflow(list_of_locations[0], list_of_locations[1])
    
    # Composition of the conditions
    add_function = And(output_function, no_overflow, no_underflow)
    
    return add_function, r_s_h

# Mov Instructions
def mov_to_reg(input_value, target_reg, register_state_helper, source_reg, extension_length):
    """
    Generic function to move a value into a register    

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    mov_function : Type : z3 equation
        Holds the combination of all constraints due to the mov instruction
        
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h

# Jump Instructions
def jump_command(input_value, target_reg, offset, register_state_helper, source_reg, extension_length):
    """
    Generic function to execute the two paths of a jump instruction    

    Parameters
    ----------
    input_value : TYPE: int
        Will be either the location of the source_reg or the imm value
        
    target_reg : TYPE : int
        Location where data will be stored after calculation
        
    offset : Type : Int
        How many instructions to jump if the comparison fails
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    source_reg : TYPE : boolean
        States whether to treat input_value as a source reg (True) or an imm value (False).
        
    extension_length : Type : Int
        if the value being added isn't the same size as the register, this value tell how much
        to either sign or zero extend it

    Returns
    -------
    jump_constraints : Type : z3 equation
        Holds the combination of all constraints due to the jump instruction, the execution
        of the branches, and the combination of the paths after
        
    r_s_h : TYPE: Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, now updated from the instruction

    """
    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    
    # I don't feel like rewriting get loc and extend to not always add a new reg value on the 
    # destination register list, so i'll just delete it here
    del r_s_h.register_history[target_reg][-1]
    
    # This is specifically for jumps with equality, but should be modularized to deal with different jump conditions
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    comparison_statement = list_of_locations[0] == list_of_locations[1]
    
    # These two variables should hold the index of the required instructions
    next_ins = r_s_h.instruction_number + 1
    next_ins_with_offset = next_ins + offset

    # Get the variable names from before the jump occurs
    before_jump_reg_names = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    # print(before_jump_reg_names)
    
    # Execute all the instructions between jump and offset
    jump_constraints = True
    for instruction_number, instruction in enumerate(r_s_h.instruction_list[next_ins:next_ins_with_offset], next_ins):
        r_s_h.instruction_number += 1
        instruction_constraints , r_s_h = \
            create_new_constraints_based_on_instruction_v2(r_s_h.instruction_list[instruction_number], register_state_helper)
        jump_constraints = And(instruction_constraints, jump_constraints)
    
    # Get the register names from after the jump instructions
    after_branch_reg_names = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    # print(after_branch_reg_names)
    
    # Create a new instance of every register, using an if then else clause to 
        # assign it the value based on which branch was taken
    for reg_number, reg_list in enumerate(r_s_h.register_history):
        
        # The register hasn't been initalized yet
        if len(reg_list) == 1:
            continue
        
        name = f'r{reg_number}_{next_ins_with_offset}_after_jump'
        reg_list.append(Register_Info(name, r_s_h.reg_bit_width))
        
        # If (compare, is_true, is_false)
        name_constraints = If(comparison_statement, reg_list[-1].name == after_branch_reg_names[reg_number].name,\
                              reg_list[-1].name == before_jump_reg_names[reg_number].name)
        
        jump_constraints = And(name_constraints, jump_constraints)
    
    # Make the main program skip over the branched instructions
    r_s_h.problem_flag = next_ins_with_offset

    return jump_constraints, register_state_helper

# Every IMM value must be the size of the register
def extend_the_number(value, value_bit_size, register_state_helper):
    """
    If a number is passed into another function that is not the size of the register
        to which it will be assigned, this will extend the BitVec representation 
        of that value to have the correct Bit Width, ie that of the destination register,
        while maintaining signed properties of the original number as needed.

    Parameters
    ----------
    value : TYPE : Int
        The integer representation of the number to be extended
        
    value_bit_size : TYPE : int
        How large the input number was assumed to be before calculation
        
    register_state_helper : TYPE : Individual_Branch
        Holds reg_history, instruction_counter, problem_flag information, and bit_size for the registers of the program
        
    Returns
    -------
    extended_value : TYPE : BitVecValue with a size matching the registers of the program
        The int passed in as "value" turned into a properly sign extended or zero extended BitVector

    """
    valueBV = BitVecVal(value, value_bit_size)
    
    # Find out how much we need to extend the number
    delta_bit_size = register_state_helper.reg_bit_width - value_bit_size
    
    if delta_bit_size > 0:
        if value >= 0:
            extended_value = ZeroExt(delta_bit_size, valueBV)
        else:
            extended_value = SignExt(delta_bit_size, valueBV)
            
    # Somehow this function was incorrectly called, and the input bit size match the register bit size?
    elif delta_bit_size == 0:
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)
                                   
    # If this branch is trigger something really went wrong, because now the input number is bigger than the register size
    else:
        print("How did you get this branch to happen? How is your imm value bigger than the reg size of the program?")
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)
        
    return extended_value

def exit_instruction(register_state_helper):
    exit_ins = Bool("exit_%d"%(register_state_helper.instruction_number - 1))
    return exit_ins, register_state_helper 