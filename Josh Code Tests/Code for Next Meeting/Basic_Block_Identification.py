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
import matplotlib.pyplot as plt

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
        print(f'Instruction {self.instruction_number}')
        print(f'Instruction: {self.full_instruction}')
        print(f'Source: {self.input_value}\tTarget: {self.target_reg}')
        return ""  
    
# Basic Block holds all Instruction_Info commands for reference in a specific chunk of straightline code
class Basic_Block:
    def __init__ (self, instruction_chunk, instruction_list, graph):
        self.name = "Instructions in Block: " + str(instruction_chunk).strip("[]")
        self.block_instructions = []
        for instruction_number in instruction_chunk:
            self.block_instructions.append(instruction_list[instruction_number])
        
        # The head of this block can be referenced in linking to other blocks
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
        print('Instructions in Block:')
        for instruction in self.block_instructions:
            print(instruction)
        print(f'Block Forward Links to Instructions: {self.output_links}')
        print(f'Block Backward Links to Instructions: {self.input_links}')
        return ""
            
# Define what instructions can be reached from another instruction
     # This is a precursor function for basic block identification
def extract_all_edges_from_instruction_list(instruction_list, graph):
    for instruction_number, instruction in enumerate(instruction_list):
        if instruction_number == len(instruction_list) - 1:
            break
        graph.add_edge(instruction_number, instruction_number+1)
        if instruction.offset != 0:
            graph.add_edge(instruction_number, instruction_number+instruction.offset+1)
    return graph

# Identifying Leaders in the linked instructions to form basic blocks
def identify_leaders(instruction_list):
    leader_set = set()    
    for instruction_number, instruction in enumerate(instruction_list):
        # Rule 1 - First Instruction is a leader
        if instruction_number == 0:
            leader_set.add(instruction_number)
        
        # IndexOutOfBound protection, last node can still be found as a possible leader below
        elif instruction_number == len(instruction_list) - 1:
            break
        
        else:
            if "jmp" in instruction.keyword:
                # Rule 2 - Instruction L is a leader if there is another instruction which jumps to it
                leader_set.add(instruction_number + instruction.offset + 1)
                
                # Rule 3 - Instruction L is a leader if it immediately follows a jump instruction
                leader_set.add(instruction_number + 1)
    return leader_set

# A block consists of a leader, and all instructions until the next leader
def identify_the_instructions_in_basic_blocks(instruction_list):
    leader_list = sorted(list(identify_leaders(instruction_list)))
    block_list = []
    while len(block_list) < len(leader_list):
        instruction_start_index = len(block_list)
        instruction_end_index = instruction_start_index + 1
        
        # Get all the instruction numbers between two subsequent leader instruction numbers
        try:
            basic_block = [i for i in range(leader_list[instruction_start_index],
                                            leader_list[instruction_end_index])]
        except IndexError:
            basic_block = [i for i in range(leader_list[instruction_start_index],
                                            len(instruction_list))]
        block_list.append(basic_block)
        
    return block_list

# Finding out how to link Basic_Block objects together
def get_edges_between_basic_blocks(block_list):
    block_graph = nx.DiGraph()
    for starting_block in block_list:
        for forward_link in starting_block.output_links:
            next_blocks = [block for block in block_list if starting_block.final_instruction
                                                            in block.input_links]
            for next_block in next_blocks:
                block_graph.add_edge(starting_block, next_block)
    return block_graph    


# Driver code for testing
start_time = time.time()
instruction_graph = nx.DiGraph()
instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "jmp 1 1 2", "d 1 1", "e 2 2", "f 2 2", "g 1 2"]

# Extending the code to arbitrary lengths for stress testing
# for _ in range(9):
#     instruction_list.extend(instruction_list)
# print(len(instruction_list))

instruction_list = [Instruction_Info(instruction, number) for number, instruction in enumerate(instruction_list)]
instruction_graph = extract_all_edges_from_instruction_list(instruction_list, instruction_graph)
# nx.draw(instruction_graph)

block_list_chunks = identify_the_instructions_in_basic_blocks(instruction_list)
block_list = []
for block_chunk in block_list_chunks:     
    block_list.append(Basic_Block(block_chunk, instruction_list, instruction_graph))

block_graph = get_edges_between_basic_blocks(block_list)
start_block = [block_node for (block_node, indegree) in block_graph.in_degree() if indegree == 0]
dom_dict = nx.dominance_frontiers(block_graph, start_block[0])
nx.draw(block_graph)
print("\n".join([f'{block.name} links forward to {end.name}' for (block, end) in block_graph.edges()]))
 
end_time = time.time()
print('\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))