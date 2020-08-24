# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 19:18:26 2020

@author: joshc

Adding a block of instruction to the solver:
    1) execute all the normal instructions in a block, up to a jmp instruction
    2) create a temp solver, and add on the formula up to this point
    3) add the jump condition
    4) if tempSolver.check() == sat, move to the succ block for true, else, succ block for false
    5) if no succ block, return s.model()

How to get around full sat checking the constantly elongating formula
    Once a block is finished, use s.model()[register_names] to extract the ending results of the calculation from the sat check in jump
    Take those constraints, and pass them forward to the next block chosen using update_start_names

    Maintain two formulas in the program holder object, one that is a constantly increasing full map of the path through the program
    the other is a block formula, which should be as short as possible, allowing sat checks to happen stupid quickly    
"""
from Basic_Block_CFG_Creator import *
import time, copy, re

class Program_Holder:
    def __init__(self, instruction_list, reg_size, num_regs):
        """
        Parameters
        instruction_list : TYPE :List of strings
            Holds all instructions individually, no assumed connections, in special keyword forms
            
        reg_size : TYPE : Int
            How big the modeled registers should be
        
        num_regs : TYPE : Int
            How many different registers the program will attempt to model

        Returns
        -------
        None.
        """
        self.block_graph, self.register_bitVec_dictionary, self.start_block = \
            basic_block_CFG_and_phi_function_setup(instruction_list, reg_size, num_regs)   
        self.formula = True
        self.end_block = 0
        self.program_error = False
        
    def add_instructions_from_block(self, block, formula):
        """
        Parameters
        ----------
        block : TYPE : Basic_Block object
            A single basic block to evaluate and add to the solver
            
        formula : TYPE : z3 Boolean formula
            A record of the full path taken through the program, to be updated by this block

        Returns
        -------
        (true/false) block : TYPE : Basic_Block object
            The next block to evaluate, decided by the control flow of the block graph
            
        formula : TYPE : z3 Boolean formula
            A record of the full path taken through the program, after being updated by this block
        """
        # Poision Pill for incorrect instruction, forcing unsat
        a = Int('a')
        poison_the_formula = And(a == 2, a == 1)
        
        print(f'\nAdding instructions in block: {block.name}')
        reg_names = copy.deepcopy(block.register_names_before_block_executes)
        reg_bv_dic = self.register_bitVec_dictionary
        in_block_formula = block.in_block_formula
        decide_what_branch = True
        bad_formula, bad_jump_check = False, False
        for instruction in block.block_instructions:
            print(f'\tChecking Instruction: {instruction.instruction_number}: {instruction.full_instruction}')
            if "EXIT" in instruction.keyword:
                formula = And(formula,  BitVec('exit',1) == 0)
            elif "J" not in instruction.keyword:
                formula, in_block_formula, reg_names =\
                    execute_instruction(formula, in_block_formula, instruction, reg_names, reg_bv_dic, poison_the_formula)
            else:
                decide_what_branch, bad_jump_check = check_jump(in_block_formula, instruction, reg_names, reg_bv_dic)

            if formula == poison_the_formula or bad_jump_check:
                print(f'-->  Instruction {instruction.instruction_number} caused a problem, and broke the program  <--')
                self.formula = formula
                bad_formula = True
                break
                
        if bad_formula:
            self.program_error = True
            print(f'-->  Stopping program run early in block {block.name}  <--')
            return 0,0
        else:
            block.register_names_after_block_executes = copy.deepcopy(reg_names)
            block.in_block_formula = in_block_formula
            end_instruction = block.final_instruction
            
            # Reached a block with no outgoing links (ie program end point)
            if len(block.output_links) == 0 or block.block_instructions[-1].keyword == "EXIT":
                self.formula = formula
                self.end_block = block
                return block, formula
            
            # Define control flow for what block to evaluate next
            else:
                successor_blocks = self.block_graph.successors(block)
                for next_block in successor_blocks:
                    if next_block.initial_instruction == end_instruction + 1:
                        true_block = next_block
                    else:
                        false_block = next_block
                if decide_what_branch:
                    print(f'Control moves to block: {true_block.name}')
                    true_block.update_start_names(block, reg_bv_dic)
                    return true_block, formula
                else:
                    print(f'Control moves to block: {false_block.name}')
                    false_block.update_start_names(block, reg_bv_dic)
                    return false_block, formula 

def check_jump(formula, instruction, reg_names, reg_bv_dic):
    """
    Currently supports:
        JNE(jump if not equal)
        JEQ (jump if equal)
        JGT (jump if greater than or equal?)
        JSGT (jump if strictly greater than?)
    
    Parameters
    ----------
    formula : TYPE : z3 Boolean conjunction
        The current FOL translation of the block, in addition to the values from the predecessor block
    
    instruction : TYPE : Instruction_Info object
        Contains all the information about a single instruction in the program
    
    reg_names : TYPE : List of Strings
        Holds the names of the most recent versions of all registers
    
    reg_bv_dic : TYPE : Dictionary (Strings -> Register_BitVec objects)
        The reference dictionary for the actual z3 bitVec variables that will be added to the solver.
        Keys are SSA forms of register names "r{register_number}_{instruction}" where instruction 
        refers to the specific program instruction where the register was changed to that value

    Returns
    -------
    formula_is_sat : TYPE : Boolean
        Tells the program how control should flow out of the end of a block.  
        False moves the program to the offset block, true to the next instruction
        
    jump_reference_valid : TYPE : Boolean
        Error check on the inputs to the jump condition
    """
    formula_is_sat = True
    try:
        if instruction.input_value_is_const:
            source_val = instruction.input_value_bitVec_Constant
        else:
            source_val = reg_bv_dic[reg_names[instruction.input_value]].name
        target_reg_val = reg_bv_dic[reg_names[instruction.target_reg]].name
        
        if "NE" in instruction.keyword:
            jump_condition = source_val == target_reg_val
        elif "EQ" in instruction.keyword:
            jump_condition = Not(source_val == target_reg_val)
        elif "SGT" in instruction.keyword:
            jump_condition = Not(target_reg_val > source_val)
        elif "GT" in instruction.keyword:
            jump_condition = Not(UGT(target_reg_val, source_val))
        else:
            return False, True
            
        tempz3 = Solver()
        tempz3.add(formula)      
        tempz3.add(jump_condition)
        if tempz3.check() != sat:
            formula_is_sat = False 
    
        return formula_is_sat, False
    
    except KeyError:
        print("\n***  Attempting to execute instruction using non-initialized register  ***")
        return False, True
    except Z3Exception:
        print("\n***  Attempting to execute instruction using an input value that doesn't fit in the register  ***")
        return False, True

def execute_instruction(formula, in_block_formula, instruction, reg_names, reg_bv_dic, poison_the_formula):
    """
    Current Functions Supported:
        mov
        add
        lsh
        rsh
        arsh
    
    Parameters
    ----------
    formula : TYPE : z3 Boolean conjunction
        The current FOL translation of the block, in addition to the values from the predecessor block

    in_block_formula : TYPE : z3 Boolean conjunction
        The FOL translation for this specific block, including the values set in the previous block
    
    instruction : TYPE : Instruction_Info object
        Contains all the information about a single instruction in the program
    
    reg_names : TYPE : List of Strings
        Holds the names of the most recent versions of all registers
    
    reg_bv_dic : TYPE : Dictionary (Strings -> Register_BitVec objects)
        The reference dictionary for the actual z3 bitVec variables that will be added to the solver.
        Keys are SSA forms of register names "r{register_number}_{instruction}" where instruction 
        refers to the specific program instruction where the register was changed to that value
        
    poison_the_formula : TYPE : z3 Boolean conjunction
        Error catching to force an unsat in the z3Solver

    Returns
    -------
    formula : TYPE : z3 Boolean conjunction
        The current FOL translation of the block, updated for this instruction, in addition to the values from the predecessor block

    in_block_formula : TYPE : z3 Boolean conjunction
        The FOL translation for this specific block, updated for this instruction, and including the values set in the previous block
        
    reg_names : TYPE : List of Strings
        Holds the names of the most recent versions of all registers after the execution of this instruction
    """
    try:
        if instruction.input_value_is_const:
            source_val = instruction.input_value_bitVec_Constant
        else:
            source_val = reg_bv_dic[reg_names[instruction.input_value]].name
        
        # Key error if register isn't live yet, but that's ok for an inital mov into a reg
        try:    
            target_reg_old_val = reg_bv_dic[reg_names[instruction.target_reg]].name
        except KeyError:
            if "MOV" in instruction.keyword:
                pass
            else:
                print("\n***  Attempting to execute instruction using non-initialized register  ***")
                return poison_the_formula, False, reg_names

        target_reg_new_val = reg_bv_dic[instruction.target_reg_new_name].name
        
        if "ADD" in instruction.keyword:
            constraints = target_reg_new_val == target_reg_old_val + source_val
        elif "MOV" in instruction.keyword:
            constraints = target_reg_new_val == source_val
        elif "LSH" in instruction.keyword:
            constraints = target_reg_new_val == target_reg_old_val << instruction.input_value
        elif "ARSH" in instruction.keyword:
            constraints = target_reg_new_val == target_reg_old_val >> instruction.input_value
        elif "RSH" in instruction.keyword:
            constraints = target_reg_new_val == LShR(target_reg_old_val, instruction.input_value)
        
        # The keyword isn't recognized, add a poision pill to force an unsat
        else:
            print("\n***  Keyword isn't a valid form for this program  ***")
            return poison_the_formula, reg_names
            
        reg_names[instruction.target_reg] = instruction.target_reg_new_name
        formula = And(formula, constraints)
        in_block_formula = And(in_block_formula, constraints)
        return formula, in_block_formula, reg_names
    
    except KeyError:
        print("\n***  Attempting to execute instruction using non-initialized register  ***")
        return poison_the_formula, False, reg_names
    except Z3Exception:
        print("\n***  Attempting to execute instruction using an input value that doesn't fit in the register  ***")
        return poison_the_formula, False, reg_names
    
def translate_to_bpf_in_c(program_list):
    """
    Simplify the testing of a program in bpf_step using our current accessible keywords
        and the libbpf.h functions.  No error checking added, assuming formating of input strings
        is valid.
        
    This function will output a list of strings containing the translated versions ready to be
        copied right into sock_example.c
        
    Example:
        program_list =
        	0:	movI64 4 1
        	1:	movI64 3 2
        	2:	addR 1 2
        	3:	jneI64 5 2 2
        	4:	addR 1 1
        	5:	addI32 3 2
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
    output = ""
    for instruction in program_list:
        split_ins = instruction.split(" ")
        keyword = split_ins[0]
        value = split_ins[1]
        target_reg = split_ins[2]
        
        if len(split_ins) == 3:
        # Add Instuctions
            if keyword == "addI32":
                instruction = f'BPF_ALU32_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addI64":
                instruction = f'BPF_ALU64_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addR":
                instruction = f'BPF_ALU64_REG(BPF_ADD, BPF_REG_{target_reg}, BPF_REG_{value})'
            
        # Mov Instructions
            elif keyword == "movI32" or keyword == "movI64":
                instruction = f'BPF_MOV64_IMM(BPF_REG_{target_reg}, {value})'
            elif keyword == "movR":
                instruction = f'BPF_MOV64_REG(BPF_REG_{target_reg}, BPF_REG_{value})'

        # Exit command
            elif keyword == "exit":
                instruction = "BPF_EXIT_INSN()"

        # Format for jump commands
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            
            if keyword == "jmpI32" or keyword == "jmpI64":
                instruction = f'BPF_JMP_IMM(BPF_JNE, BPF_REG_{target_reg}, {value}, {offset})'
            elif keyword == "jmpR":
                instruction = f'BPF_JMP_REG(BPF_JNE, BPF_REG_{target_reg}, BPF_REG_{value}, {offset})'
        
        output += instruction + ", "
    output += "BPF_EXIT_INSN(),"
    print("\nThis program would be written as the following for BPF in C:\n")        
    print(output)

def translate_smartnic_to_python_stars_comments(instruction_input):
    output = []
    reg_ex_ins = re.sub("/\*[^\*]+\*/", "", instruction_input.strip("{").strip("};").replace(" ", ""))
    reg_ex_ins= reg_ex_ins.split(", inst(")
    # print(reg_ex_ins)
    for instruction in reg_ex_ins:
        split_ins = [instr.strip("inst(").replace(",", " ") for instr in instruction.split("),")]
        # print(split_ins[:-1])
        return split_ins[:-1]         
   
def get_runtime_parameters(inputs):
    runtime_parameters = []
    for reg_num, input_param in enumerate(inputs,1):
        new_instruction = f'MOV64XC {input_param} {reg_num}'
        runtime_parameters.append(new_instruction)
    return runtime_parameters

# Driver code for running full program and outputing solutions for registers
def create_program(instructions, num_regs = 4, reg_size = 8, inputs = []):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of Instruction_Info objects
        The full instruction list of the program to pull from for the block
        
    num_regs : TYPE, optional Int
        The number of registers the program will model.  The default is 4.
        
    reg_size : TYPE, optional Int
        The bitwidth of the modeled registers. The default is 8.
        
    inputs : TYPE, optional List of ints
        Any values passes into the program at runtime

    Returns
    -------
    None.
    """

    # Program initialization, Basic Block CFG creation
    instruction_list = get_runtime_parameters(inputs)
    instruction_list.extend(instructions)
    print(f'Number of Instructions: {len(instruction_list)}')
    print("The full program in Python keyword format is:\n")
    for number, ins in enumerate(instruction_list):
        print ("\t"+ str(number) + ":\t" + ins)

    start_time = time.time()
    program = Program_Holder(instruction_list, reg_size, num_regs)
    graph_made = time.time()
    
    # Program Execution (Iteratively adds instructions from blocks along the control flow)
    block = program.start_block
    formula = True
    while not program.program_error and block.output_links:
        block, formula = program.add_instructions_from_block(block, formula)
        # if block.block_instructions[-1].keyword == "EXIT":
        #     break
    if not program.program_error:
        block, formula = program.add_instructions_from_block(block, formula)
        program.formula = formula
    formula_made = time.time()
    
    # Checking the FOL formula found along the control flow path
    if not program.program_error:
        tempz3 = Solver()
        tempz3.add(program.end_block.in_block_formula)
        print("\n--> Program Results <--")
        if tempz3.check() == sat:
            print("\tModel found the following results:")
            for reg_num, reg_name in enumerate(program.end_block.register_names_after_block_executes):
                if reg_name != '0':
                    reg_name = program.register_bitVec_dictionary[reg_name].name
                    print(f'\t\tFinal Value for Register {reg_num}: {tempz3.model()[reg_name]}')
                else:
                    print(f'\t\tFinal Value for Register {reg_num}: Not Initialized')
        else:
            print ("Model couldn't find a solution for the program: \n\tUNSATISFIABLE")      
    end_time = time.time()

    # translate_to_bpf_in_c(instruction_list)
    
    # # Debug help to check the Basic Blocks inside the CFG
    # for node in program.block_graph:
    #     print("-"*20)
    #     print(node)
    # print("-"*20)
    print('--> Total Run Time: \t\t%0.3f seconds <--' %(end_time-start_time))
    print('--> Time to make CFG: \t\t%0.3f seconds <--' %(graph_made-start_time))
    print('--> Time to create FOL: \t%0.3f seconds <--' %(formula_made-graph_made))
    print('--> Time to Evaluate: \t\t%0.3f seconds <--' %(end_time-formula_made))
    
        