# -*- coding: utf-8 -*-
"""
Created on Tue Jun  23 2020

@author: Sammy

"""  
from z3 import *

solver = Solver()

# instruction fields are:
#
# code = opcode   | usually unisgned 8 bit  | will be 0-2 for now
# dst = dst_reg   | usually unisgned 8 bit  |
# src = src_reg   | usually unsigned 8 bit  | will be 0 or 1 for now
# off = offset    | usually signed 16 bit   | will be 0 or 1 for now
# imm = constant  | usually signed 32 bit   | will be 0 or 1 for now

code = Int("code")
solver.add(code >= 0)
solver.add(code <= 2)

src = Int("src")
solver.add(Or(src == 0, src == 1))

off = Int("off")
solver.add(Or(off == 0, off == 1))

imm = Int("imm")
solver.add(Or(imm == 0, imm == 1))

# PASS is forced to False if the program would error
PASS = Bool("PASS")

L41b = Bool("L41b")
solver.add(L41b == (code == 1)) #for now treating BPF_X as 1

L42b = Bool("L42b")
solver.add(L42b == And(L41b, Or(imm != 0, off != 0)))
solver.add(Implies(L42b, Not(PASS)))

L48err = Bool("L48err")
solver.add(L48err == And(L41b, Not(L42b), True)) #replace True with check_reg_arg
solver.add(Implies(L48err, Not(PASS)))

L51b = Bool("L51b")
solver.add(L51b != L41b)

L52b = Bool("L52b")
solver.add(L52b == And(L51b, Or(src != 0, off != 0)))
solver.add(Implies(L52b, Not(PASS)))

L59err = Bool("L59err")
solver.add(L59err == False) #replace False with check_reg_arg
solver.add(Implies(L59err, Not(PASS)))



while solver.check() == sat:
  m = solver.model()
  if(m[PASS] == True):
    print (solver.model())
  solver.add(Or(code != solver.model()[code],
           off != solver.model()[off],
           imm != solver.model()[imm]))


