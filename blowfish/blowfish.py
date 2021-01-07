from WCQ import WCQ
from collections import defaultdict

import sys
sys.path.append('../')

#define constants
EPS_MAX = 'eps_max'
ACCURACY = 'accuracy'
TRUE_ANSWER = 'true_answer'
NOISY_ANSWER = 'noisy_answer'


from PolicyGraph import PolicyGraph
from conn import DB
import numpy as np
import copy

#Blowfish-private by Laplace Mechanism 
import numpy as np
from numpy import linalg as LA
import scipy.stats as st

class Mechanism:
    def __init__(self):
        self.alpha = None
        self.beta = None
        self.lap_b = None
        self.strategy = None
        self.strategy_sens = None
        self.strategy_pinv = None
        

def bflm(query, m):

    #Compute answers
    PG, domain_hist, W = query.PG.PG, query.x, query.W

    Gx = np.matmul(m.strategy, domain_hist)
    lap_noise = np.random.laplace(0, m.lap_b, len(Gx))
    noisy_Gx = Gx+lap_noise

    WG = np.matmul(W, PG)
    query.noisy_answer = np.matmul(WG, noisy_Gx)
    query.true_answer = np.matmul(W, domain_hist)

    print(f"true answer: {query.true_answer}")
    print(f"noisy_answer: {query.noisy_answer}")

    query.answer_diff = query.noisy_answer-query.true_answer
    #m.set_real_cost(max(abs(q.answer_diff)))

eps_diff = 0.0000001 #0.01
sample_size = 10000

def bflm_est_cost(query, m):
    print("Estimating cost...")
    print(f"Strategy sensitivity {m.strategy_sens}")
    WG = np.matmul(query.W, query.PG.PG)
    norm_temp = LA.norm(WG) 
    print(f"Norn of WG: {norm_temp}")
    eps_max = m.strategy_sens * LA.norm(WG) / (m.alpha * np.sqrt(m.beta / 2.0))
    eps_min = 0

    count = 0
    while (eps_max - eps_min) > eps_diff:
        count += 1
        eps = (eps_max + eps_min) / 2.0
        beta_e_adjust = estimate_beta_mc(eps, m, query)

        if beta_e_adjust < m.beta:
            eps_max = eps
        else:
            eps_min = eps
        print(f"eps_diff: {eps_max - eps_min}")

    print("DEBUG: alpha=", m.alpha, "\tcount=", count, "\teps_max=", eps_max)

    # store cache
    #m.query.eps_cache[sm_key] = eps_max

    return eps_max

def estimate_beta_mc(eps, m, query):
    counter_fail = 0
    alpha = m.alpha
    beta = m.beta

    for _ in range(int(sample_size)):
        lap_noise = np.random.laplace(0, m.strategy_sens / eps, len(m.strategy))
        wap = np.matmul(query.W, m.strategy_pinv)
        max_err = LA.norm(np.matmul(wap, lap_noise), np.inf)
        if max_err > alpha:
            counter_fail = counter_fail + 1

    beta_e = 1.0 * counter_fail / sample_size
    conf_p = beta / 100.0
    zscore = st.norm.ppf(1.0 - conf_p / 2.0)
    delta_beta = zscore * np.sqrt(beta_e * (1.0 - beta_e) / sample_size)
    beta_e_adjust = beta_e + delta_beta + conf_p

    return beta_e_adjust

#Tests
#columns = ['salary', 'age']
#x representation: [(1,1),(1,2),(1,3)...(1,10)...(10,9),(10,10)] 100 entries
#W, each row is a query, W[i]x = Q[i]
#PG, each row is one of the x entries, last row is bot, each column is an edge
#if we directly answer query using W,

def compute_sensitivity(s_matrix, x, edges):
    s_max = 0
    wx = s_matrix @ x
    for u, v in edges:
        x_copy = copy.copy(x)
        # if u, v has an edge then the corresponding entry in x will not be 0
        x_copy[u] += 1
        x_copy[v] -= 1
        wx_1 = s_matrix @ x_copy
        x_copy[u] -= 2
        x_copy[v] += 1
        wx_2 = s_matrix @ x_copy
        sens_1 = np.sum(abs(wx_1 - wx))
        sens_2 = np.sum(abs(wx_2 - wx))
        s_max = max(sens_1, sens_2)
    return s_max

def sensitivity_helper(s_matrix, x, edges): 
    imax = float('-inf')
    x=np.zeros(len(x)) 
    for u,v in edges:
        x[u],x[v] = 1,-1
        res = np.sum(abs(np.matmul(s_matrix,x)))
        if res > imax: imax = res
        x[u],x[v] = 0,0
    return imax


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


#config: policy specification (JSON)
def run_analysis(predicates, columns, config):
    result = {}
    table_name = 'income'
    wcq = WCQ(columns, predicates, table_name)
    db = DB.DB('census')
    wcq.run_query(db)
    

    print("Generating PG...")
    policy = PolicyGraph()
    #TODO currently, each distinct value remains separated, we can organize distinct values into buckets
    bags = {}
    for col in wcq.columns:
        bags[col] = [(val) for val in sorted(wcq.domain_per_column[col])]
    policy.set_domain(config)
    policy.set_vertices(bags)
    policy.construct_PG()
    wcq.PG = policy

    m = Mechanism()
    m.alpha = 0.02*32561# 0.1*1000 
    m.beta = 0.0005
    m.strategy = LA.pinv(wcq.PG.PG)

    print("Computing strategy sensitivity...")
    #inverse(A*PG), for now A=I, consider different A's
    m.strategy_sens = sensitivity_helper(m.strategy, wcq.x, wcq.PG.edges)
    m.strategy_pinv = wcq.PG.PG
    est_cost = bflm_est_cost(wcq, m)
    m.lap_b = m.strategy_sens / est_cost

    print("DEBUG: est_cost=", est_cost, "\tm.strategy_sens=", m.strategy_sens, "\tlaplace_b=", m.strategy_sens / est_cost)
    bflm(wcq, m)
    max_errpr = 1.0 - max([abs(crnt_answer_diff) for crnt_answer_diff in wcq.answer_diff]) / 32561 #self.cardinality
    print(f"Accuracy: {max_errpr}")
    
    result[EPS_MAX] = est_cost
    result[ACCURACY] = max_errpr
    result[TRUE_ANSWER] = list(wcq.true_answer)
    result[NOISY_ANSWER] = list(wcq.noisy_answer)

    return result



