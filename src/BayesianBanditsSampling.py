#!/usr/bin/python

# Imports
import numpy as np
import scipy.stats as stats
from collections import defaultdict
import abc
import sys
from Bandits import * 

#TODO: consider arms with different reward functions
#TODO: should we compute and plot expected returns for Bayesian bandits over time?


# Class definitions
class BayesianBanditSampling(abc.ABC,Bandit):
    """Class (Abstract) for Bayesian Bandits with action sampling
    
    These type of bandits pick an action by sampling the next action based on the probability of the action having the highest expected return
        They update the predictive density of each action based on previous rewards and actions via Bayes update rule
        They draw the next action by (dynamically) SAMPLING from the latest predictive action density, then picking most likely option
            the number of samples balances exploration/exploitation
            different alternatives for the number of action samples to use are implemented

    Attributes (besides inherited):
        reward_prior: the assumed prior of the multi-armed bandit's reward function (dictionary)
        reward_posterior: the posterior of the multi-armed bandit's reward function (dictionary)
        actions_predictive_density: predictive density of each action (mean and var in dictionary)
        sampling: sampling strategy for deciding on action
        n_samples: number of samples for action decision at each time instant
    """
    
    def __init__(self, K, reward_function, reward_prior, sampling):
        """ Initialize Bayesian Bandits with public attributes
        
        Args:
            K: size of the multi-armed bandit 
            reward_function: the reward function of the multi-armed bandit
            reward_prior: the assumed prior for the reward function of the multi-armed bandit (dictionary)
            sampling: sampling strategy for deciding on action
        """
        
        # Initialize bandit (without parameters)
        super().__init__(K, reward_function)
        
        # Reward prior (dictionary)
        self.reward_prior=reward_prior
        
        # Initialize reward posterior (dictonary)
            # TODO: Rethink dictionary list structure
        self.reward_posterior=defaultdict(list)
        for key, val in self.reward_prior.items():
            if key == 'name':
                self.reward_posterior['dist']=reward_prior['dist']
            else:
                self.reward_posterior[key].append(val)
                
        # sampling strategy
        self.sampling=sampling
    
    @abc.abstractmethod
    def compute_action_predictive_density(self, t):
        """ Compute the predictive density of each action based on rewards and actions up until time t
            This is an abstract method, as different alternatives are considered on how to compute this density
        
        Args:
            t: time of the execution of the bandit
        """
           
    def update_reward_posterior(self, t):
        """ Update the posterior of the reward density, based on rewards and actions up until time t
            This function is fully dependent on the type of prior and reward function
            
        Args:
            t: time of the execution of the bandit
        """
        
        # Binomial/Bernoulli reward with beta conjugate prior
        if self.reward_function['dist'].name == 'bernoulli' and self.reward_prior['dist'].name == 'beta':
            # Number of successes up to t (included)        
            s_t=self.returns[:,:t+1].sum(axis=1, keepdims=True)
            # Number of trials up to t (included)
            n_t=self.actions[:,:t+1].sum(axis=1, keepdims=True)
            self.reward_posterior['alpha'].append(self.reward_prior['alpha']+s_t)
            self.reward_posterior['beta'].append(self.reward_prior['beta']+(n_t-s_t))

        # TODO: Add other reward/prior combinations
        else:
            raise ValueError('Invalid reward_function={} with reward_prior={} combination'.format(self.reward_function['dist'].name, self.reward_prior['dist'].name))
        
    def execute(self, t_max):
        """ Execute the Bayesian bandit """
        
        # Initialize
        self.actions_predictive_density={'mean':np.zeros((self.K,t_max)), 'var':np.zeros((self.K,t_max))}
        self.actions=np.zeros((self.K,t_max))
        self.returns=np.zeros((self.K,t_max))
        self.returns_expected=np.zeros((self.K,t_max))
        self.n_samples=np.ones(t_max)
        
                
        # Execute the bandit for each time instant
        for t in np.arange(0,t_max):            
            # Compute predictive density for expected returns at this time instant
            self.compute_action_predictive_density(t)

            # Draw action from predictive density at this time instant
            # Compute number of samples, based on sampling strategy
            if self.sampling['type'] == 'static':
                # Static number of samples
                self.n_samples[t]=self.sampling['n_samples']
            elif self.sampling['type'] == 'linear':
                # Linear number of samples: n_t=n * t +n_0 and enforce at least 1 sample
                self.n_samples[t]=np.maximum(self.sampling['n_0']+self.sampling['n']*t,1)
            elif self.sampling['type'] == 'logT':
                # Logarithmic number of samples: n_t=log(t) and enforce at least 1 sample
                self.n_samples[t]=np.maximum(np.log(t),1)
            elif self.sampling['type'] == 'sqrtT':
                # Square root number of samples: n_t=sqrt(t) and enforce at least 1 sample
                self.n_samples[t]=np.maximum(np.sqrt(t),1)
            elif self.sampling['type'] == 'invVar':
                # Inverse of uncertainty in picked action, and enforce at least 1 sample
                self.n_samples[t]=np.minimum(np.maximum(1/self.actions_predictive_density['var'][self.actions_predictive_density['mean'][:,t].argmax(),t],1), self.sampling['n_max'])
            elif self.sampling['type'] == 'invPFA':
                # Inverse of probability of false alarm, and enforce at least 1 sample
                self.n_samples[t]=np.minimum(np.maximum(1/(1-self.actions_predictive_density['mean'][self.actions_predictive_density['mean'][:,t].argmax(),t]),1), self.sampling['n_max'])
            elif self.sampling['type'] == 'argMax':
                # Infinite samples are equivalent to picking maximum
                self.n_samples[t]=np.inf
            else:
                raise ValueError('Invalid sampling type={}'.format(self.sampling['type']))
            
            # Pick next action
            if self.n_samples[t] == np.inf:
                # Pick maximum 
                action = self.actions_predictive_density[:,t].argmax()
                self.actions[action,t]=1.
            else:
                # SAMPLE n_samples and pick the most likely action                
                self.actions[np.random.multinomial(1,self.actions_predictive_density['mean'][:,t], size=int(self.n_samples[t])).sum(axis=0).argmax(),t]=1
                action = np.where(self.actions[:,t]==1)[0][0]

            # Compute return for true reward function
            self.returns[action,t]=self.reward_function['dist'].rvs(*self.reward_function['args'], **self.reward_function['kwargs'])[action]

            # Update parameter posteriors
            self.update_reward_posterior(t)

class BayesianBanditSamplingMonteCarlo(BayesianBanditSampling):
    """Class for Bayesian Bandits with action sampling that compute the actions predictive density via Monte Carlo sampling
    
        These class updates the predictive density of each action using Monte Carlo sampling, based on previous rewards and actions

    Attributes (besides inherited):
        M: number of samples to use in the Monte Carlo integration
    """
    
    def __init__(self, K, reward_function, reward_prior, n_samples, M):
        """ Initialize Bayesian Bandits with public attributes 
        
        Args:
            K: size of the multi-armed bandit 
            reward_function: the reward function of the multi-armed bandit
            reward_prior: the assumed prior for the reward function of the multi-armed bandit (dictionary)
            M: number of samples to use in the Monte Carlo integration
        """
        
        # Initialize bandit (without parameters)
        super().__init__(K, reward_function, reward_prior, n_samples)
    
        # Monte carlo samples
        self.M=M
        
    def compute_action_predictive_density(self, t):
        """ Compute the predictive density of each action using Monte Carlo sampling, based on rewards and actions up until time t
            Overrides abstract method
        
        Args:
            t: time of the execution of the bandit
        """
        
        # Get posterior hyperparameters
        if self.reward_prior['dist'].name == 'beta':
            posterior_hyperparams=(self.reward_posterior['alpha'][-1], self.reward_posterior['beta'][-1])
        else:
            raise ValueError('reward_prior={} not implemented yet'.format(self.reward_prior['dist'].name))
        
        # Sample reward's parameters, given updated hyperparameters
        reward_params_samples=self.reward_posterior['dist'][0].rvs(*posterior_hyperparams, size=(self.K,self.M))
           
        # Compute expected returns, using updated parameters
        if self.reward_function['dist'].name == 'bernoulli':                   
            # Compute expected rewards, from Bernoulli with sampled parameters
            returns_expected_samples=reward_params_samples
        else:
            # In general,
            returns_expected_samples=self.reward_function['dist'].mean(reward_params_samples)
        
        self.returns_expected[:,t]=returns_expected_samples.mean(axis=1)
        
        # Monte Carlo integration for action predictive density
        # Mean times expected reward is maximum
        self.actions_predictive_density['mean'][:,t]=((returns_expected_samples.argmax(axis=0)[None,:]==np.arange(self.K)[:,None]).astype(int)).mean(axis=1)
        # Variance of times expected reward is maximum
        self.actions_predictive_density['var'][:,t]=((returns_expected_samples.argmax(axis=0)[None,:]==np.arange(self.K)[:,None]).astype(int)).var(axis=1)
        
# Making sure the main program is not executed when the module is imported
if __name__ == '__main__':
    main()