# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 20:38:59 2020

@author: joshc
"""

"""
Thoughts on SSA and Control Flow

Identify which nodes link
Single pass through instruction list, id any jump offsets

identify which register an instruction is changing

if a node has two paths leading toward it, check if the register modified in that 
specific instruction is also modified on the path from jump to node

"""
class Node_Info:
    def __init__ (self, instruction, number):
        self.full_instruction = instruction
        self.node_number = number
        self.pred_nodes = []
        self.paths_to_node = []
        self.dominated_by = []
        self.dominance_frontier_nodes = []
        
        # Getting the specifics from an instruction
        split_ins = instruction.split(" ")        
        self.keyword = split_ins[0]
        self.input_value = int(split_ins[1])
        self.target_reg = int(split_ins[2])        
        if "jmp" in self.keyword:
            self.offset = int(split_ins[3])
        else:
            self.offset = 0

    def can_be_reached_from(self, source):
        self.pred_nodes.append(source)
        
    def __str__(self):
        print(f'Node {self.node_number}')
        print(f'Instruction: {self.full_instruction}')
        print(f'Direct Pred Nodes: {self.pred_nodes}')
        return ""
        
        
"""
Given a list of instructions, where the command is either a jump or non jump,
    identify every immediate pred node for a specific instruction (node)
    
Instructions given in FOLVerifier.py format
"""
instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "d 1 2", "e 2 2"]
node_list = [Node_Info(instruction, number) for number, instruction in enumerate(instruction_list)]

# Define what nodes can be reached from another node
for node_number, node in enumerate(node_list):
    if node_number == 0:
        node.can_be_reached_from(0)
    elif node_number == len(node_list) - 1:
        break

    node_list[node_number+1].can_be_reached_from(node_number)
    if node.offset != 0:
        node_list[node_number+node.offset+1].can_be_reached_from(node_number)
        
for node in node_list:
    print(node)     

# Find out what paths lead to a specific node
# Identify if a node is in every path for another node to show dominance
# Find the dominance frontier of each node
# Do the whole Phi Function Algo

