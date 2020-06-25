# -*- coding: utf-8 -*-
"""
Created on Tue Jun  23 2020

@author: Sammy

"""  
from z3 import *

solver = Solver()

"""
instruction fields are:

code = opcode   | usually unisgned 8 bit  | 
dst = dst_reg   | usually unisgned 8 bit  | 
src = src_reg   | usually unsigned 8 bit  | represent any nonzero value with 1
off = offset    | usually signed 16 bit   | represent any nonzero value with 1
imm = constant  | usually signed 32 bit   | represent any nonzero value with 1
"""

# code = Int("code") #commented out because it's not used

# dst = Int("dst") #commented out because it's not used

src = Int("src")
solver.add(Or(src == 0, src == 1))

off = Int("off")
solver.add(Or(off == 0, off == 1))

imm = Int("imm")
solver.add(Or(imm == 0, imm == 1))

"""
A few other fields of note:

bpf_src represents BPF_SRC(insn->code)      | bool for if it is BPF_X
bpf_class represents BPF_CLASS(insn->code)  | bool for if it is BPF_ALU64

is_ptr for whether src_reg is a pointer
  Technically, there are edge cases where the program is unaware if src_reg
  is a pointer (handled in 6085 of verifier.c), but for simplicity I have
  assumed whether it is a pointer is a known boolean.

PASS is forced to False if the program would error
"""

bpf_src = Bool("bpf_src")
bpf_class = Bool("bpf_class")
is_ptr = Bool("is_ptr")
PASS = Bool("PASS")

"""
When creating formulas for L48 and L59, you'll see 'False'

This is in the place of get_reg_arg, which will check to see
if a register is valid, and returns False to show there is no
error. For now, we are assuming that all registers are valid,
so I'm just using False instead.
"""

L41_if = Bool("L41_if")
solver.add(L41_if == bpf_src)

L42_if = Bool("L42_if")
solver.add(L42_if == And(L41_if, Or(imm != 0, off != 0)))
solver.add(Implies(L42_if, Not(PASS)))

L48err = Bool("L48err")
solver.add(L48err == And(L41_if, Not(L42_if), False))
solver.add(Implies(L48err, Not(PASS)))

L51_else = Bool("L51_else")
solver.add(L51_else != L41_if)

L52_if = Bool("L52_if")
solver.add(L52_if == And(L51_else, Or(src != 0, off != 0)))
solver.add(Implies(L52_if, Not(PASS)))

L59_err = Bool("L59_err")
solver.add(L59_err == False)
solver.add(Implies(L59_err, Not(PASS)))

L63_if = Bool("L63_if")
solver.add(L63_if == bpf_src)

L67_if = Bool("L67_if")
solver.add(L67_if == And(L63_if, bpf_class))

L74_else = Bool("L74_else")
solver.add(L74_else == And(L63_if, Not(L67_if)))

L76_if = Bool("L76_if")
solver.add(L76_if == And(L74_else, is_ptr))
solver.add(Implies(L76_if, Not(PASS)))

L81_elif = Bool("L81_elif")
solver.add(L81_elif == And(L74_else, Not(L76_if), Not(is_ptr)))

L91_else = Bool("L91_else")
solver.add(L91_else == Not(L63_if))

while solver.check() == sat:
  m = solver.model()
  if(m[PASS] == True):
    print (m)
  
  solver.add(Or(
                src != solver.model()[src],
                off != solver.model()[off],
                imm != solver.model()[imm],
                #bpf_src != m[bpf_src],
                #bpf_class != m[bpf_class],
                #is_ptr != m[is_ptr]
                ))

print("Done")


