import numpy as np
from numpy import linalg as LA
import sys
sys.path.append('../')
from query import Query, Type
from privacy import PrivacyEngine
from PolicyGraph import PolicyGraph
from privacy.func.LM_SM import lm_sm, lm_sm_est_cost


def qw_1(l):
    bin_size = 5000.0 / l
    predicates = []
    for i in range(0, l):
        p = str(i * bin_size) + "<=capgain and capgain<" + str((i + 1) * bin_size)
        predicates.append(p)

    return predicates[:l]

def test_age():
    predicates = []
    for i in range(17, 91, 1):
        predicates.append(str(i) + "<=age and age <" + str((i + 1)))
    return predicates

#predicates = ['age = 1', 'age = 2', 'age = 3', 'age = 4','age = 5', 'age = 6', 'age = 7', 'age = 8', 'age = 9', 'age = 10' ]
#predicates = ['age <= 1', 'age <= 2', 'age <= 3', 'age <= 4','age <= 5', 'age <= 6', 'age <= 7', 'age <= 8', 'age <= 9', 'age <= 10' ]

data_size = 32561

#set up query
crnt_q=Query.Query()
crnt_q.table_name = 'income'
crnt_q.set_index(test_age)
cond_list = test_age()
crnt_q.set_cond_list(cond_list)
crnt_q.set_data_and_size("census", 1)
crnt_q.set_query_type(Type.QueryType.WCQ, -1, 10, -1)
crnt_q.set_mechanism_type(Type.MechanismType.LM_SM)

pe = PrivacyEngine.PrivacyEngine(float('inf'), None)
alpha=0.02*32561
beta=0.0005
crnt_run = pe.run_query(crnt_q, alpha, beta)

table_name = crnt_run.query.table_name
data_size = crnt_run.query.data_size
acc_list = crnt_run.query.get_accuracy()
print("Table {}, size {}".format(table_name, data_size))
print("true_answers via matrix= ", crnt_q.true_answer)
print("query_result_noisy= ", crnt_q.noisy_answer)
print("laplace_noise= ", crnt_q.lap_noise)
print(" {}".format(acc_list))
