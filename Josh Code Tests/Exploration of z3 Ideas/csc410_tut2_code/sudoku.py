from z3 import *
from itertools import combinations


def exactly_one(literals):
    clauses = []
    # TODO
    return clauses


def print_solution(model, lits):
    '''
    Given a model and the variables, print the solution grid.
    '''
    print("TODO")

def solve(grid):
    # All the variables we need: each cell has one of the 9 digits
    lits = []


    # Once we have created all the variables we need for the encoding,
    # we can start producing the encoding, that is, a list of clauses.
    clauses = []

    # Set of contraints #1: a cell has only one value.
    # Forall cells, exactly one of the lits[i][j][k] for k in 0 .. 9 is true.
    for i in range(9):
        for j in range(9):
            clauses += []       # TODO : add the clauses for the constraint.

    # Set of constraints #2: each value is used only once in a row.
    # For each column and each value, only one lits[i][j][k] is true for i = 0..9
    for j in range(9):
        for k in range(9):
            clauses += []       # TODO : add the clauses for the constraint.


    # Set of constraints #3: each value used exactly once in each column:
    for i in range(9):
        for k in range(9):
            clauses += []       # TODO : add the clauses for the constraint.

    # Set of constraints #4: each value used exaclty once in each 3x3 grid.

    for x in range(3):
        for y in range(3):
            for k in range(9):
                clauses += []   # TODO : add the clauses for this constraint.

    # We have encoded all the constraints for a sudoku problem.
    # Now, we also need to add the information that comes from the input grid.
    # For each cell that has a value, we need to add that the corresponding literal is true.
    for i in range(9):
        for j in range(9):
            if grid[i][j] > 0:  # if the value is > 0, there is a value provided in the grid.
                clauses += []   # TODO : add the corresponding literal.

    # Now, create a solver instance, add all the clauses, and check satisfiability
    s = Solver()

    # Adding all clauses: a clause is a disjunction of its literals.
    # Each clause is added to the solver. A call to check() will check that
    # the conjuction of all the clauses added to the solver is satisfiable.
    for clause in clauses:
        s.add(Or(clause))

    if str(s.check()) == 'sat':
        print_solution(s.model(), lits)
    else:
        print("unsat")

# ================================================================================
#  You do not need to modify anything below this line.
# ================================================================================

def well_formed_problem(grid):
    for line in grid:
        if len(line) != 9:
            print("One line has the wrong number of columns.")
            return False
        for cell in line:
            if cell < 0 or cell > 9:
                print("One cell is not in range 0-9.")
                return False
    return (len(grid) == 9)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python sudoku.py INPUT_FILE\n\tHint: test_input contains two valid input files.")
        exit(1)

    _grid = []
    with open(sys.argv[1], 'r') as input_grid:
        # Each line is a line of the sudoku grid. We should have 9 lines of length 9
        for line in input_grid.readlines():
            _grid.append([int(x) for x in line.split(" ")])

        if well_formed_problem(_grid):
            # Call the encoding function on the input.
            solve(_grid)
            exit(0)
        else:
            print("The input file is invalid.")
            print("It should have 9 lines.")
            print("Each line with 9 digits  (number between 0-9) separated by spaces.")
            exit(1)
