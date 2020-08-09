# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 20:38:59 2020

@author: joshc
"""

from collections import defaultdict 

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
        # print(f'Paths to Node: {len(self.paths_to_node)}')
        # for path in self.paths_to_node:
        #     print("New Path:")
        #     for node in path:
        #         print(node, end = " ")
        #     print()    
        print(f'Dominator Nodes: {self.dominated_by}')
        return ""
   
# This class represents a directed graph using adjacency list representation 
# Modified geek4geek dfs code
class Graph: 
    def __init__(self): 
        self.graph = defaultdict(list)  
   
    def addEdge(self, start, end): 
        self.graph[start].append(end) 
    
    # Modified Backtracking algo, code from https://www.python.org/doc/essays/graphs/
    def find_all_paths(self, start, end, path=[]):
        path = path + [start]
        if start == end:
            return [path]
        
        paths = []
        for node in self.graph[start]:
            if node not in path:
                newpaths = self.find_all_paths(node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths        
        
# Define what nodes can be reached from another node
def find_all_edges(node_list):
    for node_number, node in enumerate(node_list):
        if node_number == len(node_list) - 1:
            break
    
        node_list[node_number+1].can_be_reached_from(node_number)
        if node.offset != 0:
            node_list[node_number+node.offset+1].can_be_reached_from(node_number)
    return node_list

instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "jmp 1 1 2", "d 1 2", "e 2 2", "f 2 2"]
node_list = [Node_Info(instruction, number) for number, instruction in enumerate(instruction_list)]
node_list = find_all_edges(node_list)

# Set up the graph, and add all the edges
g = Graph()
for node in node_list:
    for pred_node in node.pred_nodes:
        print(f'Adding edge from s: {pred_node} to d: {node.node_number}')
        g.addEdge(pred_node, node.node_number)
print()
        
# Find out what paths lead to a specific node from the initial node
for d, node in enumerate(node_list):
    node.paths_to_node = g.find_all_paths(0, d)

# Take the intersection of all possible paths, the result will be all nodes
    # which dominate a chosen node
for node in node_list:
    sets_from_paths = []
    for path in node.paths_to_node:
        sets_from_paths.append(set(path))
    node.dominated_by = set.intersection(*sets_from_paths)
    print(node)    

# Find the dominance frontier of each node
# Do the whole Phi Function Algo

