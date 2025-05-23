"""
This module provides functions to visualize the effect of top-p (nucleus) sampling on probability distributions.

Functions:
    top_p_filter(probs, p):
        Applies top-p filtering to a probability distribution, ensuring at least one token is selected.
    top_p_plot_distribution(probs, p):
        Plots the effect of top-p filtering, showing both the original and filtered/normalized distributions.
"""

import numpy as np
import matplotlib.pyplot as plt

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Function to apply top-p filtering with a minimum of one token selected
def top_p_filter(probs, p):
    """
    Applies top-p (nucleus) filtering to a probability distribution.

    Args:
        probs (np.ndarray): Array of original probabilities (should sum to 1).
        p (float): Cumulative probability threshold (0 < p <= 1).

    Returns:
        filtered_probs (np.ndarray): Probabilities of the selected tokens.
        cutoff (int): Number of tokens selected by top-p filtering.
    """
    # Sort probabilities in descending order
    sorted_probs = np.sort(probs)[::-1]
    cumulative_probs = np.cumsum(sorted_probs)

    # Ensure at least one token is selected
    if p < sorted_probs[0]:
        cutoff = 1
    else:
        cutoff = np.argmax(cumulative_probs >= p) + 1

    filtered_probs = sorted_probs[:cutoff]
    return filtered_probs, cutoff

# Plot the distribution with top-p filtering
def top_p_plot_distribution(probs, p):
    """
    Plots the effect of top-p (nucleus) sampling on a probability distribution.

    Args:
        probs (np.ndarray): Array of original probabilities.
        p (float): Cumulative probability threshold for top-p filtering.
    """
    # Apply top-p filtering to get selected probabilities and cutoff
    filtered_probs, cutoff = top_p_filter(probs, p)
    normalized_probs = filtered_probs / np.sum(filtered_probs)  # Normalize the selected probabilities

    # Create two subplots: original and filtered/normalized distributions
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    labels = list(ALPHABET[:len(probs)])

    # Plot 1: Original distribution with top-p filtering
    bars1 = axs[0].bar(range(len(probs)), np.sort(probs)[::-1], tick_label=labels)
    axs[0].set_ylim(0, 1)
    axs[0].set_title(f'Top-p Sampling (p = {p:.2f}) - Original Probabilities')
    axs[0].set_ylabel('Probability')
    axs[0].set_xlabel('Categories')

    # Highlight selected and unselected probabilities
    for i, bar in enumerate(bars1):
        if i >= cutoff:
            bar.set_color('gray')  # Color the bars outside top-p as gray
        else:
            bar.set_color('blue')  # Highlight the selected probabilities

    # Add numbers on top of each bar for original distribution
    for bar in bars1:
        yval = bar.get_height()
        axs[0].text(bar.get_x() + bar.get_width()/2, yval, f'{yval:.2f}', ha='center', va='bottom')

    # Plot 2: Normalized probabilities of the selected tokens
    bars2 = axs[1].bar(range(len(filtered_probs)), normalized_probs, tick_label=labels[:len(filtered_probs)])
    axs[1].set_ylim(0, 1)
    axs[1].set_title(f'Normalized Probabilities of Selected Tokens (p = {p:.2f})')
    axs[1].set_ylabel('Normalized Probability')
    axs[1].set_xlabel('Selected Categories')

    # Add numbers on top of each bar for normalized probabilities
    for bar in bars2:
        yval = bar.get_height()
        axs[1].text(bar.get_x() + bar.get_width()/2, yval, f'{yval:.2f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()