# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 19:18:26 2020

@author: joshc

Adding a block of instruction to the solver:
    1) execute all the normal instructions in a block, up to a jmp instruction
    2) create a temp solver, and add on the formula up to this point
    3) add the jump condition
    4) if s.check() == sat, move to the succ block for true, else, succ block for false
    5) if no succ block, return s.model()

"""
from Basic_Block_CFG_Creator import *
import time, copy

class Program_Holder:
    def __init__(self, instruction_list, reg_size, num_regs):
        block_graph, register_bitVec_dictionary = \
            basic_block_CFG_and_phi_function_setup(instruction_list, reg_size, num_regs)   
            
        self.start_block = [block_node for (block_node, indegree) in block_graph.in_degree() if indegree == 0]   
        self.block_graph = block_graph
        self.register_bitVec_dictionary = register_bitVec_dictionary
        # print([(key, self.register_bitVec_dictionary[key].name) for key in self.register_bitVec_dictionary.keys()])        
        self.formula = True
        self.end_block = 0
        
    def add_instructions_from_block(self, block, formula):
        jump_check = True
        # print(f'\nAdding instructions in block: {block.name}')
        reg_names = copy.deepcopy(block.register_names_before_block_executes)
        reg_bv_dic = self.register_bitVec_dictionary
        for instruction in block.block_instructions:
            # print(f'\tChecking Instruction: {instruction.instruction_number}: {instruction.full_instruction}')
            if "exit" in instruction.keyword:
                formula = And(formula,  BitVec('exit',1) == 0)
            elif "jmp" not in instruction.keyword:
                formula, reg_names =\
                    execute_instruction(formula, instruction, reg_names, reg_bv_dic)
            else:
                jump_check = check_jump(formula, instruction, reg_names, reg_bv_dic)

        block.register_names_after_block_executes = copy.deepcopy(reg_names)
        end_instruction = block.final_instruction
        if len(block.output_links) == 0:
            self.formula = formula
            self.end_block = block
        else:
            successor_blocks = self.block_graph.successors(block)
            for next_block in successor_blocks:
                if next_block.initial_instruction == end_instruction + 1:
                    true_block = next_block
                else:
                    false_block = next_block
            if jump_check:
                # print(f'Control moves to block: {true_block.name}')
                true_block.update_start_names(block)
                self.add_instructions_from_block(true_block, formula)
            else:
                # print(f'Control moves to block: {false_block.name}')
                false_block.update_start_names(block)
                self.add_instructions_from_block(false_block, formula)

def check_jump(formula, instruction, reg_names, reg_bv_dic):
    formula_is_sat = True
    
    if instruction.input_value_type:
        source_val = instruction.input_value_bitVec_Constant
    else:
        source_val = reg_bv_dic[reg_names[instruction.input_value]].name
    target_reg_val = reg_bv_dic[reg_names[instruction.target_reg]].name
    
    jump_condition = source_val == target_reg_val
    
    tempz3 = Solver()
    tempz3.add(formula)
    # Add in a block checking sat statement to put out an error for an instruction?
    
    tempz3.add(jump_condition)
    if tempz3.check() != sat:
        formula_is_sat = False 

    return formula_is_sat

def execute_instruction(formula, instruction, reg_names, reg_bv_dic):
    try:
        if instruction.input_value_type:
            source_val = instruction.input_value_bitVec_Constant
        else:
            source_val = reg_bv_dic[reg_names[instruction.input_value]].name
        
        try:    
            target_reg_old_val = reg_bv_dic[reg_names[instruction.target_reg]].name
        except KeyError:
            pass

        target_reg_new_val = reg_bv_dic[instruction.target_reg_new_name].name
        
        if "add" in instruction.keyword:
            constraints = target_reg_new_val == target_reg_old_val + source_val
        elif "mov" in instruction.keyword:
            constraints = target_reg_new_val == source_val
        else:
            constraints = And(True, False)
            
        reg_names[instruction.target_reg] = instruction.target_reg_new_name
        formula = And(formula, constraints)
        return formula, reg_names
    
    except Z3Exception:
        return And(False, True), reg_names
    
def translate_to_bpf_in_c(program_list):
    """
    Simplify the testing of a program in bpf_step using our current accessible keywords
        and the libbpf.h functions.  No error checking added, assuming formating of input strings
        is valid.
        
    This function will output a list of strings containing the translated versions ready to be
        copied right into sock_example.c
        
    Example:
        program_list =
        	0:	movI8 4 1
        	1:	movI8 3 2
        	2:	addR 1 2
        	3:	jneI8 5 2 2
        	4:	addR 1 1
        	5:	addI4 3 2
        	6:	addR 1 2
        	7:	addR 2 1
        	8:	exit 0 0
        
        would print the following to the console:
            
            BPF_MOV64_IMM(BPF_REG_1, 4), BPF_MOV64_IMM(BPF_REG_2, 3), 
            BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1), BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 5, 2), 
            BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_1), BPF_ALU32_IMM(BPF_ADD, BPF_REG_2, 3), 
            BPF_ALU64_REG(BPF_ADD, BPF_REG_2, BPF_REG_1), BPF_ALU64_REG(BPF_ADD, BPF_REG_1, BPF_REG_2), 
            BPF_EXIT_INSN(), 
    """
    print("The full program in Python keyword format is:\n")
    for number, ins in enumerate(program_list):
        print ("\t"+ str(number) + ":\t" + ins)
    
    output = ""
    for instruction in program_list:
        split_ins = instruction.split(" ")
        keyword = split_ins[0]
        value = split_ins[1]
        target_reg = split_ins[2]
        
        if len(split_ins) == 3:
        # Add Instuctions
            if keyword == "addI4":
                instruction = f'BPF_ALU32_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addI8":
                instruction = f'BPF_ALU64_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addR":
                instruction = f'BPF_ALU64_REG(BPF_ADD, BPF_REG_{target_reg}, BPF_REG_{value})'
            
        # Mov Instructions
            elif keyword == "movI4" or keyword == "movI8":
                instruction = f'BPF_MOV64_IMM(BPF_REG_{target_reg}, {value})'
            elif keyword == "movR":
                instruction = f'BPF_MOV64_REG(BPF_REG_{target_reg}, BPF_REG_{value})'

        # Exit command
            elif keyword == "exit":
                instruction = "BPF_EXIT_INSN()"

        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            
            if keyword == "jmpI4" or keyword == "jmpI8":
                instruction = f'BPF_JMP_IMM(BPF_JNE, BPF_REG_{target_reg}, {value}, {offset})'
            elif keyword == "jmpR":
                instruction = f'BPF_JMP_REG(BPF_JNE, BPF_REG_{target_reg}, BPF_REG_{value}, {offset})'
        
        output += instruction + ", "
    output += "BPF_EXIT_INSN(),"
    print("\nThis program would be written as the following for BPF in C:\n")        
    print(output)
    
# Driver code for running full program and outputing solutions for registers
def create_program(instruction_list, num_regs = 4, reg_size = 8):
    print(f'Number of Instructions: {len(instruction_list)}')
    start_time = time.time()    
    program = Program_Holder(instruction_list, reg_size, num_regs)
    program.add_instructions_from_block(program.start_block[0], True)
    z3Solver = Solver()
    z3Solver.add(program.formula)
    if z3Solver.check() == sat:
        # print (z3Solver.model())
        print("Model found a solution for the program:\n")
        for reg_num, reg_name in enumerate(program.end_block.register_names_after_block_executes):
            if reg_name != '0':
                reg_name = program.register_bitVec_dictionary[reg_name].name
                print(f'\tFinal Value for Register {reg_num}: {z3Solver.model()[reg_name]}')
            else:
                print(f'\tFinal Value for Register {reg_num}: Not Initialized')
                
    else:
        print ("Model couldn't find a solution for the program: \n\tUNSATISFIABLE")
        
    end_time = time.time()
    print('\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))

    # for node in program.block_graph:
    #     print("-"*20)
    #     print(node)
    # print("-"*20)

    # translate_to_bpf_in_c(instruction_list)
# create_program(instruction_list)