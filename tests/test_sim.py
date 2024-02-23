"""
Test running sims
"""

import fpsim as fp
import sciris as sc
import numpy as np


def test_simple():
    sc.heading('Test simplest possible FPsim run')
    sim = fp.Sim()
    sim.run()
    sim.plot()
    return sim


def test_method_sandbox():

    # Create placeholder people
    ppl = sc.objdict()
    n_agents = 100
    ppl.ti = 0
    ppl.dt = 1/12
    ppl.ti_update = np.zeros(n_agents, dtype=int)
    ppl.age = np.random.random(n_agents)*100
    ppl.parity = np.random.choice(np.arange(6), size=n_agents)
    ppl.contraception = np.random.choice([0, 1], size=n_agents)
    ppl.method = np.random.choice(np.arange(9), size=n_agents)
    ppl.urban = np.random.choice([0, 1], size=n_agents)
    ppl.wealthquintile = np.random.choice(np.arange(10), size=n_agents)
    ppl.edu_attainment = np.random.choice(np.arange(4), size=n_agents)
    ppl.paid_employment = np.random.choice([0, 1], size=n_agents)
    ppl.decision_wages = np.random.choice([0, 1], size=n_agents)
    ppl.decision_health = np.random.choice([0, 1], size=n_agents)
    ppl.sexual_autonomy = np.random.choice([0, 1], size=n_agents)

    # Create method selector
    ms = MethodSelector(contra_use_file='contra_coef.csv', method_choice_file='method_mix.csv')

    inds = np.arange(100)
    prob_use = ms.get_prob_use(ppl, inds)
    uses_contra_bool = ms.get_contra_users(ppl, inds)
    method_used = ms.choose_method(ppl, inds[uses_contra_bool])
    time_on_method = ms.set_time_on_method(ppl, method_used)

    return


def test_methods():
    sc.heading('Test time on method')

    ms = fp.MethodSelector(contra_use_file='contra_coef.csv', method_choice_file='method_mix.csv')
    pars = fp.pars(location='test', seed=1, verbose=1)
    s = fp.Sim(pars, method_selector=ms)
    s.run()

    return s


if __name__ == '__main__':

    # s1 = test_simple()
    sim = test_methods()

    # import pandas as pd
    # df = pd.read_csv('method_mix.csv')
    #
    # dd = dict()
    # for akey in df.age_grp.unique():
    #     dd[akey] = dict()
    #     for pkey in df.parity.unique():
    #         dd[akey][pkey] = dict()
    #         for mkey in df.method.unique():
    #             val = df.loc[(df.age_grp == akey) & (df.parity == pkey) & (df.method == mkey)].percent.values[0]
    #             dd[akey][pkey][mkey] = val
    #
    #
    # if 1:
    #     level1 = 'age_grp'
    #     level2 = 'parity'
    #     method_data = {}
    #     for (age, parity), group in df.groupby([level1, level2]):
    #         if age not in method_data:
    #             method_data[age] = {}
    #         method_data[age][parity] = group.drop(columns=[level1, level2]).to_dict(orient='index')
    #     print(method_data)
    #
    #
