# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 19:52:24 2020

@author: joshc

***Not designed to be run, used as quick reference***

Collecting all the logical functions for the verifier in a smaller easier to read file.

Functions Currently Modeled:
    
    add_two_values:
        BPF_ALU32_IMM        //set destination_reg to False and extension_length to 32
        BPF_ALU64_IMM        //set destination_reg to False and extension_length to 0
        BPF_ALU64_REG        //set destination_reg to True and extension_length to 0

    mov_to_reg:
        BPF_MOV32_IMM        //set destination_reg to False and extension_length to 32
        BPF_MOV64_IMM        //set destination_reg to False and extension_length to 0
        BPF_MOV64_REG        //set destination_reg to True and extension_length to 0
        
    extend_the_number:
        Guarantees any value passed into the solver is a bitvector of the proper size 
        (ie matching the register size)
        
    exit_instructon:
        Exit instruction doesn't really do anything yet beside add an exit variable and set it to True
        Was supposed to be used with Jump commands, but given that I havent figured out jump commands yet...
"""
from z3 import *

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


# Add Instructions
def add_two_values(input_value, target_reg, register_state_helper, destination_reg, extension_length):
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
        
    destination_reg : TYPE : boolean
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

    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
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
def mov_to_reg(input_value, target_reg, register_state_helper, destination_reg, extension_length):
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
        
    destination_reg : TYPE : boolean
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
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h

def exit_instruction(register_state_helper):
    exit_ins = Bool("exit_%d"%(register_state_helper.instruction_number - 1))
    return exit_ins, register_state_helper 