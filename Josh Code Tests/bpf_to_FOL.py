# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 22:29:46 2020

@author: joshc
"""


"""
So we're trying to come up with some way of codifying how a specific bpf program would be valid on all inputs
This means it has to pass bpf_check.
In bpf_check, it has to follow the following logical route:
    The first two instructions return a specific error code (enomem, for out of memory problems)
    1) is the size of bpf_verifier_ops == 0
    2) is there instruction data fed properly into a bpf_insn_aux_data struct
    3) here there be dragons (Lines 10701 - 10743)
        we're just going to assume all this stuff loaded in properly, cause we don't know what it does yet.
    4) Replace_map_fd_with_map_ptr, env->explored_states are going to be assumed to be true
    5) Check_subprogs
        
        




'


"""