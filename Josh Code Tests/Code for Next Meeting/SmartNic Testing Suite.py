# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 21:16:48 2020

@author: joshc
Using tests from:
    https://github.com/smartnic/superopt/blob/master/src/isa/ebpf/inst_test.cc

Tests 5 - 10 omitted due to endian conversions

Outputs are for the 9/3/20 version of FOL_from_BPF
Expected Results are from smartnic code
"""
from FOL_from_BPF import *

instructions1 = "{inst(MOV64XC, 0, 0xffffffff),  /* mov64 r0, 0xffffffff */                         inst(ADD64XY, 0, 0),           /* add64 r0, r0 */                         inst(EXIT),                    /* exit, return r0 */                        };"
instructions2 = "{inst(MOV64XC, 0, 0xffffffff),  /* mov64 r0, 0xffffffff */                         inst(ADD32XY, 0, 0),           /* add32 r0, r0 */                         inst(EXIT),                    /* exit, return r0 */                        };"
instructions3 = "{inst(MOV32XC, 0, -1),         /* r0 = 0x00000000ffffffff */                         inst(ADD64XC, 0, 0x1),        /* r0 = 0x0000000100000000 */                         inst(MOV64XC, 1, 0x0),        /* r1 = 0 */                         inst(JEQXC, 0, 0, 4),         /* if r0 == 0, ret r0 = 0x100000000 */                         inst(MOV64XC, 0, -1),         /* else r0 = 0xffffffffffffffff */                         inst(JEQXC, 0, 0xffffffff, 1),/* if r0 == -1, ret r0 = 0 */                         inst(EXIT),                   /* else ret r0 = 0xffffffffffffffff */                         inst(MOV64XC, 0, 0),                         inst(EXIT),                        };"
instructions4 = "{inst(MOV32XC, 0, 0xffffffff), /* r0 = 0x00000000ffffffff */                         inst(ADD64XC, 0, 0x1),        /* r0 = 0x0000000100000000 */                         inst(MOV64XC, 1, 0x0),        /* r1 = 0 */                         inst(JEQXY, 0, 1, 4),         /* if r0 == r1, ret r0 = 0x100000000 */                         inst(MOV64XY, 1, 0),          /* else r1 = r0 */                         inst(JEQXY, 0, 1, 1),         /* if r0 == r1, ret r0 = 0x100000001 */                         inst(EXIT),                   /* else ret r0 = 0x100000000 */                         inst(ADD64XC, 0, 0x1),                         inst(EXIT),                        };"
instructions11 = "{inst(MOV64XC, 0, -1),         /* r0 = 0xffffffffffffffff */                          inst(RSH64XC, 0, 63),         /* r0 >> 63 */                          inst(JEQXC, 0, 1, 1),         /* if r0 != 0x1, exit */                          inst(EXIT),                   /* exit */                          inst(MOV64XC, 0, -1),         /* else r0 = 0xffffffffffffffff */                          inst(RSH32XC, 0, 1),          /* r0 >>32 1 */                          inst(EXIT),                   /* exit, return r0 */                         };"
instructions12 = "{inst(MOV64XC, 0, -1),         /* r0 = 0xffffffffffffffff */                         inst(ARSH64XC, 0, 63),        /* r0 >> 63 */                          inst(MOV64XC, 1, -1),         /* r1 = 0xffffffffffffffff */                          inst(JEQXY, 0, 1, 1),         /* if r0 != r1, exit */                          inst(EXIT),                   /* exit */                          inst(MOV64XC, 0, -1),         /* else r0 = 0xffffffffffffffff */                          inst(ARSH32XC, 0, 1),         /* r0 >>32 1 */                          inst(EXIT),                   /* exit, return r0 */                         };"
instructions13 = "{inst(MOV32XC, 0, -1),         /* r0 = 0xffffffff */                          inst(JGTXC, 0, 0, 1),         /* if r0 <= 0, ret r0 = 0xffffffff */                          inst(EXIT),                          inst(MOV64XC, 1, -1),         /* else r1 = 0xffffffffffffffff */                          inst(JGTXY, 1, 0, 1),         /* if r1 <= r0, ret r0 = 0xffffffff */                          inst(EXIT),                          inst(MOV64XC, 0, 0),          /* else r0 = 0 */                          inst(EXIT),                   /* exit, return r0 */                         };"
instructions14 = "{inst(MOV64XC, 0, -1),         /* r0 = -1 */                          inst(JSGTXC, 0, 0, 4),        /* if r0 s>= 0, ret r0 = -1 */                          inst(JSGTXC, 0, 0xffffffff, 3),/* elif r1 s> 0xffffffff, ret r0 = -1 */                          inst(MOV64XC, 1, 0),          /* r1 = 0 */                          inst(JSGTXY, 0, 1, 1),           /* if r0 s> r1, ret r0 = -1 */                          inst(MOV64XC, 0, 0),          /* else r0 = 0 */                          inst(EXIT),                   /* exit, return r0 */                         };"
instructions15 = "{inst(MOV32XC, 0, -1),         /* r0 = 0xffffffff */                          inst(JGTXC, 0, -2, 1),        /* if r0 > 0xfffffffffffffffe, ret r0 = 0xffffffff */                          inst(MOV64XC, 0, 0),          /* else ret r0 = 0 */                          inst(EXIT),                         };"

test_list_with_stars = [instructions1, instructions2, instructions3, instructions4, instructions11, 
             instructions12, instructions13, instructions14, instructions15]

tests_1_to_4 = []
tests_11_to_15 = []

for instruction in test_list_with_stars[:4]:
    new_inst = translate_smartnic_to_python_stars_comments(instruction)
    tests_1_to_4.append(new_inst)
# print(tests_1_to_4[0])

for instruction in test_list_with_stars[4:]:
    new_inst = translate_smartnic_to_python_stars_comments(instruction)
    tests_11_to_15.append(new_inst)
# print(tests_11_to_15)

for num, instruction in enumerate(tests_1_to_4, 1):
    print("*"*20+f"\nInstruction Test #{num}\n")
    create_program(instruction, 2, 64)
for num, instruction in enumerate(tests_11_to_15, 11):
    print("*"*20+f"\nInstruction Test #{num}\n")
    create_program(instruction, 2, 64)

"""
Test 1:
    Output:     r0 =    18446744073709551614
    Expected:   r0 =    0xfffffffffffffffe; 
                        18446744073709551614 (decimal)
                    
Test 2:
    Output:     r0 =    4294967294
    Expected:   r0 =    0xfffffffe; 
                        4294967294 (decimal)
                    
Test 3:
    Output:     r0 =    0
    Expected:   r0 =    0
                    
Test 4:
    Output:     r0 =    4294967297
    Expected:   r0 =    0x100000001:
                        4294967297 (decimal)
                    
Test 11:
    Output:     r0 =    2147483647 (decimal)
    Expected:   r0 =    0x7fffffff (hex)
                        2147483647 (decimal)
Test 12:
    Output:     r0 =    2147483647 (decimal)
                        0x7fffffff (hex)
                        
    Expected:   r0 =    0xffffffff (hex)
                        4294967295 (decimal)
                    
Test 13:
    Output:     r0 =    0
    Expected:   r0 =    0
                    
Test 14:
    Output:     r0 =    0
    Expected:   r0 =    0
                    
Test 15:
    Output:     r0 =    0
    Expected:   r0 =    0  

Passed: 8
Attempted: 9    

Reasons for Failed Tests:
    12) problems with arsh32 taking the front bit of the 64bit register value, not the 32 bit value
"""