# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 17:32:08 2020

@author: joshc

Code Examples from:
    https://theory.stanford.edu/~nikolaj/programmingz3.html
"""


from z3 import *

Tie, Shirt = Bools('Tie Shirt')
s = Solver()
s.add(Or(Tie, Shirt), 
      Or(Not(Tie), Shirt), 
      Or(Not(Tie), Not(Shirt)))
print(s.check())
print(s.model())
print("Hello World!")