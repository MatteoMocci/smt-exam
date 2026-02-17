from z3 import *

def CountingStrategy(numbers : list[int], target : int):
    # Variables
    OPERATION_IDS = {0: '+', 1: '-', 2: '*', 3: '/'}  # Each possible operation is encoded with an integer value
    ids = [Int(f'id_{i}') for i in range(6)]           # The index of the number used in step i for i in 0...5, step 0 is the first number
    steps = [Bool(f'step_done_{i}') for i in range(6)] # Since we want to minimize the number of steps as well, we keep track if we did a step or not
    ops = [Int(f'op_{i}') for i in range(1,6)]         # The index of the operation used in step i for i in 1...5
    vals = [Int(f'res_{i}') for i in range(6)]         # The partial result in step i for i in 0...5
    dist_to_target = target                            # The difference between the target and the current result
    arr = K(IntSort(), 0)                              # Array of integer numbers to be indexed with Z3 integers
    for i, v in enumerate(numbers):
        arr = Store(arr, i, v)

    opt = Optimize()

    def apply(op_now, val_now, val_next, step, n_used):
        return If(
            step,                                                       
            If(op_now == 0, val_next == val_now + n_used,  # add case

            If(op_now == 1, val_next == val_now - n_used,  # minus case
                
            If(op_now == 2, val_next == val_now * n_used,  # times case
                
            And(n_used != 0, val_now % n_used == 0, val_next == val_now / n_used)))),  # division case, we avoid dividing by 0 and we check divisibility

            val_next == val_now  # We don't apply the operation if we're skipping the step
        )    


    # Constraints
    opt.add(vals[0] == Select(arr, ids[0]))  # The first partial result is the first chosen number
    for id in ids:
        opt.add(And(id >= 0, id < 6))  # The id values should be between 0 and 5
    
    for op in ops:
        opt.add(And(op >= 0, op < 4))  # The op values should be between 0 and 3

    for i in range(len(steps)):
        if i != 0:
            opt.add(Implies(steps[i],steps[i-1]))  # If I'm doing step n, it means I did step n-1
    
    for i in range(6):
        for j in range(i+1,6):
            c1 = And(steps[i],steps[j])  # If I did steps i and j
            c2 = ids[i] != ids[j]        # Then, the id at step i must be different than the id in step j: I can use each number once
            opt.add(Implies(c1, c2))     # Add the implication constraint

    # Transition definition
    for k in range(1,6):
        opt.add(
            If(
                steps[k],  # If you're doing step k
                apply(ops[k-1],vals[k-1],vals[k],True,Select(arr,ids[k])),  # Then apply the chosen operation
                vals[k] == vals[k-1]  # Else, keep the same value
            )
        )
    
    opt.add(steps[0] == True)  # We force an initial number

    # Objectives
    used_count = Sum([If(steps[k], 1, 0) for k in range(6)])  # We want to minimize how many numbers we are using
    dist_to_target = Abs(target - vals[5])                    # We want to minimize the distance between the target and final result
    opt.minimize(dist_to_target)
    opt.minimize(If(dist_to_target == 0 , used_count, 0))     # If you reached the correct number, minimize the number of used numbers

    # Model printing
    if opt.check() == sat:                                                      # When there is a feasible solution
            m = opt.model()
            print(f"Initial number : {m.eval(Select(arr, ids[0])).as_long()}")  # Print the initial number
            for j in range(1, 6):                                               # For each solution step
                if is_true(m.eval(steps[j])):                                   # If we did the step
                    operator = OPERATION_IDS[m.eval(ops[j-1]).as_long()]        # Get the corresponding operation
                    number = m.eval(Select(arr, ids[j])).as_long()              # Get the number we used
                    print(f"Step {j}: operation {operator} with number {number} -> result {m.eval(vals[j]).as_long()}")
                else:
                    break
            print(f"Final number : {m.eval(vals[5]).as_long()}")
            print(f"Distance from goal: {m.eval(dist_to_target).as_long()}")


def CountingStrategyResilient(numbers: list[int], target: int):
    # Variables
    OPERATION_IDS = {0: '+', 1: '-', 2: '*', 3: '/'}  # Each possible operation is encoded with an integer value
    ids = [Int(f'id_{i}') for i in range(6)]           # The index of the number used in step i for i in 0...5, step 0 is the first number
    steps = [Bool(f'step_done_{i}') for i in range(6)] # Since we want to minimize the number of steps as well, we keep track if we did a step or not
    ops = [Int(f'op_{i}') for i in range(1,6)]         # The index of the operation used in step i for i in 1...5
    vals = [Int(f'res_{i}') for i in range(6)]         # The partial result in step i for i in 0...5
    vals_arr = K(IntSort(),0)
    dist_to_target = target                            # The difference between the target and the current result
    arr = K(IntSort(), 0)                              # Array of integer numbers to be indexed with Z3 integers
    last_op = Int('last_op')                           # The last executed operation's index
    ops_arr = K(IntSort(), 0)

    # Populate the arrays (cannot use Z3 integers to index python lists)
    for i, v in enumerate(numbers):
        arr = Store(arr, i, v)
    
    for i in range(6):
        vals_arr = Store(vals_arr, i, vals[i])

    for i in range(5):
        ops_arr = Store(ops_arr, i, ops[i])

    opt = Optimize()

    def apply(op_now, val_now, val_next, step, n_used):
        return If(
            step,                                                       
            If(op_now == 0, val_next == val_now + n_used,  # add case

            If(op_now == 1, val_next == val_now - n_used,  # minus case
                
            If(op_now == 2, val_next == val_now * n_used,  # times case
                
            And(n_used != 0, val_now % n_used == 0, val_next == val_now / n_used)))),  # division case, we avoid dividing by 0 and we check divisibility

            val_next == val_now  # We don't apply the operation if we're skipping the step
        )
        


    # Constraints
    opt.add(vals[0] == Select(arr, ids[0]))  # The first partial result is the first chosen number
    for id in ids:
        opt.add(And(id >= 0, id < 6))  # The id values should be between 0 and 5
    
    for op in ops:
        opt.add(And(op >= 0, op < 4))  # The op values should be between 0 and 3

    for i in range(len(steps)):
        if i != 0:
            opt.add(Implies(steps[i],steps[i-1]))  # If I'm doing step n, it means I did step n-1
    
    for i in range(6):
        for j in range(i+1,6):
            c1 = And(steps[i],steps[j])  # If I did steps i and j
            c2 = ids[i] != ids[j]        # Then, the id at step i must be different than the id in step j: I can use each number once
            opt.add(Implies(c1, c2))     # Add the implication constraint

    cases = []
    # Transition definition
    for k in range(1,6):
        opt.add(
            If(
                steps[k],  # If you're doing step k
                apply(ops[k-1],vals[k-1],vals[k],True,Select(arr,ids[k])),  # Then apply the chosen operation
                vals[k] == vals[k-1]  # Else, keep the same value
            )
        )

        tail = BoolVal(True) if k == 5 else Not(steps[k+1])
        cases.append(And(last_op == k, steps[k], tail)) 
        # For each turn, these things must be true:
        # 1) The last_operation is equal to k
        # 2) Step k is executed, (doesn't mean it's the last operation)
        # 3) If k < 5, next step is not executed, when k == 5, there is no next step
    
    opt.add(Or(cases))  # The last operation is exactly the last executed step
    
    opt.add(steps[0] == True)                # We force an initial number
    opt.add(steps[1] == True)                # We force to execute one operation (execute step 1)
    opt.add(And(last_op >= 1, last_op <= 5)) # The last operation has an index between 1 and 5

    # Objectives
    used_count = Sum([If(steps[k], 1, 0) for k in range(6)])  # We want to minimize how many numbers we are using
    dist_to_target = Abs(target - vals[5])
    pre_last_val = Select(vals_arr, last_op-1)                      # Take the partial result before the last operation
    last_op_code = Select(ops_arr, last_op-1)                       # Take the operator of the last operation
    att_results = []
    att_dists = []
    for attack in range(1,11):
        result = Int(f"att_res_{attack}")
        legal_attack = Or(last_op_code != 3, pre_last_val % attack == 0)
        # In division case, we exclude the "illegal" attacks where there is no divisibility between the numbers
        opt.add(Implies(legal_attack,apply(last_op_code, pre_last_val, result, True, IntVal(attack))))
        # If the attack is legal, apply it
        
        dist_a = Int(f"att_dist_{attack}")
        opt.add(dist_a == If(legal_attack, Abs(target-result), IntVal(-1)))
        # Add the distance only if it's a legal attack

        att_results.append(result)
        att_dists.append((dist_a, legal_attack))

    worst_dist = Int("worst_dist")
    for d, _ in att_dists:
        opt.add(worst_dist >= d)
    opt.add(Or([And(legal, worst_dist == d) for d, legal in att_dists]))
    # worst_dist is the maximum distance among legal attacks (illegal = -1)

    opt.minimize(worst_dist)
    opt.minimize(If(worst_dist == 0, used_count, 0))


    # Model printing
    if opt.check() == sat:
            m = opt.model()
            print(f"Initial number : {m.eval(Select(arr, ids[0])).as_long()}")
            for j in range(1, 6):
                if is_true(m.eval(steps[j])):
                    operator = OPERATION_IDS[m.eval(ops[j-1]).as_long()]
                    number = m.eval(Select(arr, ids[j])).as_long()
                    print(f"Step {j}: operation {operator} with number {number} -> result {m.eval(vals[j]).as_long()}")
                else:
                    break
            print(f"Final number : {m.eval(vals[5]).as_long()}")
            print(f"Distance from goal: {m.eval(dist_to_target).as_long()}")
            print(f"Distance from goal after attack: {m.eval(worst_dist).as_long()}")

if __name__ == '__main__':
    cool_example = False
    CountingStrategy([1, 3, 5, 8, 10, 50], 462)
    CountingStrategyResilient([1, 3, 5, 8, 10, 50], 462)
    if cool_example:
        CountingStrategy([25,50,75,100,3,6],952) 
        # It works also with this particular instance, known as one of the most amazing solves in Numbers Game from UK Countdown
        # -> https://www.youtube.com/watch?v=pfa3MHLLSWI
        #         
