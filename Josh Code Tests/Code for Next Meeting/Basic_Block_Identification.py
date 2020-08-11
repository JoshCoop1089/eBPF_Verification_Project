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
import time
import networkx as nx

# Unsure if nx.draw(graph) actually requires this
# import matplotlib.pyplot as plt

class Instruction_Info:
    def __init__ (self, instruction, number):
        self.full_instruction = instruction
        self.instruction_number = number
        
        # Getting the specifics from an instruction
        # Will eventually be used in the eBPF instructions, but for now,
            # only offset is important for linking instructions together
        split_ins = instruction.split(" ")        
        self.keyword = split_ins[0]
        self.input_value = int(split_ins[1])
        self.target_reg = int(split_ins[2])        
        if "jmp" in self.keyword:
            self.offset = int(split_ins[3])
        else:
            self.offset = 0

    def __str__(self):
        print(f'Instruction {self.instruction_number}: {self.full_instruction}')
        print(f'Source: {self.input_value}\tTarget: {self.target_reg}')
        return ""  
    
# Basic Block holds all Instruction_Info commands for reference in a specific chunk of straightline code
class Basic_Block:
    def __init__ (self, instruction_chunk, instruction_list, graph):
        self.name = "Instructions in Block: " + str(instruction_chunk).strip("[]")
        self.block_instructions = []
        for instruction_number in instruction_chunk:
            self.block_instructions.append(instruction_list[instruction_number])
            
        # Identifying what registers need new SSA names in a block
        self.variables_changed_in_block = set()
        for instruction in self.block_instructions:
            if "jmp" not in instruction.keyword:
                self.variables_changed_in_block.add(instruction.target_reg)
                
        # Phi Functions for changes in registers
        self.phi_functions = []
        
        # All of the following might be overcomplicating block linkage
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
            
    def __str__(self):
        print(self.name)
        for instruction in self.block_instructions:
            print(instruction)
        print(f'Block Forward Links to Instructions: {self.output_links}')
        print(f'Block Backward Links to Instructions: {self.input_links}')
        print(f'Block Makes Changes to the following registers: {self.variables_changed_in_block}')
        print(f'Block needs a phi function for registers: {self.phi_functions}')
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

def set_up_basic_block_cfg(instruction_list):
    """
    Parameters
    ----------
    instruction_list : TYPE : List of Instruction_Info objects
        Holds all instructions individually, no assumed connections

    Returns
    -------
    block_graph : TYPE : nx.DiGraph
        Holds the node/edge connections from the block_list, where nodes are Basic_Block objects
        holding all required Instruction_Info objects
    """
    instruction_list = [Instruction_Info(instruction, number) for number, instruction in enumerate(instruction_list)]
    instruction_graph = extract_all_edges_from_instruction_list(instruction_list)
    # nx.draw(instruction_graph)
    
    block_list_chunks = identify_the_instructions_in_basic_blocks(instruction_list)
    block_list = []
    for block_chunk in block_list_chunks:     
        block_list.append(Basic_Block(block_chunk, instruction_list, instruction_graph))
    
    # for block in block_list:
    #     print("-"*20)
    #     print(block)

    block_graph = get_edges_between_basic_blocks(block_list)
    # print("-"*20)
    # print("\n".join([f'{block.name} links forward to {end.name}' for (block, end) in block_graph.edges()]))

    # nx.draw(block_graph)

    return block_graph
    
# Do the whole Phi Function Algo
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
    # for node in dom_dict.keys():
    #     print(node.name)
    #     print(f'Block: {node.name}  has a DF of {[df.name for df in dom_dict[node]]}')

    for register_number in range(3):
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
                    dom_front_node.phi_functions.append(f'{register_number}')
                    already_has_phi_func.add(dom_front_node)
                    
                    # Process each node at most once
                    if dom_front_node not in ever_on_work_list:
                        work_list.add(dom_front_node)
                        ever_on_work_list.add(dom_front_node)
                        
    return block_graph

# Driver code for testing
start_time = time.time()
instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "jmp 1 1 2", "d 1 1", "e 2 2", "f 2 2", "g 1 2"]

# Extending the code to arbitrary lengths for stress testing
# for _ in range(9):
#     instruction_list.extend(instruction_list)
# print(len(instruction_list))

block_graph = set_up_basic_block_cfg(instruction_list)
block_graph = phi_function_locations(block_graph)
for node in block_graph:
    print("-"*20)
    print(node)
print("-"*20)
        
end_time = time.time()
print('\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))