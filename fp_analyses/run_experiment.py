'''
File to extract outputs to calibration from model and compare to data -- renamed to experiment
'''

import sciris as sc
import fpsim as fp
import senegal_parameters as sp

sc.tic()

'''
CALIBRATION TARGETS:
'''
# ALWAYS ON - Information for scoring needs to be extracted from DataFrame with cols 'Age', 'Parity', 'Currently pregnant'
# Dict key: 'pregnancy_parity'
# Overall age distribution and/or percent of population in each age bin
# Age distribution of agents currently pregnant
# Age distribution of agents in each parity group (can be used to make box plot)
# Percent of reproductive age female population in each parity group
# 'pop_years' = Whole years model has run for comparison to population years
# 'tfr_years' = Whole years TFR was recorded in both the model and the data

flags = sc.objdict(
    popsize = 1,  # Population size and growth over time on whole years, adjusted for n number of agents; 'pop_size'
    skyscrapers = 1, # Population distribution of agents in each age/parity bin (skyscraper plot); 'skyscrapers'
    first_birth = 1,  # Age at first birth mean with standard deviation; 'age_first_birth'
    birth_space = 1,  # Birth spacing both in bins and mean with standard deviation; 'spacing'
    age_pregnancy = 1, # Summary stats (mean, std, 25, 50, 75%) ages of those currently pregnant; 'age_pregnant_stats',
        # Summmary stats (mean, std, 25, 50, 75%) ages at each parity; 'age_parity_stats'
    mcpr = 1,  # Modern contraceptive prevalence; 'mcpr'
    methods = 1, # Overall percentage of method use and method use among users; 'methods'
    mmr = 1,  # Maternal mortality ratio at end of sim in model vs data; 'maternal_mortality_ratio'
    infant_m = 1,  # Infant mortality rate at end of sim in model vs data; 'infant_mortality_rate'
    cdr = 1,  # Crude death rate at end of sim in model vs data; 'crude_death_rate'
    cbr = 1,  # Crude birth rate (per 1000 inhabitants); 'crude_birth_rate'
    tfr = 0,  # Not using as calibration target given different formulas in data vs model
)

do_save = True # Whether to save the completed calibration


pars = sp.make_pars()
exp = fp.Experiment(pars=pars, flags=flags)
exp.run()

if do_save:
    sc.saveobj('senegal_experiment.obj', exp)

sc.toc()

print('Done.')
