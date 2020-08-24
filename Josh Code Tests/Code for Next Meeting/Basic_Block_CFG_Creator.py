# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 19:39:17 2020

@author: joshc
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 16:07:01 2020

@author: joshc
Purpose of File:
    
    basic_block_CFG_and_phi_function_setup will take in a list of special keyworded instructions,
        break the list into basic blocks, form the proper control flow graph, and create a dictionary
        holding z3 BitVector objects to be referenced in the FOL_from_BPF.py file.
        
    These functions do not actually execute or evaluate the instruction list, they only make
        the information into a form that is usable in the next file (FOL_from_BPF.py)
        
Main Ideas in this code:
    Instruction_Info object
        Takes an individual instruction from the instruction list, and splits 
        it up to allow for future execution based on the specifics in the instruction string
        
    Basic_Block object
        Collects all the Instruction_Info objects in a straightline group of code
        
        Finds out the links between the final instruction in the block, and the next
            instruction, to allow the Basic_Block object to correctly link to the
            next Basic_Block in the CFG
            
Assumptions about instruction links:
    There are two types of links
        1) Directly forward (all instructions link to the next one)
        2) Jump offset to a future instruction (found in the Instruction_Info.offset value)
"""
import copy, bitstring
import networkx as nx
from z3 import *

# Internal representation for one instance of a register
    # Made a class for this because eventually we may need to make the registers more complex,
    # since all we do now is add ints to ints, but what about pointers?
class Register_BitVec:
    def __init__(self, name, reg_bit_size):
        self.name = BitVec(name, reg_bit_size)
        self.reg_name = name 

# All the info for parsing a single instruction from a program
class Instruction_Info:
    def __init__ (self, instruction, number, reg_bit_size):
        """
        Parameters
        ----------
        instruction : TYPE : String
            String literal holding the instruction in specific keyword form
        number : TYPE : Int
            Instruction number from program order
        reg_bit_size : TYPE : Int
            How big the bitVector objects need to be to model our registers

        Returns
        -------
        None.
        """
        self.full_instruction = instruction
        self.instruction_number = number
        
        # Breaking a keyword into the parts needed to interpret it
        split_ins = instruction.split(" ")        
        self.keyword = split_ins[0]
        self.input_value, self.target_reg, self.offset = 0,0,0
        if len(split_ins) > 1:
            self.target_reg = int(split_ins[1])        
            self.input_value = get_input_value(split_ins[2])
            if "J" in self.keyword:
                try:
                    self.offset = int(split_ins[3])
                except Exception:
                    pass

        
        # Defining how to treat self.input_value (as a constant, or register location)
        if self.input_value > 2 ** (reg_bit_size - 1) - 1 or \
                        self.input_value < -1 * (2 ** (reg_bit_size - 1)):
            self.input_value_is_const = True
            # Poision Pill for input size being too large, forcing unsat
            a = Int('a')
            self.input_value_bitVec_Constant = And(a == 2, a == 1)
        else:    
            if "32XC" in self.keyword:
                self.input_value_is_const = True
                self.input_value_bitVec_Constant = extend_to_proper_bitvec(self.input_value, reg_bit_size)
            elif "64XC" in self.keyword or "XC" in self.keyword:
                self.input_value_is_const = True     
                self.input_value_bitVec_Constant = BitVecVal(self.input_value, reg_bit_size)
            else:
                # print("current version of program treats 32 bit and 64 bit register commands as 64 bit")
                self.input_value_is_const = False
                self.input_value_bitVec_Constant = False
            
        # Store the name in the instruction, reference the actual bitVec object from an external dictionary
        if "J" not in self.keyword or "EXIT" not in self.keyword:
            self.target_reg_new_name = f'r{self.target_reg}_{self.instruction_number}'
        else:
            self.target_reg_new_name = ""

    def __str__(self):
        print(f'Instruction {self.instruction_number}: {self.full_instruction}')
        # print(f'Source: {self.input_value}\tTarget: {self.target_reg}')
        return ""  
def get_input_value(instruction_string):
    input_value = 0
    if "0x" in instruction_string:
        temp_value = int(instruction_string, 16)
        mask = 2**31
        if temp_value > mask:
            input_value = -(temp_value & mask) + (temp_value & ~mask)
        else:
            input_value = temp_value
    else:
        input_value = int(instruction_string) 
    return input_value    


# Extending half sized constant inputs to be register sized (assuming no one tries to use odd sized registers)
def extend_to_proper_bitvec(value, reg_size):
    valueBV = BitVecVal(value, reg_size//2)
    if value >= 0:
        return ZeroExt(reg_size//2, valueBV)
    else:
        return SignExt(reg_size//2, valueBV)
    
# Basic Block holds all Instruction_Info commands for reference in a specific chunk of straightline code
class Basic_Block:
    def __init__ (self, num_regs, instruction_chunk, instruction_list, instruction_graph):
        """
        Parameters
        ----------
        num_regs : TYPE : Int
            How many registers the program is trying to model
            
        instruction_chunk : TYPE : List of ints
            Which instruction numbers are part of the current basic block
            
        instruction_list : TYPE : List of Instruction_Info objects
            The full instruction list of the program to pull from for the block
            
        instruction_graph : TYPE : nx.DiGraph
            The control flow graph of the individual instructions

        Returns
        -------
        None.
        """
        self.name = str(instruction_chunk).strip("[]")
        self.num_regs = num_regs
        self.block_instructions = []
        for instruction_number in instruction_chunk:
            self.block_instructions.append(instruction_list[instruction_number])
        
        # Stores the most up to date names of registers from the last block
            # If a phi function is required for a variable in the block, 
            # will put r{reg_number}_{block_ID}_phi instead of r{reg_number}_{instruction_number}
        self.register_names_before_block_executes = ['0' for _ in range(self.num_regs)]
        
        # Stores all reg names after execution of the block to pass onto the next block in the CFG
        self.register_names_after_block_executes = ['0' for _ in range(self.num_regs)]
        
        # Optimization for not repeatedly doing sat checks on the whole path formula 
        self.in_block_formula = True
        
        # Block edge creation helpers in the CFG representation
        self.initial_instruction = instruction_chunk[0]
        self.final_instruction = instruction_chunk[-1]
        self.input_links = []
        self.output_links = []
        
        # Find all instructions which link to the first instruction in the block from previous instructions/blocks
        for (start_of_edge, end_of_edge) in instruction_graph.in_edges([self.block_instructions[0].instruction_number]):
            self.input_links.append(start_of_edge)
            
        # Find all the instructions that are linked to by the last instruction in this block
        for (start_of_edge, end_of_edge) in instruction_graph.edges([self.block_instructions[-1].instruction_number]):
            self.output_links.append(end_of_edge)

        # # **************************************
        # # Depending on if I actually need to implement phi functions, the following could be deleted
        # # For use in naming any phi functions the block requires
        # self.block_ID = str(instruction_chunk[0])
        # # Identifying what registers need new SSA names in a block
        # self.variables_changed_in_block = set()
        # for instruction in self.block_instructions:
        #     if "jmp" not in instruction.keyword:
        #         self.variables_changed_in_block.add(instruction.target_reg)      
        # # Holds the numbers of any registers which would require a phi function at the beginning of the block
        # self.phi_functions = []
        # # Since Phi functions aren't known at block creation time, will be updated 
        #     # with any names after phi_function_locations has been run on the CFG
        # self.phi_function_named_registers = []
        # # End of phi function stuff
        # # **************************************
            
    def update_start_names(self, block, register_bitVec_dictionary):
        """
        Parameters
        ----------
        block : TYPE : Basic_Block object
            Block will be the predecessor node in the control flow path to 
                whatever Basic_Block object this function is called on
            
        register_bitVec_dictionary : TYPE : Dictionary (Strings -> Register_BitVec objects)
            The reference dictionary for the actual z3 bitVec variables that will be added to the solver.
            Keys are SSA forms of register names "r{register_number}_{instruction}" where instruction 
            refers to the specific program instruction where the register was changed to that value

        Returns
        -------
        None.
        """
        # Getting the most recent values found by the Solver, and putting them into the
            # next block, to allow for smaller FOL sat checks and speed up runtime
        tempz3 = Solver()
        tempz3.add(block.in_block_formula)
        if tempz3.check() == sat:
            for reg_num, reg_name in enumerate(block.register_names_after_block_executes):
                if reg_name != '0':
                    reg_name = register_bitVec_dictionary[reg_name].name
                    self.in_block_formula = And(self.in_block_formula, reg_name == tempz3.model()[reg_name])
        
        # print("Updating Names")
        self.register_names_before_block_executes = \
            copy.deepcopy(block.register_names_after_block_executes)     
        # print(f'New Starting Names are now: {self.register_names_before_block_executes}')

    # Do I need these two functions? Phi Function Questions
    # def create_phi_function_register_names(self):
    #     for register_number in self.phi_functions:
    #         reg_name = f'r{register_number}_Block_{self.block_ID}_phi'
    #         self.phi_function_named_registers.append(reg_name)  
    
    # def get_reg_names_for_beginning_of_block(self, block_graph):
    #     if self.block_ID == '0':
    #         self.register_names_before_block_executes = \
    #             [f'r{i}_start' for i in range(self.num_regs)]
    #     else:
    #         previous_blocks =[block for block in block_graph.predecessors(self)]
    #         self.register_names_before_block_executes = copy.deepcopy(previous_blocks[0].register_names_after_block_executes)
    
    #         # Block needs a phi function definition
    #         for reg_number in self.phi_functions:
    #             reg_name = [name for name in self.phi_function_named_registers if f'r{reg_number}' in name]
    #             self.register_names_before_block_executes[reg_number] = reg_name[0]
    
    def __str__(self):
        print(f'\nInstructions in Block: {self.name}' + '\n' + '*'*20)
        for instruction in self.block_instructions:
            print(instruction)
        print(f'Block starts with regs named: {self.register_names_before_block_executes}')
        print(f'Block ends with regs named: {self.register_names_after_block_executes}')
        # print(f'Block Forward Links to Instructions: {self.output_links}')
        # print(f'Block Backward Links to Instructions: {self.input_links}')
        # print(f'Block Makes Changes to the following registers: {self.variables_changed_in_block}')
        # print(f'Block needs a phi function for registers: {self.phi_functions}')
        return ""
            
# Define what instructions can be reached from another instruction
     # This is a precursor function for basic block identification/linking
def extract_all_edges_from_instruction_list(instruction_list):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of Instruction_Info objects
        Holds all instructions individually, no assumed connections

    Returns
    -------
    instruction_graph : TYPE : nx.DiGraph 
        Holds the node/edge connections from the instruction_list in a directed graph
        
    Assumptions about instruction links:
        1) Directly forward (all instructions except exits link to the next one)
        2) Exit instructions do not make a forward link, but can be an end point for a link
        3) Jump offset to a future instruction (found in the Instruction_Info.offset value)
    """
    instruction_graph = nx.DiGraph()
    for instruction_number, instruction in enumerate(instruction_list):
        if instruction_number == len(instruction_list) - 1:
            break
        if instruction.keyword != "EXIT":
            instruction_graph.add_edge(instruction_number, instruction_number+1)
        if instruction.offset != 0:
            instruction_graph.add_edge(instruction_number, instruction_number+instruction.offset+1)
    return instruction_graph

# Identifying Leaders in the linked instructions to form basic blocks
def identify_leaders(instruction_list):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of Instruction_Info objects
        Holds all instructions individually, no assumed connections

    Returns
    -------
    leader_set : TYPE : set of ints
        Has the instruction numbers (not instruction_info objects) which are leaders for basic blocks
    """
    leader_set = set()    
    for instruction_number, instruction in enumerate(instruction_list):
        # IndexOutOfBound protection, last node can still be found as a possible leader below
        if instruction_number == len(instruction_list) - 1:
            break
        
        # Rule 1 - First Instruction is a leader
        elif instruction_number == 0:
            leader_set.add(instruction_number)
        else:
            if "J" in instruction.keyword:
                # Rule 2 - Instruction L is a leader if there is another instruction which jumps to it
                leader_set.add(instruction_number + instruction.offset + 1)
                
                # Rule 3 - Instruction L is a leader if it immediately follows a jump instruction
                leader_set.add(instruction_number + 1)
    return leader_set

# A block consists of a leader, and all instructions until the next leader
def identify_the_instructions_in_basic_blocks(instruction_list):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of Instruction_Info objects
        Holds all instructions individually, no assumed connections

    Returns
    -------
    block_list : TYPE : List of Lists of Ints
        Contains a List holding all instruction numbers (not instruction_info objects)
        partitioned into their basic blocks
    """
    leader_list = sorted(list(identify_leaders(instruction_list)))
    block_list = []
    while len(block_list) < len(leader_list):
        index_of_current_leader = len(block_list)
        index_of_next_leader = index_of_current_leader + 1
        
        # Get all the instruction numbers between two subsequent leader instructions
        # Example: If leader_list was [0,3,5] and there were 7 total instructions
            # First basic block would return [0,1,2]
            # Second block would be [3,4]
            # Final Block would be [5,6]
        try:
            basic_block = [i for i in range(leader_list[index_of_current_leader],
                                            leader_list[index_of_next_leader])]
        except IndexError:
            basic_block = [i for i in range(leader_list[index_of_current_leader],
                                            len(instruction_list))]
        block_list.append(basic_block)
        
    return block_list

# Finding out how to link Basic_Block objects together
def set_edges_between_basic_blocks(block_list):
    """
    Parameters
    ----------
    block_list : TYPE : List of Lists of Ints
        Contains a List holding all instruction numbers (not instruction_info objects)
        partitioned into their blocks

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections in a directed graph created from the block_list,
        where nodes are Basic_Block objects holding all required Instruction_Info objects
    """
    block_graph = nx.DiGraph()
    if len(block_list) == 1:
        block_graph.add_node(block_list[0])
    else:
        for starting_block in block_list:
            next_blocks = [block for block in block_list 
                               if starting_block.final_instruction in block.input_links]
            for next_block in next_blocks:
                if starting_block.block_instructions[-1].keyword != "EXIT":
                    block_graph.add_edge(starting_block, next_block)
    return block_graph    

def set_up_basic_block_cfg(instruction_list, reg_size, num_regs):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of strings
        Holds all instructions individually, no assumed connections, in special keyword forms
            
    reg_size : TYPE : Int
        How big the modeled registers should be
    
    num_regs : TYPE : Int
        How many different registers the program will attempt to model

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections in a directed graph created from the block_list,
        where nodes are Basic_Block objects holding all required Instruction_Info objects
        
    register_bitVec_dictionary : TYPE : Dictionary (Strings -> Register_BitVec objects)
        The reference dictionary for the actual z3 bitVec variables that will be added to the solver.
        Keys are SSA forms of register names "r{register_number}_{instruction}" where instruction 
        refers to the specific program instruction where the register was changed to that value
        
    block_list[0] : TYPE : Basic_Block object
        The starting block of the graph, so we don't have to find it again
    """
    instruction_list = [Instruction_Info(instruction, number, reg_size) for number, instruction in enumerate(instruction_list)]

    # Create all the regular register bitVec instances that might be needed.  Does not create phi function registers yet
    register_bitVec_dictionary = {}
    for instruction in instruction_list:
        reg_name = instruction.target_reg_new_name
        register_bitVec_dictionary[reg_name] = Register_BitVec(reg_name, reg_size)
    
    instruction_graph = extract_all_edges_from_instruction_list(instruction_list)
    
    # Actual creation of the basic block CFG happens here!
    block_list_chunks = identify_the_instructions_in_basic_blocks(instruction_list)
    block_list = []
    for block_chunk in block_list_chunks:     
        block_list.append(Basic_Block(num_regs, block_chunk, instruction_list, instruction_graph))
    block_graph = set_edges_between_basic_blocks(block_list)

    # Visualization options for the graphs, only show connections, haven't figured
        # out how to make the nodes be named in the output picture yet
    # nx.draw_planar(instruction_graph,  with_labels = True)
    # block_labels = {node:node.name for node in block_graph}
    # nx.draw_planar(block_graph, labels = block_labels, with_labels = True)
    
    return block_graph, register_bitVec_dictionary, block_list[0]
    
# Identify and place phi function for required register changes
def phi_function_locations(block_graph, start_block):
    """
    From slide 26 in lecture7.ppt about the Cytron 1991 Efficiently Computing SSA paper
    
    Parameters
    ----------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects 
        holding all required Instruction_Info objects

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects
        holding all required Instruction_Info objects. Nodes have been updated with 
        Phi functions for specific registers
    """
    dom_dict = nx.dominance_frontiers(block_graph, start_block)   

    for register_number in range(start_block[0].num_regs):
        work_list = set()
        ever_on_work_list = set()
        already_has_phi_func = set()
        
        # Get all nodes which assign a value to our target_reg
        for block in block_graph:
            if register_number in block.variables_changed_in_block:
                work_list.add(block)
        
        ever_on_work_list = work_list
        while len(work_list) != 0:
            check_dom_front_of_block = work_list.pop()
            for dom_front_node in dom_dict[check_dom_front_of_block]:
                
                # Insert at most 1 phi function per node
                if dom_front_node not in already_has_phi_func:
                    dom_front_node.phi_functions.append(register_number)
                    already_has_phi_func.add(dom_front_node)
                    
                    # Process each node at most once
                    if dom_front_node not in ever_on_work_list:
                        work_list.add(dom_front_node)
                        ever_on_work_list.add(dom_front_node)                    
    return block_graph

# Startup function to create the CFG, set up the register bitVecs, and initialize phi functions if needed
def basic_block_CFG_and_phi_function_setup(instruction_list, reg_size, num_regs):
    """
    Parameters
    ----------
    instruction_list : TYPE :List of strings
        Holds all instructions individually, no assumed connections, in special keyword forms
        
    reg_size : TYPE : Int
        How big the modeled registers should be
    
    num_regs : TYPE : Int
        How many different registers the program will attempt to model

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects
        holding all required Instruction_Info objects. Nodes have been updated with 
        Phi functions for specific registers, and all registers which will be used in the program
        have been created and assigned to their specific blocks ready to be combined with their
        specific eBPF instructions
        
    register_bitVec_dictionary : TYPE : Dictionary (Strings -> Register_BitVec objects)
        The reference dictionary for the actual z3 bitVec variables that will be added to the solver.
        Keys are SSA forms of register names "r{register_number}_{instruction}" where instruction 
        refers to the specific program instruction where the register was changed to that value
        
    block_list[0] : TYPE : Basic_Block object
        The starting block of the graph, so we don't have to find it again
    """    
    # Commented out all of the things I had done involving phi functions, as I think I found a
        # way around calculating their positions and using them as bridging variables.
        # Will require confirmation that my method is not just a quirk of my test cases.
    
    block_graph, register_bitVec_dictionary, start_block = set_up_basic_block_cfg(instruction_list, reg_size, num_regs)

    # Generate the locations of phi functions, name them, and create the register bit vec objects for reference.  
    # block_graph = phi_function_locations(block_graph, start_block)
    # for block in block_graph:
    #     block.create_phi_function_register_names()
    #     block.get_reg_names_for_beginning_of_block(block_graph)
    #     for new_phi_reg in block.phi_function_named_registers:
    #         register_bitVec_dictionary[new_phi_reg] = Register_BitVec(new_phi_reg, reg_size)
    return block_graph, register_bitVec_dictionary, start_block