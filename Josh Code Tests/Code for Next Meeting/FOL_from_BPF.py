# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 19:18:26 2020

@author: joshc

FOL Actions:
    
    Iterate through the block list
    Add each instruction to the general formula
        Update the in block current register name after an instruction
    Jump conditions don't get considered because they're only for breaking up blocks
    
Deciding FOL for phi functions:

1) Find the immediate dominator (ImmDom) of the block in question (PhiN)
2) for all the immediate predecessor blocks (predBlock) of PhiN
    2a) Trace the shortest path from the ImmDom to a single predBlock
    2b) Establish the series of true/false for all the jump conditions along the path
        2b1) If len(shortest_path) is 0, the only condition is a false from ImmDom
    2c) Take the conjunction of all conditions from 2b
    2d) Take the conjunction of 2c with PhiN_register == predBlock_register
3) PhiN phi function for a register will be the disjunction of all distinct conjunctions from 2d

"""
from Basic_Block_CFG_Creator import *
import time

# Driver code for testing
start_time = time.time()
num_regs = 4
reg_size = 8

# 3 Pred Node at end
# instruction_list = ["a 1 1", "jmp 1 1 9", "b 1 1",  "jmp 1 1 2", "c 1 1", "jmp 1 1 5", 
#     "d 1 1", "jmp 1 1 1", "e 1 1", "f 1 1", "g 1 1", "h 1 1"]

# Multiple variables need phi functions
instruction_list = ["a 1 1", "b 1 2", "jmp 1 2 2", "c 2 1", "jmp 1 1 2", "d 1 1", "e 2 2", "f 2 2", "g 1 2"]

# Extending the code to arbitrary lengths for stress testing
# for _ in range(13):
#     instruction_list.extend(instruction_list)
print(f'Number of Instructions: {len(instruction_list)}')

block_graph, register_bitVec_dictionary = basic_block_CFG_and_phi_function_setup(instruction_list, reg_size, num_regs)    

# print([(key, register_bitVec_dictionary[key].name) for key in register_bitVec_dictionary.keys()])        
# for node in block_graph:
#     print("-"*20)
#     print(node)
# print("-"*20)

#     Deciding FOL for phi functions
start_block = [block_node for (block_node, indegree) in block_graph.in_degree() if indegree == 0]
for phi_block in block_graph:
    if phi_block.phi_functions:
        
        # 1) Find the immediate dominator (ImmDom) of the block in question (phi_block)
        ImmDom = nx.immediate_dominators(block_graph, start_block[0])[phi_block]
        pred_blocks = block_graph.predecessors(phi_block)
        print("\n"+"-"*20)
        print(f'Block: {phi_block.name}, For Register(s): {phi_block.phi_functions}')
        print(f'Immediate Dominator Block: {ImmDom.name}')

        # Repeating the path finding process for each individual phi func as a first try just to see if it works
        #  Can be optimized to somehow save a path and then reuse the path for multiple phi funcs
        for phi_func_index, register_number in enumerate(phi_block.phi_functions):
            print(f'\nFinding FOL for phifunc of Register: {register_number}')
            phi_func_name = phi_block.phi_function_named_registers[phi_func_index]
            phi_bit_vec = register_bitVec_dictionary[phi_func_name]

            # 2) For all the immediate predecessor blocks (predBlock) of phi_block
            phi_func_for_reg = False
            for pred_block in pred_blocks:
                
                # 2a) Trace the shortest path from the ImmDom to a single predBlock
                path = nx.shortest_path(block_graph, ImmDom, pred_block)
                print(f'Path is: {[block.name for block in path]}')
                
                # 2b) Establish the series of true/false for all the jump conditions along the path
                path_conditions = True
                for path_number, block_in_path in enumerate(path):
                    jump_condition = get_jump_condition(some_params, block_in_path)
                    
                    # 2b1) If len(shortest_path) is 0, the only condition is a false from ImmDom
                    if path_number == len(path) - 1:
                        path_conditions = And(path_conditions, Not(jump_condition))
                    else:
                        try:
                            next_ins = path[path_number+1].initial_instruction
                            if next_ins == block_in_path.final_instruction + 1:
                                path_conditions = And(path_conditions, jump_condition)
                            else:
                                path_conditions = And(path_conditions, Not(jump_condition))
                                
                        # You're at the pred_block before phi_block, so there are no more jumps to choose
                        except IndexError:
                            break
                # 2c) Take the conjunction of all conditions from 2b
                # Now path_conditions holds all the jump t/f
                        
                # Add on the register from the pred block
                pred_block_reg_name = pred_block.register_names_after_block_execution[phi_func_index]
                pred_reg_bit_vec = register_bitVec_dictionary[pred_block_reg_name]
                phi_to_pred = phi_bit_vec == pred_reg_bit_vec

                # Now I have a full path with assignment for one register
                # 2d) Take the conjunction of 2c with PhiN_register == predBlock_register
                full_FOL_for_path = And(path_conditions, phi_to_pred)
         
            # 3) PhiN phi function for a register will be the disjunction of all distinct conjunctions from 2d
            phi_func_for_reg = Or(phi_func_for_Reg, full_FOL_for_path)
            
            # Now this formula can be added into the solver, and all instructions can reference the phi_func_names
            # and have those names always produce the right outcome because the above formula will force a numerical
            # definition based on the path
            
end_time = time.time()
print('\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))