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
# a, s, u = Bools('a s u')
# cond1 = Implies(u, Not(a))
# cond2 = Implies(a,s)
# cond3 = Implies(Not(s), Not(u))                
# equation = Solver()
# equation.add(cond1,cond2,cond3)

# # print(s.check())
# # print(s.model())


# # Good ol' StackOverflow with the ideas
# while (equation.check() == sat):
#   print (equation.check())
#   print (equation.model())
#   equation.add(And((a != equation.model()[a]), (s != equation.model()[s]), (u != equation.model()[u])))
  
  # If i use And(...) it will only produce the single FFF answer given previously.
  # If i use Or(...) it will produce an inifite loop of answers, but each answer will alternatively include
  # s and a, or s and u, never all three in conjunction
  
"""
Bringing in a direct copy of the SO code from:
    https://stackoverflow.com/questions/13395391/z3-finding-all-satisfying-models

"""  

a = Int('a')
b = Int('b')

"""
This part is saying that 1<= a,b <=5, and it wants to give every value which satisfies a >= 2b

The output should be:
[b = 1, a = 2]
[b = 2, a = 4]
[b = 1, a = 3]
[b = 2, a = 5]
[b = 1, a = 4]
[b = 1, a = 5]

and it is.
"""
s = Solver()
s.add(1 <= a)
s.add(a <= 5)
s.add(1 <= b)
s.add(b <= 5)
s.add(a >= 2*b)

# while s.check() == sat:
#   print (s.model())
#   s.add(Or(a != s.model()[a], b != s.model()[b]))
  
# Now let's test the idea with three int variables
c = Int('c')
s3 = Solver()

# Adding constraints
s3.add(1 <= a)
s3.add(1 <= b)
s3.add(1 <= c)

s3.add(a <= 4)
s3.add(b <= 4)
s3.add(c <= 4)

# Adding equation to solve
s3.add(c > a+b)
s3.check()
print (s3.model())
while s3.check() == sat:
  print (s3.model())
  s3.add(Or(a != s3.model()[a], b != s3.model()[b]), c != s3.model()[c])
  
  #Outputs 113, 214, but not 124



