#!/usr/bin/python

# Imports
import numpy as np
import scipy.stats as stats
import pickle
import sys, os
import argparse
from itertools import *
import pdb
from matplotlib import colors

# Add path and import Bayesian Bandits
sys.path.append('../src')
# Plotting
from plot_Bandits import *
# Optimal Bandit
from OptimalBandit import *
# Sampling
from BayesianBanditSampling import *
from MCBanditSampling import *
# Quantiles
from BayesianBanditQuantiles import *
from MCBanditQuantiles import *

# Main code
def main(A, t_max, M, N_max, R, exec_type, theta):

    ############################### MAIN CONFIG  ############################### 
    print('{}-armed Bernoulli bandit with TS and arm sampling policies with {} MC samples for {} time-instants and {} realizations'.format(A, M, t_max, R))

    # Directory configuration
    dir_string='../results/{}/A={}/t_max={}/R={}/M={}/N_max={}/theta={}'.format(os.path.basename(__file__).split('.')[0], A, t_max, R, M, N_max, '_'.join(str.strip(np.array_str(theta.flatten()),'[]').split()))
    os.makedirs(dir_string, exist_ok=True)
    
    ########## Bernoulli Bandit configuration ##########
    # No context
    context=None    

    # Reward function and prior
    reward_function={'type':'bernoulli', 'dist':stats.bernoulli, 'theta':theta}
    reward_prior={'dist': stats.beta, 'alpha': np.ones((A,1)), 'beta': np.ones((A,1))}
    # MC Sampling
    # MC mininimum sampling uncertainty
    min_sampling_sigma=0.000001
    mc_reward_prior={'dist': stats.beta, 'alpha': np.ones((A,1)), 'beta': np.ones((A,1)), 'sampling':'density', 'sampling_sigma':min_sampling_sigma, 'M':M}
    ############################### BANDITS  ###############################    
    # Bandits to evaluate as a list
    bandits=[]
    bandits_labels=[]
       
    ### Thompson sampling: when sampling with static n=1 and no MC
    thompsonSampling={'sampling_type':'static', 'MC_type':'MC_arms', 'M':1, 'arm_N_samples':1}
    bandits.append(BayesianBanditSampling(A, reward_function, reward_prior, thompsonSampling))
    bandits_labels.append('Thompson Sampling')

    # Monte-Carlo based
    bandits.append(MCBanditSampling(A, reward_function, mc_reward_prior, thompsonSampling))
    bandits_labels.append('MC Thompson Sampling, M_theta={}'.format(mc_reward_prior['M']))
    
    ### Inverse Pfa sampling
    # Truncated Gaussian with log10(1/Pfa), MC over arms with provided M and N_max
    invPfaSampling={'sampling_type':'infPfa', 'Pfa':'tGaussian', 'f(1/Pfa)':np.log10, 'MC_type':'MC_arms', 'M': M, 'N_max':N_max}
    bandits.append(BayesianBanditSampling(A, reward_function, reward_prior, invPfaSampling))
    bandits_labels.append('tGaussian log10(1/Pfa), M_a={}'.format(invPfaSampling['M']))

    # Monte-Carlo based
    bandits.append(MCBanditSampling(A, reward_function, mc_reward_prior, invPfaSampling))
    bandits_labels.append('MC tGaussian log10(1/Pfa), M_a={}, M_theta={}'.format(invPfaSampling['M'], mc_reward_prior['M']))
    
    # Chebyshev with log10(1/Pfa), MC over arms with provided M and N_max
    invPfaSampling={'sampling_type':'infPfa', 'Pfa':'Chebyshev', 'f(1/Pfa)':np.log10, 'MC_type':'MC_arms', 'M': M, 'N_max':N_max}
    bandits.append(BayesianBanditSampling(A, reward_function, reward_prior, invPfaSampling))
    bandits_labels.append('Chebyshev log10(1/Pfa), M_a={}'.format(invPfaSampling['M']))

    # Monte-Carlo based
    bandits.append(MCBanditSampling(A, reward_function, mc_reward_prior, invPfaSampling))
    bandits_labels.append('MC Chebyshev log10(1/Pfa), M_a={}, M_theta={}'.format(invPfaSampling['M'], mc_reward_prior['M']))

    # Markov with log10(1/Pfa), MC over arms with provided M and N_max
    invPfaSampling={'sampling_type':'infPfa', 'Pfa':'Markov', 'f(1/Pfa)':np.log10, 'MC_type':'MC_arms', 'M': M, 'N_max':N_max}
    bandits.append(BayesianBanditSampling(A, reward_function, reward_prior, invPfaSampling))
    bandits_labels.append('Markov log10(1/Pfa), M_a={}'.format(invPfaSampling['M']))

    # Monte-Carlo based
    bandits.append(MCBanditSampling(A, reward_function, mc_reward_prior, invPfaSampling))
    bandits_labels.append('MC Markov log10(1/Pfa), M_a={}, M_theta={}'.format(invPfaSampling['M'], mc_reward_prior['M']))
     
    ### BANDIT EXECUTION
    # Execute each bandit
    for (n,bandit) in enumerate(bandits):
        bandit.execute_realizations(R, t_max, context, exec_type)
    
    # Save bandits info
    with open(dir_string+'/bandits.pickle', 'wb') as f:
        pickle.dump(bandits, f)
    with open(dir_string+'/bandits_labels.pickle', 'wb') as f:
        pickle.dump(bandits_labels, f)

    ############################### PLOTTING  ############################### 
    ## Plotting arrangements
    bandits_colors=[colors.cnames['black'], colors.cnames['silver'], colors.cnames['red'], colors.cnames['salmon'], colors.cnames['navy'], colors.cnames['blue'], colors.cnames['green'], colors.cnames['lime'], colors.cnames['orange'], colors.cnames['yellow'], colors.cnames['cyan'], colors.cnames['lightblue'],  colors.cnames['purple'], colors.cnames['fuchsia'], colors.cnames['saddlebrown'], colors.cnames['peru']]
        
    # Plotting direcotries
    dir_plots=dir_string+'/plots'
    os.makedirs(dir_plots, exist_ok=True)

    # Plotting time: all
    t_plot=t_max
    
    ## GENERAL
    # Plot regret
    plot_std=False
    bandits_plot_regret(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    plot_std=True
    bandits_plot_regret(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)

    # Plot cumregret
    plot_std=False
    bandits_plot_cumregret(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    plot_std=True
    bandits_plot_cumregret(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    
    # Plot rewards expected
    plot_std=True
    bandits_plot_rewards_expected(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    
    # Plot actions
    plot_std=False
    bandits_plot_actions(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    plot_std=True
    bandits_plot_actions(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)

    # Plot correct actions
    plot_std=False
    bandits_plot_actions_correct(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    plot_std=True
    bandits_plot_actions_correct(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    
    ## Sampling bandits
    # Plot action predictive density
    plot_std=True
    bandits_plot_arm_density(bandits, bandits_colors, bandits_labels, t_plot, plot_std, plot_save=dir_plots)
    ###############
            
# Making sure the main program is not executed when the module is imported
if __name__ == '__main__':
    # Input parser
    # Example: python3 -m pdb evaluate_Bernoulli_MCBanditSampling_all.py -A 2 -t_max 10 -M 50 -N_max 20 -R 2 -exec_type sequential -theta 0.2 0.5
    parser = argparse.ArgumentParser(description='Evaluate Bernoulli Bandits and MC: TS and all arm sampling policies.')
    parser.add_argument('-A', type=int, default=2, help='Number of arms of the bandit')
    parser.add_argument('-t_max', type=int, default=10, help='Time-instants to run the bandit')
    parser.add_argument('-M', type=int, default=1000, help='Number of samples for the MC integration')
    parser.add_argument('-N_max', type=int, default=25, help='Maximum number of arm candidate samples')
    parser.add_argument('-R', type=int, default=1, help='Number of realizations to run')
    parser.add_argument('-exec_type', type=str, default='sequential', help='Type of execution to run: batch or sequential')
    parser.add_argument('-theta', nargs='+', type=float, default=None, help='Theta parameters of the Bernoulli distribution')

    # Get arguments
    args = parser.parse_args()
    
    # Make sure A and theta size match
    if args.theta != None:
        assert len(args.theta)==args.A, 'Not enough Bernoulli parameters theta={} provided for A={}'.format(args.theta, args.A)
        theta=np.reshape(args.theta, (args.A))
    else:
        # Random
        theta=np.random.randn(args.A)

    # Call main function
    main(args.A, args.t_max, args.M, args.N_max, args.R, args.exec_type, theta)
