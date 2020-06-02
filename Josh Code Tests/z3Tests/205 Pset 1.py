# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 11:47:47 2020

@author: joshc
"""


"""
Using PSet 1 Problems from 205 as a base for practicing z3 functions
"""

'''
Problem 4:
    
    a = User can access file system
    s = User can save
    u = System being upgraded
    
    1) u => ~a
    2) a => s
    3) ~s => ~u
    
    According to HW, U = True, A = False, S = True satisfies the given params.
        But, my work on the HW wasn't to find all possible sats, just if there was 
        a possible.
        
    Code below outputs u = false, a = false, s = false as the "answer"
    
    How to get it to output all possible satisfiable options?
'''
from z3 import *
a, s, u = Bools('a s u')
cond1 = Implies(u, Not(a))
cond2 = Implies(a,s)
cond3 = Implies(Not(s), Not(u))                
s = Solver()
s.add(cond1,cond2,cond3)
print(s.check())
print(s.model())

