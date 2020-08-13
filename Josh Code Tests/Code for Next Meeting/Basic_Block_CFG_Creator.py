# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 16:07:01 2020

@author: joshc

Main Ideas in this code:
    Instruction_Info object
        Takes an individual instruction from the instruction list, and splits 
        it up to allow for future execution based on the specifics in the string
        
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
import time, copy
import networkx as nx
from z3 import *

# Unsure if nx.draw(graph) actually requires this
# import matplotlib.pyplot as plt

# Internal representation for one instance of a register
class Register_BitVec:
    def __init__(self, name, reg_bit_size):
        self.name = BitVec(name, reg_bit_size)
        self.reg_name = name 

# All the info for parsing a single instruction from a program
class Instruction_Info:
    def __init__ (self, instruction, number):
        self.full_instruction = instruction
        self.instruction_number = number
        
        # Getting the specifics from an instruction
        split_ins = instruction.split(" ")        
        self.keyword = split_ins[0]
        self.input_value = int(split_ins[1])
        self.target_reg = int(split_ins[2])        
        if "jmp" in self.keyword:
            self.offset = int(split_ins[3])
        else:
            self.offset = 0
        
        # Defining how to treat self.input_value
        if "I4" in self.keyword:
            self.input_value_type = "Half-sized External Value"
        elif "I8" in self.keyword:
            self.input_value_type = "Register-sized External Value"     
        elif "Reg" in self.keyword:
            self.input_value_type = "Value from Register"     
        else:
            self.input_value_type = "ya broked it"
            
        # Store the name in the instruction, reference the actual bitVec object from an external dictionary
        if "jmp" not in self.keyword:
            self.target_reg_name = f'r{self.target_reg}_{self.instruction_number}'
        else:
            self.target_reg_name = ""

    def __str__(self):
        print(f'Instruction {self.instruction_number}: {self.full_instruction}')
        # print(f'Source: {self.input_value}\tTarget: {self.target_reg}')
        # print(f'Source Type: {self.input_value_type}\t ')
        return ""  
    
# Basic Block holds all Instruction_Info commands for reference in a specific chunk of straightline code
class Basic_Block:
    def __init__ (self, num_regs, instruction_chunk, instruction_list, graph):
        self.name = str(instruction_chunk).strip("[]")
        self.num_regs = num_regs
        
        # For use in naming any phi functions the block requires
        self.block_ID = str(instruction_chunk[0])
        
        self.block_instructions = []
        for instruction_number in instruction_chunk:
            self.block_instructions.append(instruction_list[instruction_number])
            
        # Identifying what registers need new SSA names in a block
        self.variables_changed_in_block = set()
        for instruction in self.block_instructions:
            if "jmp" not in instruction.keyword:
                self.variables_changed_in_block.add(instruction.target_reg)
                
        # Holds the numbers of any registers which would require a phi function at the beginning of the block
        self.phi_functions = []
        
        # Since Phi functions aren't known at block creation time, will be updated 
            # with any names after phi_function_locations has been run on the CFG
        self.phi_function_named_registers = []
        
        # Gets the most up to date names of registers from the last block
            # If a phi function is required for a variable in the block, 
            # will put r{reg_number}_{block_ID}_phi instead of r{reg_number}_{instruction_number}
        self.register_names_before_block_executes = ['0' for _ in range(self.num_regs)]
        
        # Stores all reg names after execution of the block to pass onto the next block in the CFG
        self.register_names_after_block_executes = ['0' for _ in range(self.num_regs)]
        
        # All of the following relates to block linkage in the CFG representation
        self.initial_instruction = instruction_chunk[0]
        self.final_instruction = instruction_chunk[-1]
        self.input_links = []
        self.output_links = []
        
        # Find all instructions which link to the first instruction in the block from previous instructions/blocks
        for (start_of_edge, end_of_edge) in graph.in_edges([self.block_instructions[0].instruction_number]):
            self.input_links.append(start_of_edge)
            
        # Find all the instructions that are linked to by the last instruction in this block
        for (start_of_edge, end_of_edge) in graph.edges([self.block_instructions[-1].instruction_number]):
            self.output_links.append(end_of_edge)
            
    def create_phi_function_register_names(self):
        for register_number in self.phi_functions:
            reg_name = f'r{register_number}_Block_{self.block_ID}_phi'
            self.phi_function_named_registers.append(reg_name)
            
    def get_reg_names_for_beginning_of_block(self, block_graph):
        if self.block_ID == '0':
            self.register_names_before_block_executes = \
                [f'r{i}_start' for i in range(self.num_regs)]
        else:
            previous_blocks =[block for block in block_graph.predecessors(self)]
            self.register_names_before_block_executes = copy.deepcopy(previous_blocks[0].register_names_after_block_executes)
    
            # Block need a phi function definition
            for reg_number in self.phi_functions:
                reg_name = [name for name in self.phi_function_named_registers if f'r{reg_number}' in name]
                self.register_names_before_block_executes[reg_number] = reg_name[0]
    
    def get_reg_names_for_end_of_block(self):
        for instruction in self.block_instructions:
            new_name = instruction.target_reg_name
            if not new_name == "":
                self.register_names_after_block_executes[instruction.target_reg] = new_name
                
        for reg_num, reg_name in enumerate(self.register_names_after_block_executes):
            if reg_name == '0':
                self.register_names_after_block_executes[reg_num] = \
                    self.register_names_before_block_executes[reg_num]
        
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
        Holds the node/edge connections from the instruction_list
    """
    instruction_graph = nx.DiGraph()
    for instruction_number, instruction in enumerate(instruction_list):
        if instruction_number == len(instruction_list) - 1:
            break
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
            if "jmp" in instruction.keyword:
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
        partitioned into their blocks
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
# Does this need to be changed?  I am less than enamored with the next_blocks identification method
def get_edges_between_basic_blocks(block_list):
    """
    Parameters
    ----------
    block_list : TYPE : List of Lists of Ints
        Contains a List holding all instruction numbers (not instruction_info objects)
        partitioned into their blocks

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects
        holding all required Instruction_Info objects

    """
    block_graph = nx.DiGraph()
    for starting_block in block_list:
        for forward_link in starting_block.output_links:
            next_blocks = [block for block in block_list if starting_block.final_instruction
                                                            in block.input_links]
            for next_block in next_blocks:
                block_graph.add_edge(starting_block, next_block)
    return block_graph    

def set_up_basic_block_cfg(instruction_list, reg_size, num_regs):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of strings
        Holds all instructions individually, no assumed connections, in special keyword forms

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects
        holding all required Instruction_Info objects
    """
    instruction_list = [Instruction_Info(instruction, number) for number, instruction in enumerate(instruction_list)]
    
    # Create all the regular register bitVec instances needed.  Does not create phi function registers yet
    register_bitVec_dictionary = {}
    for reg_num in range(num_regs):
        reg_name = f'r{reg_num}_start'
        register_bitVec_dictionary[reg_name] = Register_BitVec(reg_name, reg_size)

    for instruction in instruction_list:
        reg_name = instruction.target_reg_name
        register_bitVec_dictionary[reg_name] = Register_BitVec(reg_name, reg_size)
        
    instruction_graph = extract_all_edges_from_instruction_list(instruction_list)
    # nx.draw(instruction_graph)
    
    block_list_chunks = identify_the_instructions_in_basic_blocks(instruction_list)
    block_list = []
    for block_chunk in block_list_chunks:     
        block_list.append(Basic_Block(num_regs, block_chunk, instruction_list, instruction_graph))

    block_graph = get_edges_between_basic_blocks(block_list)
    # nx.draw(block_graph)

    return block_graph, register_bitVec_dictionary
    
# Identify and place phi function for required register changes
def phi_function_locations(block_graph):
    """
    From slide 26 in lecture7.ppt in Code for Next Meeting
    
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
    start_block = [block_node for (block_node, indegree) in block_graph.in_degree() if indegree == 0]
    dom_dict = nx.dominance_frontiers(block_graph, start_block[0])   

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

# Startup function to create the CFG and set up the register names
def basic_block_CFG_and_phi_function_setup(instruction_list, reg_size, num_regs):
    """
    Parameters
    ----------
    instruction_list : TYPE :List of strings
        Holds all instructions individually, no assumed connections, in special keyword forms
    reg_size : TYPE
        DESCRIPTION.

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects
        holding all required Instruction_Info objects. Nodes have been updated with 
        Phi functions for specific registers, and all registers which will be used in the program
        have been created and assigned to their specific blocks ready to be combined with their
        specific eBPF instructions
    register_bitVec_dictionary : TYPE : Dictionary (Strings, Register_BitVec objects)
        The reference list for the actual z3 bitVec variables that will be added to the solver
    """
    block_graph, register_bitVec_dictionary = set_up_basic_block_cfg(instruction_list, reg_size, num_regs)
    block_graph = phi_function_locations(block_graph)
    
    # Create the phi function register bit vec objects for reference.  
    # Regular registers are created in set_up_basic_block_cfg
    for block in block_graph:
        block.create_phi_function_register_names()
        block.get_reg_names_for_beginning_of_block(block_graph)
        block.get_reg_names_for_end_of_block()
        for new_phi_reg in block.phi_function_named_registers:
            register_bitVec_dictionary[new_phi_reg] = Register_BitVec(new_phi_reg, reg_size)
    return block_graph, register_bitVec_dictionary   
     
"""
To Do List
-- Completed -- 
Naming Scheme for registers 
    Variable Names:
        r1_{instruction_number}
            Can be made during instruction_info object creation
            Only required for the target_reg new instance
            Maintain the names required for an instruction inside the instruction_info object for easy reference
            Maintain the actual bitvec representations in an outside dictionary so you don't recopy them
        r1_{block_ID}_phi

    Make a new list at the beginning of every block holding the most recent names from the pred block(s)
    If there are multiple pred blocks, then you would need to combine a specific
        variable using a phi function (see 2 for specifics)
    After all the instructions in the block have executed, make a new list for any name updates to be
        sent to a subsequent block
        
-- In Progress -- 
FOL Translations of eBPF
Identifying Phi Function Conditions
       
Phi Function Conditions

1) Find the immediate dominator (ImmDom) of the block in question (PhiN)
2) for all the immediate predecessor blocks (predBlock) of PhiN
    2a) Trace the shortest path from the ImmDom to a single predBlock
    2b) Establish the series of true/false for all the jump conditions along the path
        2b1) If len(shortest_path) is 0, the only condition is a false from ImmDom
    2c) Take the conjunction of all conditions from 2b
    2d) Take the conjunction of 2c with PhiN_register == predBlock_register
3) PhiN phi function for a register will be the disjunction of all distinct conjunctions from 2d

For the current 12 instruction long test program, we should get the following phi functions
    
phi(d_r) = (b = T ^ c = T ^ d_r = c_r) V (b = F ^ d_r = b_r)
phi(f_r) = (d = T ^ f_r = e_r) V (d = F ^ f_r = d_r)
phi(g_r) = (a = F ^ g_r = a_r) V (a = T ^ b = T ^ c = F ^ g_r = c_r) V (a = T ^ b = F ^ d = F ^ g_r = f_r)

"""



# # Driver code for testing
# start_time = time.time()
# num_regs = 4
# reg_size = 8

# # 3 Pred Node at end
# instruction_list = ["a 1 1", "jmp 1 1 9", "b 1 1",  "jmp 1 1 2", "c 1 1", "jmp 1 1 5", 
#     "d 1 1", "jmp 1 1 1", "e 1 1", "f 1 1", "g 1 1", "h 1 1"]

# # Multiple variables need phi functions
# # instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "jmp 1 1 2", "d 1 1", "e 2 2", "f 2 2", "g 1 2"]

# # Extending the code to arbitrary lengths for stress testing
# # for _ in range(13):
# #     instruction_list.extend(instruction_list)
# print(f'Number of Instructions: {len(instruction_list)}')

# block_graph, register_bitVec_dictionary = basic_block_CFG_and_phi_function_setup(instruction_list, reg_size, num_regs)    

    
# # print([(key, register_bitVec_dictionary[key].name) for key in register_bitVec_dictionary.keys()])        
# for node in block_graph:
#     print("-"*20)
#     print(node)
# print("-"*20)
        
# end_time = time.time()
# print('\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))