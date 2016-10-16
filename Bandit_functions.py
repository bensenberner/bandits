#!/usr/bin/python

# Imports
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

from Bandits import * 
from BayesianBandits import * 
from BayesianContextualBandits import * 

# Bandit execution function
def execute_bandits(K, bandits, R, t_max, plot_colors=False):
    """ Execute a set of bandits for t_max time instants over R realization 
        
        Args:
            bandits: list of bandits to execute
            R: number of realizations to run
            t_max: maximum time for the bandits' execution
            plot_colors: colors to use for plotting each realization (default is False, no plotting)
        Rets:
            returns: array with averaged returns (bandit idx by K by t_max)
            actions: array with averaged actions (bandit idx by K by t_max)
            predictive: array with averaged action predictive density (bandit idx by K by t_max)            
    """
    
    n_bandits=len(bandits)
    
    # Allocate space
    returns=np.zeros((n_bandits, R, bandits[0].K, t_max))
    actions=np.zeros((n_bandits, R, bandits[0].K, t_max))
    predictive=np.zeros((n_bandits, R, bandits[0].K, t_max))

    # Realizations
    for r in np.arange(R):
        
        # Execute each bandit
        for n in np.arange(n_bandits):
            bandits[n].execute(t_max)
            
            if isinstance(bandits[n], OptimalBandit):
                returns[n,r,bandits[n].actions,:]=bandits[n].returns
                actions[n,r,bandits[n].actions,:]=np.ones(t_max)
                predictive[n,r,bandits[n].actions,:]=np.ones(t_max)
            elif isinstance(bandits[n], ProbabilisticBandit):
                returns[n,r,:,:]=bandits[n].returns
                actions[n,r,:,:]=bandits[n].actions
                predictive[n,r,:,:]=bandits[n].returns_expected*np.ones((1,t_max))
            elif isinstance(bandits[n], BayesianBandit):
                returns[n,r,:,:]=bandits[n].returns
                actions[n,r,:,:]=bandits[n].actions
                predictive[n,r,:,:]=bandits[n].actions_predictive_density
            else:
                raise ValueError('Invalid bandit number {} class type={}'.format(n, bandits[n]))            
        
    # Return averages
    return (returns, actions, predictive)

# Bandit plotting function  
def plot_bandits(returns_expected, bandit_returns, bandit_actions, bandit_predictive, colors, labels, t_plot=None, plot_std=True):
    """ Plot results for a set of bandits
        
        Args:
            R: number of realizations executed
            returns_expected: true expected returns
            bandit_returns: bandits' returns
            bandit_actions: bandits' actions
            bandit_predictive: bandits' action predictive density
        Rets:
    """
    # Dimensionalities
    n_bandits, R, K, t_max = bandit_returns.shape

    if t_plot is None:
        t_plot=t_max
        
    # Returns over time
    plt.figure()
    plt.plot(np.arange(t_plot), returns_expected.max()*np.ones(t_plot), 'k', label='Expected')
    for n in np.arange(n_bandits):
        plt.plot(np.arange(t_plot), bandit_returns[n,:,:,0:t_plot].sum(axis=1).mean(axis=0), colors[n], label=labels[n])
        if plot_std:
            plt.fill_between(np.arange(t_plot), bandit_returns[n,:,:,0:t_plot].sum(axis=1).mean(axis=0)-bandit_returns[n,:,:,0:t_plot].sum(axis=1).std(axis=0), bandit_returns[n,:,:,0:t_plot].sum(axis=1).mean(axis=0)+bandit_returns[n,:,:,0:t_plot].sum(axis=1).std(axis=0),alpha=0.5, facecolor=colors[n])
    plt.xlabel('t')
    plt.ylabel(r'$y_t$')
    plt.title('Returns over time')
    plt.xlim([0, t_plot-1])
    legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
    plt.show()

    # Cumulative returns over time
    plt.figure()
    plt.plot(np.arange(t_plot), returns_expected.max()*np.arange(t_plot), 'k', label='Expected')
    for n in np.arange(n_bandits):
        plt.plot(np.arange(t_plot), bandit_returns[n,:,:,0:t_plot].sum(axis=1).cumsum(axis=1).mean(axis=0), colors[n], label=labels[n])
        if plot_std:
            plt.fill_between(np.arange(t_plot), bandit_returns[n,:,:,0:t_plot].sum(axis=1).cumsum(axis=1).mean(axis=0)-bandit_returns[n,:,:,0:t_plot].sum(axis=1).cumsum(axis=1).std(axis=0), bandit_returns[n,:,:,0:t_plot].sum(axis=1).cumsum(axis=1).mean(axis=0)+bandit_returns[n,:,:,0:t_plot].sum(axis=1).cumsum(axis=1).std(axis=0),alpha=0.5, facecolor=colors[n])
    plt.xlabel('t')
    plt.ylabel(r'$\sum_{t=0}^Ty_t$')
    plt.title('Cumulative returns over time')
    plt.xlim([0, t_plot-1])
    legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
    plt.show()

    # Regret over time
    plt.figure()
    for n in np.arange(n_bandits):
        plt.plot(np.arange(t_plot), returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1).mean(axis=0), colors[n], label=labels[n])
        if plot_std:
            plt.fill_between(np.arange(t_plot), (returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1).mean(axis=0))-bandit_returns[n,:,:,0:t_plot].sum(axis=1).std(axis=0), (returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1).mean(axis=0))+bandit_returns[n,:,:,0:t_plot].sum(axis=1).std(axis=0),alpha=0.5, facecolor=colors[n])
    plt.xlabel('t')
    plt.ylabel(r'$l_t=y_t^*-y_t$')
    plt.title('Regret over time')
    plt.xlim([0, t_plot-1])
    legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
    plt.show()

    # Cumulative regret over time
    plt.figure()
    for n in np.arange(n_bandits):
        plt.plot(np.arange(t_plot), (returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1)).cumsum(axis=1).mean(axis=0), colors[n], label=labels[n])
        if plot_std:
            plt.fill_between(np.arange(t_plot), (returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1)).cumsum(axis=1).mean(axis=0)-(returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1)).cumsum(axis=1).std(axis=0), (returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1)).cumsum(axis=1).mean(axis=0)+(returns_expected.max()-bandit_returns[n,:,:,0:t_plot].sum(axis=1)).cumsum(axis=1).std(axis=0),alpha=0.5, facecolor=colors[n])
    plt.xlabel('t')
    plt.ylabel(r'$L_t=\sum_{t=0}^T y_t^*-y_t$')
    plt.title('Cumulative regret over time')
    plt.xlim([0, t_plot-1])
    legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
    plt.show()  

    # Action predictive density probabilities over time: separate plots
    for k in np.arange(0,K):
        plt.figure()
        for n in np.arange(n_bandits):
            plt.plot(np.arange(t_plot), bandit_predictive[n,:,k,0:t_plot].mean(axis=0), colors[n], label=labels[n]+' predictive density')
            if plot_std:
                plt.fill_between(np.arange(t_plot), bandit_predictive[n,:,k,0:t_plot].mean(axis=0)-bandit_predictive[n,:,k,0:t_plot].std(axis=0), bandit_predictive[n,:,k,0:t_plot].mean(axis=0)+bandit_predictive[n,:,k,0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
        plt.ylabel(r'$f(a_{t+1}=a|a_{1:t}, y_{1:t})$')
        plt.xlabel('t')
        plt.title('Averaged Action Predictive density probabilities for arm {}'.format(k))
        plt.xlim([0, t_plot-1])
        legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
        plt.show()
    
    # Action probabilities over time: separate plots
    for k in np.arange(0,K):
        plt.figure()
        for n in np.arange(n_bandits):
            plt.plot(np.arange(t_plot), bandit_actions[n,:,k,0:t_plot].mean(axis=0), colors[n], label=labels[n]+' actions')
            if plot_std:
                plt.fill_between(np.arange(t_plot), bandit_actions[n,:,k,0:t_plot].mean(axis=0)-bandit_actions[n,:,k,0:t_plot].std(axis=0), bandit_actions[n,:,k,0:t_plot].mean(axis=0)+bandit_actions[n,:,k,0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
        plt.ylabel(r'$f(a_{t+1}=a|a_{1:t}, y_{1:t})$')
        plt.xlabel('t')
        plt.title('Averaged Action probabilities for arm {}'.format(k))
        plt.xlim([0, t_plot-1])
        legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
        plt.show()

    # Action probabilities (combined) over time: Subplots
    """
    f, *axes = plt.subplots(K, sharex=True, sharey=True)
    for k in np.arange(0,K):
        for n in np.arange(n_bandits):
            axes[0][k].plot(np.arange(t_plot), bandit_predictive[n,:,k,0:t_plot].mean(axis=0), colors[n], label=labels[n]+' predictive density')
            axes[0][k].plot(np.arange(t_plot), bandit_actions[n,:,k,0:t_plot].mean(axis=0), colors[n]+'-.', label=labels[n]+' actions')
            if plot_std:
                axes[0][k].fill_between(np.arange(t_plot), bandit_predictive[n,:,k,0:t_plot].mean(axis=0)-bandit_predictive[n,:,k,0:t_plot].std(axis=0), bandit_predictive[n,:,k,0:t_plot].mean(axis=0)+bandit_predictive[n,:,k,0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
                axes[0][k].fill_between(np.arange(t_plot), bandit_actions[n,:,k,0:t_plot].mean(axis=0)-bandit_actions[n,:,k,0:t_plot].std(axis=0), bandit_actions[n,:,k,0:t_plot].mean(axis=0)+bandit_actions[n,:,k,0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
    plt.ylabel(r'$f(a_{t+1}=a|a_{1:t}, y_{1:t})$')
    plt.xlabel('t')
    plt.title('Averaged Predictive probabilities')
    plt.axis([0, t_plot-1,0,1])
    legend = plt.legend(loc='upper right', shadow=True)
    plt.show()
    
    # Action probabilities (combined) over time: separate plots
    for k in np.arange(0,K):
        plt.figure()
        for n in np.arange(n_bandits):
            plt.plot(np.arange(t_plot), bandit_predictive[n,:,k,0:t_plot].mean(axis=0), colors[n], label=labels[n]+' predictive density')
            plt.plot(np.arange(t_plot), bandit_actions[n,:,k,0:t_plot].mean(axis=0), colors[n]+'-.', label=labels[n]+' actions')
            if plot_std:
                plt.fill_between(np.arange(t_plot), bandit_predictive[n,:,k,0:t_plot].mean(axis=0)-bandit_predictive[n,:,k,0:t_plot].std(axis=0), bandit_predictive[n,:,k,0:t_plot].mean(axis=0)+bandit_predictive[n,:,k,0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
                plt.fill_between(np.arange(t_plot), bandit_actions[n,:,k,0:t_plot].mean(axis=0)-bandit_actions[n,:,k,0:t_plot].std(axis=0), bandit_actions[n,:,k,0:t_plot].mean(axis=0)+bandit_actions[n,:,k,0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
        plt.ylabel(r'$f(a_{t+1}=a|a_{1:t}, y_{1:t})$')
        plt.xlabel('t')
        plt.title('Averaged Predictive probability for arm {}'.format(k))
        plt.axis([0, t_plot-1,0,1])
        legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
        plt.show()
    """
    	
	# Correct arm selection probability
    plt.figure()
    for n in np.arange(n_bandits):
        plt.plot(np.arange(t_plot), bandit_actions[n,:,returns_expected.argmax(),0:t_plot].mean(axis=0), colors[n], label=labels[n]+' actions')
        if plot_std:
            plt.fill_between(np.arange(t_plot), bandit_actions[n,:,returns_expected.argmax(),0:t_plot].mean(axis=0)-bandit_actions[n,:,returns_expected.argmax(),0:t_plot].std(axis=0), bandit_actions[n,:,returns_expected.argmax(),0:t_plot].mean(axis=0)+bandit_actions[n,:,returns_expected.argmax(),0:t_plot].std(axis=0),alpha=0.5, facecolor=colors[n])
    plt.ylabel(r'$f(a_{t+1}=a^*|a_{1:t}, y_{1:t})$')
    plt.xlabel('t')
    plt.title('Averaged Correct Action probabilities')
    plt.xlim([0, t_plot-1])
    legend = plt.legend(bbox_to_anchor=(0,-0.25), ncol=n_bandits, loc='center', shadow=True)
    plt.show()
	
	
# Making sure the main program is not executed when the module is imported
if __name__ == '__main__':
    main()
