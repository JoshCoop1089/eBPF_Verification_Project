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

    def __str__(self):
        return "<min: " + str(self.min) + ", range: " + str(self.range) + ">"

    def lshift(self, i):
        LShL(self.mini, i)
        LShL(self.range, i)

    def rshift(self, i):
        LShR(self.min, i)
        LShR(self.range, i)

    def is_const(self):
        return self.range == 0

    def eq_const(self, c):
        return And(self.is_const(), self.min == c)

    def eq_tnum(self, other):
        return And(self.min == other.min, self.range == other.range)

    def add(self, other):
        """
        verifier does the following:
            sv = sum of values/mins
            sm = sum of masks/ranges

            sigma (maximal result) = sm + sv
            chi (all carry bits) = bitwise XOR of sigma and sv
            mu (all unknown bits) = bitwise OR of chi and both original masks/ranges
                -> propogates all unknown bits of original masks
                   also accounts for newly generated unknown bits

            final value/min: bitwise AND of sv and mu
            final mask/range: mu
        """
        sm = self.range + other.range
        sv = self.min + other.min

        sigma = self.range + self.min + other.range + other.min
        chi = sigma ^ sv
        mu = chi | self.range | other.range
        
        return tnum(sv & (~mu), mu)

    def sub(self, other):
        dv = self.min - other.min;
        
        alpha = dv + self.range
        beta = dv - other.range
        chi = alpha ^ beta
        mu = chi | self.range | other.range

        return tnum(dv & (~mu), mu)

    #currently not working - see hma method
    def mult(self, other):
        pi = self.min * other.min
        acc = hma(tnum(pi, 0), self.range, other.range | other.min)
        return hma(acc, other.range, self.min)

    def tnum_and(self, other):
        alpha = self.min | self.range
        beta = other.min | other.range
        v = self.min & other.min
        return tnum(v, alpha & beta & ~v)

    def tnum_or(self, other):
        v = self.min | other.min
        mu = self.range | other.range
        return tnum(v, mu & ~v)

    def tnum_xor(self, other):
        v = self.min ^ other.min
        mu = self.range | other.range
        return tnum(v & ~mu, mu)

    def interect(self, other):
        v = self.min | other.min
        mu = self.range & other.range
        return tnum(v & ~mu, mu)

    def tnum_in(self, other):
        if (other.range & ~self.range) is not 0:
            return False
        other.min &= ~self.range
        return self.min == other.min

    

#current error - will infinitely rightshift because the bitvecs check for satisfiability rather than concrete values
"""
half-multiply, apparently a static intermediate step to multiply
"""
def hma(acc, value, mask):
    loops = 0
    while mask != 0:
        if (mask & 1) is not 0:
            acc = acc.add(tnum(0, value))
        mask >>= 1
        value <<= 1
    return acc
    
"""
t1 = tnum(BitVecVal(2, 64), BitVecVal(1, 64))
t2 = tnum(BitVecVal(2, 64), BitVecVal(0, 64))
t3 = tnum(BitVec('min', 64), BitVec('range', 64))

solve(t3.eq_tnum(t1.add(t2)))
solve(t3.eq_tnum(t1.sub(t2)))
"""

#Alright, the cool test
n1 = tnum(BitVec('n1', 8), BitVecVal(0, 8))
n2 = tnum(BitVec('n2', 8), BitVecVal(0, 8))
n3 = tnum(BitVec('n3', 8), BitVecVal(0, 8))

t1 = tnum(BitVec('tn1_value', 8), BitVec('tn1_mask', 8))
t2 = tnum(BitVec('tn2_value', 8), BitVec('tn2_mask', 8))
t3 = tnum(BitVec('tn3_value', 8), BitVec('tn3_mask', 8))

solver = Solver()

solver.add(n3.eq_tnum(n1.add(n2)))

while solver.check() == sat:
  m = solver.model()
  print (m)

    
"""          
s.add(t1.tnum_in(n1))
s.add(t2.tnum_in(n2))
s.add(Not(t3.tnum_in(n3))

s.add(t3.tnum_eq(t1.add(t2)))
"""

#test = tnum(BitVec('val', 64), BitVecVal(0, 64))
#print(t1.tnum_in(t2))
#solve(t3.eq_tnum(t1.mult(t2)))
    
