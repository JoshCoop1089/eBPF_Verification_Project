# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 20:23:11 2020

@author: joshc
"""


"""
Going to attempt to transform the logic inside a small portion of check_alu_ops
(line 5849 via https://elixir.bootlin.com/linux/latest/source/kernel/bpf/verifier.c)

Going to start assumption that the input is valid, the source, and dest registers are valid,
    and essentially start inside the else command on line 5960

/* check validity of 32-bit and 64-bit arithmetic operations */
static int check_alu_op(struct bpf_verifier_env *env, struct bpf_insn *insn)
{
    struct bpf_reg_state *regs = cur_regs(env);
	u8 opcode = BPF_OP(insn->code);
	int err;
    if (...) {some stuff i'm not worrying about yet, ie, opcodes that arent bpf_add'}
    else {	/* all other ALU ops: and, sub, xor, add, ... */

		if (BPF_SRC(insn->code) == BPF_X) {
			if (insn->imm != 0 || insn->off != 0) {
				verbose(env, "BPF_ALU uses reserved fields\n");
				return -EINVAL;
			}
			/* check src1 operand */
			err = check_reg_arg(env, insn->src_reg, SRC_OP);
			if (err)
				return err;
		} else {
			if (insn->src_reg != BPF_REG_0 || insn->off != 0) {
				verbose(env, "BPF_ALU uses reserved fields\n");
				return -EINVAL;
			}
		}

		/* check src2 operand */
		err = check_reg_arg(env, insn->dst_reg, SRC_OP);
		if (err)
			return err;

		if ((opcode == BPF_MOD || opcode == BPF_DIV) &&
		    BPF_SRC(insn->code) == BPF_K && insn->imm == 0) {
			verbose(env, "div by zero\n");
			return -EINVAL;
		}

		if ((opcode == BPF_LSH || opcode == BPF_RSH ||
		     opcode == BPF_ARSH) && BPF_SRC(insn->code) == BPF_K) {
			int size = BPF_CLASS(insn->code) == BPF_ALU64 ? 64 : 32;

			if (insn->imm < 0 || insn->imm >= size) {
				verbose(env, "invalid shift %d\n", insn->imm);
				return -EINVAL;
			}
		}

		/* check dest operand */
		err = check_reg_arg(env, insn->dst_reg, DST_OP_NO_MARK);
		if (err)
			return err;

		return adjust_reg_min_max_vals(env, insn);
"""
from z3 import *

s = Solver()

# a = Int('a')

# s.add(a < 10)
# s.add(a > 1)
# while s.check() == sat:
#     print(s.model())
#     s.add(a != s.model()[a])
    
b, c = Bools("b c")
s.add(Implies(b, c))
# s.add(c == True, b == False)
print(s.check())
count = 1
while count < 5 and s.check() == sat:
    print(s.model())
    count += 1
    s.add(
        # Or(b != s.model()[b], 
           c != s.model()[c])
        # )


#Defining useful variables, registers, and register limits
"""
Where are we getting our values from in the actual program?  Since we're going to assume
     this is a small scale look at a single alu_op command, there would be the register
     stucture which would have a current listing of the values stored, and any predefined
     min/max possibilities for the register, but is that a valid place to extract 
     bounds from (see next note on SSA)
     
     While we can just cheat, and use the s.model()[varname] to extract some defined value
     already present in the model, will we always be able to assume that a bound is
     defined before we need to reference it/change it?
     """

#What logic binds the basic register together?
"""Since we're doing this with the expectation of SSA for our variables,
     is it ok to assume that whenever we need to calculate new bounds on a register,
     they'll always start off as u64_min, u64_max, and such, without any of the
     previously changed bounds?
     
     ie, any time we call a verification/range check, we are able to start from scratch,
     and put in those specific bounds changes without referencing the previous changes
     
     Also, need to define the breaking points in the logic, every time it returns
     -EINVAL or err == 1
    """

    
#What specific subfunctions are we going to have to check first, 
    #before returning check_alu_ops in full?
"""In the above truncated case, we have to check:
    bpf_src(insn -> code)  --> for a specific opcode which leads to logic branching
    check_reg_arg   --> multiple checks to ensure validitiy of input values
    bpf_class(insn -> code)  --> getting size information for shifting (not worrying abou this yet)
    adjust_reg_min_max  --> this is the big one, with a whole bunch of subcalls and changes.
        Looking more at this thursday morning.
    """
#Do we specify a specific solving instance for a subprogram, and then add a true/false
    #to the main program based on some form of passed inputs?