'''
@author: Sammy Berger

Short for 'tracked number' or 'tristate number'

Some bits may be unknown. A tnum keeps track of both known and unknown
bits in a single number, and propagates unknown bits forward to future
tnums in operations.

Will have always have two variables
  lower - the value of the tnum if all unknown bits were 0
  range - the range of the tnum; alternatively, 1 at every unkown bit

Example: 4 bit number, 10_1 where the _ is unknown

min   = 1001 = 9
range = 0010 = 2

This means that lower + range is the maximum bound for tnum (in this case, 11)

This also means if we want to check if a bit is unknown, we can check if that
bit is set to 1 in the range.
'''
from z3 import *

class tnum:

    def __init__(self, m, r):
        self.min = m
        self.range = r

    def lshift(self, i):
        self.min <<= i
        self.range <<= i

    def rshift(self, i):
        self.min >>= i
        self.range >>= i

    def is_const(self):
        return self.range == 0

    def eq_const(self, c):
        return And(self.is_const(), self.min == c)

    def eq_tnum(self, other):
        return And(self.min == other.min, self.range == other.range)

    def add(self, other):
        """
        Add is nontrivial.

        The new minimum is clearly just old minimum + old minimum.

        Figuring out the new range is difficult though. You can't just
        add the two previous ranges; as an example, let's say we're adding
        the following two numbers:

          01_0 -> 0100, 0010 = 4 or 6
        + 00_1 -> 0001, 0010 = 1 or 3
        ------
          ????

        The new number could be 5, 7, or 9. Adding the mins get you to
        5. Adding the ranges gets you 4. So you just add them and done, right?
        Wrong. Adding them gets you 0101 and 0100. This is not a valid representation
        of our number.
        

        """
        ret = tnum(self.min + other.min, self.range + other.range)
        return ret

    

a = 12
t1 = tnum(BitVecVal(5, 4), BitVecVal(0, 1))
t2 = tnum(BitVecVal(7, 4), BitVecVal(0, 1))
t3 = tnum(BitVec('min', 4), BitVec('range', 1))

solve(t3.eq_tnum(t1.add(t2)))
    
    
