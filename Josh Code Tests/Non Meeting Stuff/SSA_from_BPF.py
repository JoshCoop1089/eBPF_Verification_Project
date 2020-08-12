# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 20:38:59 2020

@author: joshc
"""
import time
from collections import defaultdict 

class Node_Info:
    def __init__ (self, instruction, number):
        self.full_instruction = instruction
        self.node_number = number
        self.pred_nodes = []
        self.pred_set = set()
        self.paths_to_node = []
        self.dominated_by = set()
        self.dominance_frontier_nodes = set()
        self.phi_func = []
        
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
        print(f'Source: {self.input_value}\tTarget: {self.target_reg}')
        # print(f'Direct Pred Nodes: {self.pred_nodes}')
        # print(f'Pred node Set: {self.pred_set}')
        # print(f'Paths to Node: {len(self.paths_to_node)}')
        # for path in self.paths_to_node:
        #     print("New Path:")
        #     for node in path:
        #         print(node, end = " ")
        #     print()    
        # print(f'Dominator Nodes: {self.dominated_by}')
        print(f'Dominance Frontier: {self.dominance_frontier_nodes}')
        print(f'{self.phi_func}')
        return ""
   
# This class represents a directed graph using adjacency list representation 
# Modified geek4geek dfs code
class Graph: 
    def __init__(self): 
        self.graph = defaultdict(list)  
   
    def addEdge(self, start, end): 
        self.graph[start].append(end) 
    
    """Modified Backtracking algo, code from https://www.python.org/doc/essays/graphs/
    
    This code blows up if tracing more than 64 instructions.  Figure out a better 
        way to find sub paths.  Either use tail recursion, or some type of 
        memoization of past paths.
    
    Depending on how monday meeting goes, will optimize more in future, tonight's focus
        is still on getting the phi function placement to work'
    """
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


def establish_dominators(node_list): 
    g = Graph()
    for node in node_list:
        for pred_node in node.pred_nodes:
            # print(f'Adding edge from s: {pred_node} to d: {node.node_number}')
            g.addEdge(pred_node, node.node_number)
    # print()
            
    # Find out what paths lead to a specific node from the initial node
    for d, node in enumerate(node_list):
        node.paths_to_node = g.find_all_paths(0, d)
    
    # Using all possible paths, get the set of dominator nodes and predecessor nodes
    for node in node_list:
        sets_from_paths = []
        for path in node.paths_to_node:
            sets_from_paths.append(set(path))
        node.dominated_by = set.intersection(*sets_from_paths)
        node.pred_set = set.union(*sets_from_paths)
        node.pred_set.remove(node.node_number)
    
    return node_list

# Find the dominance frontier of each node
def node1_sdom_node2_check(node1, node2):
    """
    Checking if node1 sdom node2 for use in Dominance Frontier selection
    
    ie, return True if node1 is in the dominator set of node 2, and node1 == node 2
    """
    return (node1.node_number in node2.dominated_by) and (node1.node_number != node2.node_number)  
    
def find_dominance_frontier(node_list):
    """
    From slide 20 in lecture7.ppt in Code for Next Meeting
    Dominance Frontier Algorithm:
        DF(node D) = {N | There exists a node Pred, which is a predecessor of node N such that
                 node D dominates node Pred, and node d doesn't strictly dominate node N'}
        
        The predecessor nodes of node N would be any node on a path that leads to N
        So after establishing path, we should also take the union of the paths to be searched
        
    """
    # Finding the dominance frontier of checking_node (node D)
    for checking_node in node_list:

        # possible_DF_Node  is node N
        for possible_DF_node in node_list:
            
            if not node1_sdom_node2_check(checking_node, possible_DF_node):
                # Check the prednode set for any node that is dominated by checking_node
                for node in possible_DF_node.pred_set:
                    if checking_node.node_number in node_list[node].dominated_by:
                        checking_node.dominance_frontier_nodes.add(possible_DF_node.node_number)
    return node_list

# Do the whole Phi Function Algo
def phi_function_locations(node_list):
    """
    From slide 26 in lecture7.ppt in Code for Next Meeting
    
    Note: Can a node have a phi function for different variables? 
        ie, can it need a phi func for register 1 and register 2?  I think this 
        should be valid, because since I haven't made any choice about phi func
        usage based on inputs, we need to know about every possible change to any 
        variable across the whole program!
    """
    for register_number in range(10):
        work_list = set()
        ever_on_work_list = set()
        already_has_phi_func = set()
        
        # Get all nodes which assign a value to our target_reg
        for node_number, node in enumerate(node_list):
            if "jmp" not in node.keyword and node.target_reg == register_number:
                work_list.add(node_number)
                
        ever_on_work_list = work_list
        while len(work_list) != 0:
            check_dom_front_of = work_list.pop()
            for dom_front_node in node_list[check_dom_front_of].dominance_frontier_nodes:
                
                # Insert at most 1 phi function per node
                if "jmp" not in node_list[dom_front_node].keyword and dom_front_node not in already_has_phi_func:
                    node_list[dom_front_node].phi_func.append(f'Need a phi func for register {register_number}')
                    already_has_phi_func.add(dom_front_node)
                    
                    # Process each node at most once
                    if dom_front_node not in ever_on_work_list:
                        work_list.add(dom_front_node)
                        ever_on_work_list.add(dom_front_node)
                        
    return node_list
                        
                        
start_time = time.time()
instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "jmp 1 1 2", "d 1 1", "e 2 2", "f 2 2"]
# for _ in range(3):
#     instruction_list.extend(instruction_list)
# print(len(instruction_list))
node_list = [Node_Info(instruction, number) for number, instruction in enumerate(instruction_list)]
node_list = find_all_edges(node_list)
node_list = establish_dominators(node_list)
node_list = find_dominance_frontier(node_list)
node_list = phi_function_locations(node_list)
for node in node_list:
    print(node)
end_time = time.time()
print('\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))