# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 11:47:47 2020

@author: joshc
"""

  
"""
Bringing in a direct copy of the SO code from:
    https://stackoverflow.com/questions/13395391/z3-finding-all-satisfying-models

"""  
from z3 import *

a = Int('a')
b = Int('b')
test = Bool("test")


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
s.add(test == (a > b + 3))

print("Solving all possible solutions for a >= 2b, with 1 <= a,b <= 5")
while s.check() == sat:
  print (s.model())
  s.add(Or(a != s.model()[a], b != s.model()[b]))
  
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

print("\nSolving all possible solutions for c > a + b, with 1 <= a,b,c <= 4")
# Adding in the Or constraint to disallow use of previous model values
while s3.check() == sat:
  print (s3.model())
  s3.add(Or( a != s3.model()[a], b != s3.model()[b], c != s3.model()[c]))
  
  # Outputs all 4 possibilities correctly
  
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
        
    Code below outputs u = false, a = false, s = false as the answer, which, unsuprisingly,
        is a valid solution to the constraints.  Yay z3!
    
    How to get it to output all possible satisfiable options?
    
    Update1:
        Based on the SO codes, adding in the Or constraint with the negation of the current values
        should allow the model to continue checking other possibilities.
        
        This works for ints, using bounded limits (a <= 5 and such), 
        but for the booleans below it does some weirdness
'''
p, q = Bools('p q')
simple = Solver()
cond = Implies(p, q)
simple.add(cond)

count = 0

print("\nThis should give all three viable solutions to satisfying p => q")
while count < 10 and simple.check() == sat:
  print (simple.model())
  count += 1
  simple.add(Or(p != simple.model()[p], q != simple.model()[q]))


a, s, u = Bools('a s u')
cond1 = Implies(u, Not(a))
cond2 = Implies(a,s)
cond3 = Implies(Not(s), Not(u))
equation = Solver()
equation.add(cond1,cond2,cond3)

# print("\nSolving a possible solutions for the given constraints: \n\t" + 
#       "1) u => ~a \n\t2) a => s \n\t3) ~s => ~u")
# print(equation.check())
# print(equation.model())


# Good ol' StackOverflow with the ideas
print("\nSolving all possible solutions for the given constraints: \n\t" + 
       "1) u => ~a \n\t2) a => s \n\t3) ~s => ~u")
count = 0
      # Since there are 3 inputs, there can be a max of 8 combinations, thus the count limit
      # It's totally not because this code causes an infinite loop of answer possibilities...
while count < 10 and equation.check() == sat:
  print (equation.model())
  count += 1
  equation.add(And(u != equation.model()[u], s != equation.model()[s], a != equation.model()[a]))
  
  # If i use And(...) it will only produce the single FFF answer given previously.
  # If i use Or(...) it will produce an inifite loop of answers, but each answer will alternatively include
  # s and a, or s and u, never all three in conjunction
  
  
  



