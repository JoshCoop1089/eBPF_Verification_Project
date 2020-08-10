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


    #when the sat solver generates tnums we have to ensure it complies with good tnum practices
    def validate(self):
        """
        intended result: every 1-bit of self.range is a 0-bit in self.min

        plan - self.min == self.min & ~self.range

        Should work. If any unknown bits are set to 1, then ~self.range will be a 0, the result after the & will be 0, and the
        two values will not be equivalent. Any known value is a 1 in self.range, so they will be unchanged by the &
        """

        unknownCheck = self.min & ~self.range
        return self.min == unknownCheck
        
    
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

    def tnum_eq(self, other):
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

    #should check whether 'other' is a subset of 'self'
    def tnum_in(self, other):
        """
        if (other.range & ~self.range) is not 0:
            return False

            > Requirement to return True: other.range & ~self.range == 0
            
            > Conceptually: Ensures no overlap between known bits of self and unknown bits of other. This means that every variable
            bit in other is also variable in self.
        
        other.min &= ~self.range

            > Conceptually: If the bit is unknown in self, then it will be 0 in ~self.range. This will result in a 0 after the '&'
            operation for every unknown bit. Known bits in self will be 1 in ~self.range; thus, all bits in other.min at known
            locations will be propagated forward (0 & 1 = 0, 1 & 1 = 1)
        
        return self.min == other.min

            > Requirement to return True: self.min == other.min & ~self.range
            
            > Conceptually: Look at previous step. If the bit is unknown in self.range, it will always be set to 0. This is what
            we require from the tnum.min field. If th bit is known in self.range, it will be set to its value and compared against
            the value in self.min. If there's a discrepancy, then other must contain a known bit which differs from a known bit
            in self.min. This would imply that other is not in self.
        """

        maskOverlap = other.range & ~self.range
        knownBits = other.min & ~self.range

        return And((maskOverlap == 0), (self.min == knownBits))

    

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

#""""
#Alright, the cool test
n1 = tnum(BitVec('n1', 8), BitVecVal(0, 8))
n2 = tnum(BitVec('n2', 8), BitVecVal(0, 8))
n3 = tnum(BitVec('n3', 8), BitVecVal(0, 8))

t1 = tnum(BitVec('tn1_value', 8), BitVec('tn1_mask', 8))
t2 = tnum(BitVec('tn2_value', 8), BitVec('tn2_mask', 8))
t3 = tnum(BitVec('tn3_value', 8), BitVec('tn3_mask', 8))


solver = Solver()

solver.add(n3.tnum_eq(n1.add(n2)))

#"""
solver.add(t1.tnum_in(n1))
solver.add(t2.tnum_in(n2))
solver.add((t3.tnum_in(n3)))
solver.add(t3.tnum_eq(t1.add(t2)))
solver.add(n1.validate())
solver.add(n2.validate())
solver.add(n3.validate())
solver.add(t1.validate())
solver.add(t2.validate())
solver.add(t3.validate())

"""
n1 = 10000011 = 131
n2 = 11111100 = 252
n3 = 01111111 = 127


t1 = 10000011 | 01100000 = 132 | 96
t2 = 11111100 | 00000000 = 252 | 0
t3 = 00011111 | 11100000 =  31 | 224
""


if solver.check() == sat:
   m = solver.model()
   print(m)
