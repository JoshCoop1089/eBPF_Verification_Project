# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 12:41:36 2020

@author: joshc
"""
from z3 import *

# General helper functions for ease of use
def extend_the_number(value, value_bit_size, register_state_helper):

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

def get_the_locations_and_extend(input_value, target_reg, register_state_helper, destination_reg, extension_length):

    r_s_h = register_state_helper
    
    # Two Register Operation
    if destination_reg:
        list_of_locations, r_s_h = get_the_locations(input_value, r_s_h, target_reg)
    
    # Adding an imm value to a register
    else:
        list_of_locations, r_s_h = get_the_locations(target_reg, r_s_h)
        
        # Check that any imm value can fit inside the bit size of the register, 
        # because z3 extend functions also auto apply a modulo operator to force the fit
        if input_value > 2 ** (r_s_h.reg_bit_width - 1) - 1 or input_value < -1 * (2 ** (r_s_h.reg_bit_width - 1)):
            r_s_h.problem_flag = r_s_h.instruction_number * -1
        
        else:
            # Resize the imm value to the size of the target_reg if needed
            if extension_length != 0:
                print("\tExtending the smaller bitVector value to match reg size")
                list_of_locations[0] = extend_the_number(input_value, extension_length, r_s_h)
                
            else:
                list_of_locations[0] = BitVecVal(input_value, r_s_h.reg_bit_width)
                
    return list_of_locations, r_s_h

# Add Instructions
def add_two_values(input_value, target_reg, register_state_helper, destination_reg, extension_length):

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

    r_s_h = register_state_helper
    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, destination_reg, extension_length)
    
    # list_of_locations = [source_val, destination_old_val, destination_new_val]
    mov_function = list_of_locations[2] == list_of_locations[0]

    return mov_function, r_s_h