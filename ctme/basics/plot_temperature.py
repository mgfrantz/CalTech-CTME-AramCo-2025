"""
This module provides functions to visualize the effect of the temperature parameter on the softmax probability distribution.

Functions:
    softmax_with_temperature(probs, temperature):
        Applies the softmax function with a temperature parameter to a probability distribution.
    temperature_plot_distribution(probs, temperature):
        Plots the adjusted probability distribution for a given temperature.
"""

import numpy as np
import matplotlib.pyplot as plt

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Softmax function with temperature parameter
def softmax_with_temperature(probs, temperature):
    """
    Applies the softmax function with a temperature parameter to a probability distribution.

    Args:
        probs (np.ndarray): Array of original probabilities (should sum to 1).
        temperature (float): Temperature parameter (>0). Lower values make the distribution sharper, higher values make it flatter.

    Returns:
        np.ndarray: Adjusted probability distribution after applying temperature.
    """
    # Take the log of the probabilities, divide by temperature, exponentiate, and normalize
    exp_probs = np.exp(np.log(probs) / temperature)
    return exp_probs / np.sum(exp_probs)

# Plot the distribution with numbers on top of each bar
def temperature_plot_distribution(probs: np.ndarray, temperature: float):
    """
    Plots the probability distribution after applying softmax with temperature.

    Args:
        probs (np.ndarray): Array of original probabilities.
        temperature (float): Temperature parameter for softmax.
    """
    # Adjust the probabilities using the softmax with temperature
    adjusted_probs = softmax_with_temperature(probs, temperature)
    plt.figure(figsize=(6, 4))
    # Plot bars for each category
    bars = plt.bar(range(len(probs)), adjusted_probs, tick_label=list(ALPHABET[:len(probs)]))
    plt.ylim(0, 1)
    plt.title(f'Softmax with Temperature = {temperature:.2f}')
    plt.ylabel('Probability')
    plt.xlabel('Categories')

    # Add numbers on top of each bar for clarity
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:.2f}', ha='center', va='bottom')

    plt.show()