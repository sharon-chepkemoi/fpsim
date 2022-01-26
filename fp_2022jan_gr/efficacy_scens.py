'''
Run efficacy scenarios for the GR
'''

import numpy as np
import pandas as pd
import sciris as sc
import fpsim as fp
import fp_analyses as fa

# Define basic things here
default_pars = fa.senegal_parameters.make_pars()
method_names = default_pars['methods']['names']
age_keys = list(default_pars['methods']['probs_matrix'].keys())


def key2ind(sim, key):
    ''' Take a method key and convert to an int, e.g. 'Condoms' → 7 '''
    ind = key
    if ind in [None, 'all']:
        ind = slice(None) # This is equivalent to ":" in matrix[:,:]
    elif isinstance(ind, str):
        ind = sim.pars['methods']['map'][key]
    return ind


class update_methods(fp.Intervention):
    ''' Intervention to modify method efficacy and/or switching matrix '''

    def __init__(self, year, scen):
        super().__init__()
        self.year = year
        self.scen = scen

    def apply(self, sim, verbose=True):

        if sim.y >= self.year and not(hasattr(sim, 'modified')):
            sim.modified = True

            # Implement efficacy
            if 'eff' in self.scen:
                for k,v in self.scen.eff.items():
                    ind = key2ind(sim, k)
                    orig = sim.pars['method_efficacy'][ind]
                    sim.pars['method_efficacy'][ind] = v
                    if verbose:
                        print(f'At time {sim.y:0.1f}, efficacy for method {k} was changed from {orig:0.3f} to {v:0.3f}')

            # Implement method mix shift
            if 'probs' in self.scen:
                for entry in self.scen.probs:
                    source = key2ind(sim, entry['source'])
                    dest   = key2ind(sim, entry['dest'])
                    factor = entry.pop('factor', None)
                    value  = entry.pop('value', None)
                    keys   = entry.pop('keys', None)
                    if keys is None:
                        keys = age_keys

                    for k in keys:
                        matrix = sim.pars['methods']['probs_matrix'][k]
                        orig = matrix[source, dest]
                        if factor is not None:
                            matrix[source, dest] *= factor
                        elif value is not None:
                            matrix[source, dest] = value
                        if verbose:
                            print(f'At time {sim.y:0.1f}, matrix for age group {k} was changed from:\n{orig}\nto\n{matrix[source, dest]}')


        return

def make_sim(label='<no label>', **kwargs):
    ''' Create a single sim, with a label and updated parameters '''
    pars = fa.senegal_parameters.make_pars()
    pars.update(kwargs)
    sim = fp.Sim(pars=pars, label=label)
    return sim


def make_sims(repeats=5, **kwargs):
    ''' Create a list of sims that are all identical except for the random seed '''
    sims = sc.autolist()
    for i in range(repeats):
        kwargs.setdefault('seed', 0)
        kwargs['seed'] += i
        sims += make_sim(**kwargs)
    return sims


def run_sims(*args):
    ''' Actually run a list of sims '''
    msims = sc.autolist()
    for sims in args:
        msims += fp.MultiSim(sims)
    msim = fp.MultiSim.merge(*msims)
    msim.run()
    return msim


def analyze_sims(msim, start_year=2010, end_year=2020):
    ''' Take a list of sims that have different labels and count the births in each '''

    def count_births(sim):
        year = sim.results['t']
        births = sim.results['births']
        inds = sc.findinds((year >= start_year), year < end_year)
        output = births[inds].sum()
        return output

    def method_failure(sim):
        year = sim.results['tfr_years']
        meth_fail = sim.results['method_failures_over_year']
        inds = sc.findinds((year >= start_year), year < end_year)
        output = meth_fail[inds].sum()
        return output

    def count_pop(sim):
        year = sim.results['tfr_years']
        popsize = sim.results['pop_size']
        inds = sc.findinds((year >= start_year), year < end_year)
        output = popsize[inds].sum()
        return output
    
    def mean_tfr(sim):
        year = sim.results['tfr_years']
        rates = sim.results['tfr_rates']
        inds = sc.findinds((year >= start_year), year < end_year)
        output = rates[inds].mean()
        return output

    # Split the sims up by scenario
    results = sc.objdict()
    results.sims = sc.objdict(defaultdict=sc.autolist)
    for sim in msim.sims:
        results.sims[sim.label] += sim

    # Count the births across the scenarios
    raw = sc.objdict(defaultdict=sc.autolist)
    for key,sims in results.sims.items():
        for sim in sims:
            n_births = count_births(sim)
            n_fails  = method_failure(sim)
            n_pop = count_pop(sim)
            n_tfr = mean_tfr(sim)
            raw.scenario += key      # Append scenario key
            raw.births   += n_births # Append births
            raw.fails    += n_fails  # Append failures
            raw.popsize  += n_pop    # Append population size
            raw.tfr      += n_tfr    # Append mean tfr rates

    # Calculate basic stats
    results.stats = sc.objdict()
    for statkey in ['mean', 'median', 'std', 'min', 'max']:
        results.stats[statkey] = sc.objdict()
        for k,vals in raw.items():
            if k != 'scenario':
                results.stats[statkey][k] = getattr(np, statkey)(vals)

    # Also save as pandas
    results.df = pd.DataFrame(raw)

    return results



if __name__ == '__main__':

    debug   = False # Set population size and duration
    one_sim = False # Just run one sim

    #%% Define sim parameters
    scen_year = 2005 # Year to start the different scenarios
    if not debug:
        pars = dict(
            n          = 100_000,
            start_year = 1980,
            end_year   = 2030,
        )
        repeats   = 10 # How many duplicates of each sim to run
    else:
        pars = dict(
            n          = 1_000,
            start_year = 2000,
            end_year   = 2010,
        )
        repeats = 3

    #%% Define scenarios

    # Increased efficacy
    eff_scen = sc.objdict(
        eff={method:0.994 for method in method_names if method != 'None'} # Set all efficacies to 1.0 except for None
    )
    eff = update_methods(scen_year, eff_scen) # Create intervention

    # Increased uptake high efficacy
    uptake_scen = sc.objdict(
        eff = {'Other modern':0.994}, # Co-opt an unused method and simulate a medium-efficacy method
        probs = [
            dict(
                source = 'None', # Source method, 'all' for all methods
                dest   = 'Other modern', # Destination
                factor = None, # Factor by which to multiply existing probability
                value  = 0.2, # Alternatively, specify the absolute probability of switching to this method
                keys   = ['>25'], # Which age keys to modify -- if not specified, all
            ),
        ]
    )
    uptake = update_methods(scen_year, uptake_scen) # Create intervention
    
    
    # Increased uptake moderate efficacy
    uptake_scen_mod = sc.objdict(
        eff = {'Other modern':0.93}, # Co-opt an unused method and simulate a medium-efficacy method
        probs = [
            dict(
                source = 'None', # Source method, 'all' for all methods
                dest   = 'Other modern', # Destination
                factor = None, # Factor by which to multiply existing probability
                value  = 0.2, # Alternatively, specify the absolute probability of switching to this method
                keys   = ['>25'], # Which age keys to modify -- if not specified, all
            ),
        ]
    )
    uptake_mod = update_methods(scen_year, uptake_scen_mod) # Create intervention    
    
    
    # Increased uptake low efficacy
    uptake_scen_low = sc.objdict(
        eff = {'Other modern':0.86}, # Co-opt an unused method and simulate a medium-efficacy method
        probs = [
            dict(
                source = 'None', # Source method, 'all' for all methods
                dest   = 'Other modern', # Destination
                factor = None, # Factor by which to multiply existing probability
                value  = 0.2, # Alternatively, specify the absolute probability of switching to this method
                keys   = ['>25'], # Which age keys to modify -- if not specified, all
            ),
        ]
    )
    uptake_low = update_methods(scen_year, uptake_scen_low) # Create intervention
    

        # Increased uptake low efficacy
    uptake_scen_25 = sc.objdict(
        eff = {'Other modern':0.86}, # Co-opt an unused method and simulate a medium-efficacy method
        probs = [
            dict(
                source = 'None', # Source method, 'all' for all methods
                dest   = 'Other modern', # Destination
                factor = None, # Factor by which to multiply existing probability
                value  = 0.2, # Alternatively, specify the absolute probability of switching to this method
                keys   = ['>25'], # Which age keys to modify -- if not specified, all
            ),
        ]
    )
    uptake_25 = update_methods(scen_year, uptake_scen_25) # Create intervention
    
            # Increased uptake low efficacy
    uptake_scen_20 = sc.objdict(
        eff = {'Other modern':0.86}, # Co-opt an unused method and simulate a medium-efficacy method
        probs = [
            dict(
                source = 'None', # Source method, 'all' for all methods
                dest   = 'Other modern', # Destination
                factor = None, # Factor by which to multiply existing probability
                value  = 0.2, # Alternatively, specify the absolute probability of switching to this method
                keys   = ['<18','18-20'], # Which age keys to modify -- if not specified, all
            ),
        ]
    )
    uptake_20 = update_methods(scen_year, uptake_scen_20) # Create intervention



    #%% Create sims
    sims1 = make_sims(repeats=repeats, label='Baseline', **pars)
    # sims2 = make_sims(repeats=repeats, interventions=eff, label='Increased efficacy', **pars)
    # sims3 = make_sims(repeats=repeats, interventions=uptake, label='Increased uptake, high eff', **pars)
    # sims4 = make_sims(repeats=repeats, interventions=uptake_mod, label='Increased uptake, mod eff', **pars)
    # sims5 = make_sims(repeats=repeats, interventions=uptake_low, label='Increased uptake, low eff', **pars)
    sims6 = make_sims(repeats=repeats, interventions=uptake_25, label='Increased uptake over age 25', **pars)
    sims7 = make_sims(repeats=repeats, interventions=uptake_20, label='Increased uptake under age 21', **pars)


    #%% Run
    if one_sim:
        sim = sims1[4]
        sim.run()
        sim.plot()

    else:
        msim = run_sims(sims1, 
                        # sims2, 
                        # sims3, 
                        # sims4, 
                        # sims5,
                        sims6,
                        sims7)


    #%% Plotting
    msim2 = msim.remerge()
    msim.plot(plot_sims=False) # This plots all 15 individual sims as lines of 3 colors
    msim2.plot(plot_sims=True) # This plots 3 multisims with uncertainty bands in the same 3 colors


        # Analyze
    results = analyze_sims(msim)
    print(results.df)
    # print(results.stats)
    print('Done.')

