'''
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

    def max(self):
        print(self.min + self.range)

#assumption - high and low are same # of bits
def tnum_range(low, high):
    return tnum(low, high-low)
    

    
    
