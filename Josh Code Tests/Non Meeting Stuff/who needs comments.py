# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 14:36:29 2020

@author: joshc
"""
import itertools, copy, time
from z3 import *
class Register_Info:
    def __init__(self, name, reg_bit_size,  reg_type = ""):
        self.name = BitVec(name, reg_bit_size)
        self.reg_name = name 
class Individual_Branch:
    def __init__(self, num_Regs, reg_bit_width):
        self.num_Regs = num_Regs
        self.reg_bit_width = reg_bit_width
        self.solver_object = Solver()
        self.register_history = [[]]
        self.instruction_list = [""]
        self.instruction_number = 0
        self.problem_flag = 0
        self.skip_flag = 0    
    def __str__(self):
        print()
        print("The current contents of this branch are:")
        print("\tRegister Bit Width: %d"%self.reg_bit_width)
        print("\tCurrent Instruction Number is: %d"%self.instruction_number)
        print("\tProblem Flag's Value': %d"%self.problem_flag)
        print("\tThe register history looks like: \n")
        r_h = self.register_history
        for reg in r_h:
            for reg_instance in reg:
                print("\t" + reg_instance.reg_name, end = " ")
            print()
        return "\n"
def extend_the_number(value, value_bit_size, register_state_helper):
    valueBV = BitVecVal(value, value_bit_size)    
    delta_bit_size = register_state_helper.reg_bit_width - value_bit_size    
    if delta_bit_size > 0:
        if value >= 0:
            extended_value = ZeroExt(delta_bit_size, valueBV)
        else:
            extended_value = SignExt(delta_bit_size, valueBV)        
    elif delta_bit_size == 0:
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)                               
    else:
        print("How did you get this branch to happen? How is your imm value bigger than the reg size of the program?")
        extended_value = BitVecVal(value, register_state_helper.reg_bit_width)    
    return extended_value
def get_the_locations(source_reg, register_state_helper, destination_reg = -1):
    r_s_h = register_state_helper
    s_r = source_reg
    source_val = r_s_h.register_history[s_r][-1].name        
    if destination_reg == -1:
        d_r = s_r
        destination_old_val = source_val
    else:
        d_r = destination_reg
        destination_old_val = r_s_h.register_history[d_r][-1].name
    r_s_h.register_history[d_r].append(\
               Register_Info("r%d_%d"%(d_r, r_s_h.instruction_number),r_s_h.reg_bit_width))    
    destination_new_val = r_s_h.register_history[d_r][-1].name
    list_of_locations = [source_val, destination_old_val, destination_new_val]    
    return list_of_locations, r_s_h
def get_the_locations_and_extend(input_value, target_reg, register_state_helper, source_reg, extension_length):
    r_s_h = register_state_helper
    if source_reg:
        list_of_locations, r_s_h = get_the_locations(input_value, r_s_h, target_reg)
    else:
        list_of_locations, r_s_h = get_the_locations(target_reg, r_s_h)
        if input_value > 2 ** (r_s_h.reg_bit_width - 1) - 1 or input_value < -1 * (2 ** (r_s_h.reg_bit_width - 1)):
            r_s_h.problem_flag = r_s_h.instruction_number * -1        
        else:
            if extension_length != 0:
                list_of_locations[0] = extend_the_number(input_value, extension_length, r_s_h)
            else:
                list_of_locations[0] = BitVecVal(input_value, r_s_h.reg_bit_width)                
    return list_of_locations, r_s_h
def add_two_values(input_value, target_reg, register_state_helper, source_reg, extension_length):
    r_s_h = register_state_helper
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    output_function = list_of_locations[2] == list_of_locations[1] + list_of_locations[0]    
    no_overflow = BVAddNoOverflow(list_of_locations[0], list_of_locations[1], True)
    no_underflow = BVAddNoUnderflow(list_of_locations[0], list_of_locations[1])    
    add_function = And(output_function, no_overflow, no_underflow)    
    return add_function, r_s_h
def mov_to_reg(input_value, target_reg, register_state_helper, source_reg, extension_length):
    r_s_h = register_state_helper    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    mov_function = list_of_locations[2] == list_of_locations[0]
    return mov_function, r_s_h
def jump_command(input_value, target_reg, offset, register_state_helper, source_reg, extension_length):
    r_s_h = register_state_helper    
    list_of_locations, r_s_h = get_the_locations_and_extend(input_value, target_reg, r_s_h, source_reg, extension_length)
    del r_s_h.register_history[target_reg][-1]
    comparison_statement = list_of_locations[0] == list_of_locations[1]    
    next_ins = r_s_h.instruction_number + 1
    next_ins_with_offset = next_ins + offset
    before_jump_reg_names = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    jump_constraints = True
    for instruction_number, instruction in enumerate(r_s_h.instruction_list[next_ins:next_ins_with_offset], next_ins):
        if register_state_helper.skip_flag > instruction_number:
            continue        
        r_s_h.instruction_number += 1
        instruction_constraints , r_s_h = \
            create_new_constraints_based_on_instruction_v2(r_s_h.instruction_list[instruction_number], register_state_helper)
        jump_constraints = And(instruction_constraints, jump_constraints)   
    after_branch_reg_names = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    for reg_number, reg_list in enumerate(r_s_h.register_history):
        if len(reg_list) == 1:
            continue        
        name = f'r{reg_number}_{next_ins_with_offset}_after_jump'
        reg_list.append(Register_Info(name, r_s_h.reg_bit_width))
        name_constraints = If(comparison_statement, reg_list[-1].name == after_branch_reg_names[reg_number].name,reg_list[-1].name == before_jump_reg_names[reg_number].name)        
        jump_constraints = And(name_constraints, jump_constraints)
    r_s_h.skip_flag = max(next_ins_with_offset, r_s_h.skip_flag)
    return jump_constraints, register_state_helper
def exit_instruction(register_state_helper):
    exit_ins = Bool("exit_%d"%(register_state_helper.instruction_number))
    return exit_ins, register_state_helper 
def check_and_print_model(register_state_helper):
    s = register_state_helper.solver_object
    instruction_list = register_state_helper.instruction_list
    problem_flag = register_state_helper.problem_flag
    if problem_flag == 0:
        problem_flag = register_state_helper.instruction_number    
    if s.check() == sat:
        print("\nThe last instruction attempted was #%d:\n"%(abs(problem_flag)))
        if problem_flag == (len(instruction_list) - 1):
            print("Program successfully added all instructions")
        else:
            print("Program didn't successfully add all given instructions")
        print("The stored model contains the following variable states")
        print(s.model())
    else:
        print("You screwed something up if this ever gets printed")    
    print_current_register_state(register_state_helper)
    print()   
def print_current_register_state(register_state_helper):
    print()    
    r_s_h = register_state_helper
    r_s_h.solver_object.check()
    current_reg_states = [r_s_h.register_history[i][-1] for i in range(r_s_h.num_Regs)]
    print("The register values are currently:")
    for j, register in enumerate(current_reg_states):
        print("\tRegister %d:\t"%j, end = " ")
        if "start" in register.reg_name:
            print("Not Initalized")
        else:
            try:
                print(r_s_h.solver_object.model()[register.name])
            except Z3Exception:
                print("oops, z3 said nope! wonder why...")
    print()
def translate_to_bpf_in_c(program_list):
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
            if keyword == "addI4":
                instruction = f'BPF_ALU32_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addI8":
                instruction = f'BPF_ALU64_IMM(BPF_ADD, BPF_REG_{target_reg}, {value})'
            elif keyword == "addR":
                instruction = f'BPF_ALU64_REG(BPF_ADD, BPF_REG_{target_reg}, BPF_REG_{value})'
            elif keyword == "movI4" or keyword == "movI8":
                instruction = f'BPF_MOV64_IMM(BPF_REG_{target_reg}, {value})'
            elif keyword == "movR":
                instruction = f'BPF_MOV64_REG(BPF_REG_{target_reg}, BPF_REG_{value})'
            elif keyword == "exit":
                instruction = "BPF_EXIT_INSN()"
        elif len(split_ins) == 4:
            offset = int(split_ins[3])
            if keyword == "jneI4" or keyword == "jneI8":
                instruction = f'BPF_JMP_IMM(BPF_JNE, BPF_REG_{target_reg}, {value}, {offset})'
            elif keyword == "jneR":
                instruction = f'BPF_JMP_REG(BPF_JNE, BPF_REG_{target_reg}, BPF_REG_{value}, {offset})'
        output += instruction + ", "    
    print("\nThis program would be written as the following for BPF in C:\n")        
    print(output)
def create_register_list(register_state_helper):
    register_state_helper.register_history = [[Register_Info("r"+str(i) + "_start", register_state_helper.reg_bit_width)] for i in range(register_state_helper.num_Regs)]    
    return register_state_helper  
def incorrect_instruction_format(instruction, register_state_helper):
    print("\nIncorrect instruction format for instruction number: %d"%register_state_helper.instruction_number)
    print("Please retype the following instruction: \n\t-->  %s  <--"%instruction)
    register_state_helper.problem_flag = register_state_helper.instruction_number * -1
    new_constraints = False    
    return new_constraints, register_state_helper   
def create_new_constraints_based_on_instruction_v2(instruction, register_state_helper):
    print("Attempting to combine solver with instruction #%d: %s"%(register_state_helper.instruction_number, instruction))
    split_ins = instruction.split(" ")    
    if len(split_ins) < 3 or len(split_ins) > 4:
        new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)
    else:
        keyword = split_ins[0]
        input_value = int(split_ins[1])
        target_reg = int(split_ins[2])
        if "I4" in keyword:
            source_reg = False
            extension_length = register_state_helper.reg_bit_width//2
        elif "I8" in keyword:
            source_reg = False
            extension_length = 0
        elif "R" in keyword:
            source_reg = True
            extension_length = 0
        if len(split_ins) == 3:           
            if "add" in keyword:
                new_constraints, register_state_helper = add_two_values(input_value, target_reg, register_state_helper, source_reg, extension_length)
            elif "mov" in keyword:
                new_constraints, register_state_helper = mov_to_reg(input_value, target_reg, register_state_helper, source_reg, extension_length)
            elif keyword == "exit":
                new_constraints, register_state_helper = exit_instruction(register_state_helper)
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)
        elif len(split_ins) == 4:
            offset = int(split_ins[3])            
            if "jne" in keyword:
                new_constraints , register_state_helper = jump_command(input_value, target_reg, offset, register_state_helper, source_reg, extension_length)
            else:
                new_constraints, register_state_helper = incorrect_instruction_format(instruction, register_state_helper)    
    # print(register_state_helper)
    # print_current_register_state(register_state_helper)    
    return new_constraints, register_state_helper
def execute_program_v2(register_state_helper): 
    for instruction_number, instruction in enumerate(register_state_helper.instruction_list):
        register_state_helper.instruction_number = instruction_number
        if register_state_helper.skip_flag > instruction_number:
            continue        
        new_constraints, register_state_helper = create_new_constraints_based_on_instruction_v2(instruction, register_state_helper)
        register_state_helper.solver_object.push()
        register_state_helper.solver_object.add(new_constraints)
        # print(register_state_helper)
        if register_state_helper.solver_object.check() == unsat:            
            register_state_helper.solver_object.pop()
            register_state_helper.problem_flag = register_state_helper.instruction_number * -1            
            if register_state_helper.instruction_number == 0:
                register_state_helper.problem_flag = -1
        if register_state_helper.problem_flag < 0:
            print("\nThe program encountered an error on instruction #%s"%abs(register_state_helper.problem_flag))
            print("\t-->  " + register_state_helper.instruction_list[abs(register_state_helper.problem_flag)] + "  <--")
            print("The last viable solution before the problem instruction is shown below:")
            break
    # print_current_register_state(register_state_helper)
    check_and_print_model(register_state_helper)
    translate_to_bpf_in_c(register_state_helper.instruction_list)              
def create_program(program_list = "", num_Regs = 4, reg_bit_width = 8):
    start_time = time.time()
    if program_list == "":
        program_list = ["movI8 4 1", "movI8 3 2", "addR 1 2", "jneI8 5 2 2", "addR 1 1", "addI4 3 2", "addR 1 2", "addR 2 1", "exit 0 0"]
    register_state_helper = Individual_Branch(num_Regs, reg_bit_width)
    register_state_helper = create_register_list(register_state_helper)
    register_state_helper.instruction_list = program_list    
    execute_program_v2(register_state_helper)    
    end_time = time.time()
    print('\n\n-->  Elapsed Time: %0.3f seconds  <--' %(end_time-start_time))    
create_program()