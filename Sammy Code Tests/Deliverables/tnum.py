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

#throughout the project we will assume every bitvector is of this length
bitLength = 8

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

    #If erroring, look at the hma subfunction first
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

    

#current error - type mismatch stuff
"""
half-multiply, apparently a static intermediate step to multiply

Idea: While the mask is nonzero (it has at least one 1), check the rightmost bit. If it's a 1, then add the value to the accumulator.
        Then, rightshift the mask (move one bit further in) and leftshift the value (you're working with the 2^n+1 bit, so multiply
        your value by 2)

original code:

static struct tnum hma(struct tnum acc, u64 value, u64 mask)
    while (mask) {
        if (mask & 1)
            acc = tnum_add(acc, TNUM(0, value));
        mask >>= 1;
        value <<= 1;
    }
    return acc;

our code:

hma(a, v, m):
    for i from 1 -> bitlength:
        if mask[i] == 1
            accumulate()
        value <<= 1
    return acc

Note - Objects persist across python methods, as they would in Java.
        This means that we have to copy the values into a new object
        before editing/using them.
"""

#acc: tnum
#value: BitVec
#mask: BitVec
def hma(acc, value, mask):
    
    for i in range(0, bitLength):
        bit = z3.Extract(i, i, mask)

        if(bit == BitVecVal(0, 1)):
            acc = tnum_add(acc, tnum(0, value))

        value <<= 1

    return acc
    
    
#             #
#             #
# Tests below #
#             #
#             #

solver = Solver()

n1 = tnum(BitVecVal(4, bitLength), BitVecVal(0, bitLength))
n2 = tnum(BitVecVal(2, bitLength), BitVecVal(0, bitLength))
n3 = tnum(BitVec("n3_value", bitLength), BitVec("n3_range", bitLength))

solver.add(n3.tnum_eq(n1.mult(n2)))
if solver.check() == sat:
   m = solver.model()
   print(m)
