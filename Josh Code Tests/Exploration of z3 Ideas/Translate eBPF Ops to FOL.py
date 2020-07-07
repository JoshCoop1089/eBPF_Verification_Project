# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 16:03:04 2020

@author: joshc
"""


"""
Given a specific ebpf opcode, how do you take it and model it as an FOL equation 
    to put into z3?
    
    First Thoughts: (4pm 7/5)
        set up bitvec variables to model the values held in a register
        use size 4 bitvecs to test in beginning, can set bitvec size as a variable
            to use different sizes in the future
        Functions to Model:
            bpf_add
            bpf_left_shift
            bpf_and
        variable naming scheme
            
        bpf_add:
            inputs:
                src register value
                dest register value

"""
from z3 import *

a = Int('a')
b = Int('b')
s = Solver()
s.add(a < 3)
s.add(b < 3)
s.add(a >= 0)
s.add(b >= 0)
s.add(a+b > 1)
# while s.check() == sat:
#   print (s.model())
#   s.add(Or(a != s.model()[a], b != s.model()[b]))

# Dynamic Creation of Variable storage for SSA attempts

regChanges = [Int(str(i)) for i in range(4)]
# regChanges[0] = Int('0')
# regChanges[1] = Int('1')
s.add(regChanges[0] == a)
while s.check() == sat:
  print (s.model())
  s.add(Or(a != s.model()[a], b != s.model()[b]))
def addVariable(reg_to_change, regChangesCounter):
    return 0