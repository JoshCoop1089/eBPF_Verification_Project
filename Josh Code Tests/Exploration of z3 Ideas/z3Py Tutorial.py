# -*- coding: utf-8 -*-
"""
Created on Sun Jun 28 14:57:26 2020

@author: joshc
Code from z3Py tutorial:
    https://www.cs.tau.ac.il/~msagiv/courses/asv/z3py/guide-examples.htm
"""


from z3 import *


x = Int('x')
y = Int('y')

s = Solver()
print (s)

s.add(x > 10, y == x + 2)
print (s)
print ("Solving constraints in the solver s ...")
print (s.check())

print ("Create a new scope...")
s.push()
s.add(y < 11)
print (s)
print ("Solving updated set of constraints...")
print (s.check())

print ("Restoring state...")
s.pop()
print (s)
print ("Solving restored set of constraints...")
print (s.check())

x = Int('x')
y = Int('y')

s = Solver()

# Simplify culls unneeded variables and trys to present smaller equations
print (simplify(x + y + 2*x + 3))
print (simplify(x < y + x + 2))
print (simplify(And(x + 1 >= 3, x**2 + x**2 + y**2 + 2 >= 5)))



x = Int('x')
y = Int('y')
n = x + y >= 3
print ("\nnum args: ", n.num_args())
print ("children: ", n.children())
print ("1st child:", n.arg(0))
print ("2nd child:", n.arg(1))
print ("operator: ", n.decl())
print ("op name:  ", n.decl().name())