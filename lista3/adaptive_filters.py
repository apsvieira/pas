from typing import Optional, List, Union

import numpy as np


def lms(
    signal: Union[List, np.ndarray],
    reference: Union[List, np.ndarray],
    num_parameters: int,
    pace: Optional[float] = None
) -> np.ndarray:
    if pace is None:
        pace = 1 / (num_parameters * np.correlate(signal, signal, 'valid'))

    weights = np.zeros(num_parameters).reshape(-1, 1)
    samples = np.zeros(num_parameters).reshape(-1, 1)
    filtered_signal = np.zeros_like(signal)
    weight_history = []

    for n in range(signal.shape[0]):
        weight_history.append(weights)
        samples = np.roll(samples, 1)
        samples[0] = signal[n]

        estimate = weights.T @ samples
        filtered_signal[n] = estimate

        error = reference[n] - estimate

        weights = weights + pace * samples * error

    return filtered_signal, weight_history


def error_signal_lms(
    signal: Union[List, np.ndarray],
    reference: Union[List, np.ndarray],
    num_parameters: int,
    pace: Optional[float] = None
) -> np.ndarray:
    if pace is None:
        pace = 1 / (num_parameters * np.correlate(signal, signal, 'valid'))

    weights = np.zeros(num_parameters).reshape(-1, 1)
    samples = np.zeros(num_parameters).reshape(-1, 1)
    filtered_signal = np.zeros_like(signal)
    weight_history = []

    for n in range(signal.shape[0]):
        weight_history.append(weights)
        samples = np.roll(samples, 1)
        samples[0] = signal[n]

        estimate = weights.T @ samples
        filtered_signal[n] = estimate

        ref_sample = reference[n]
        if ref_sample > estimate:
            error_signal = 1
        elif ref_sample < estimate:
            error_signal = -1
        else:
            error_signal = 0

        weights = weights + pace * samples * error_signal

    return filtered_signal, weight_history


def rls(
    signal: Union[List, np.ndarray],
    reference: Union[List, np.ndarray],
    num_parameters: int,
    fading: float,
    sigma: float
) -> np.ndarray:
    weights = np.zeros(num_parameters).reshape(-1, 1)
    samples = np.zeros(num_parameters).reshape(-1, 1)
    P = np.eye(num_parameters) / sigma

    filtered_signal = np.zeros_like(signal)
    weight_history = []

    for n in range(signal.shape[0]):
        weight_history.append(weights)

        samples = np.roll(samples, 1)
        samples[0] = signal[n]
        ref_sample = reference[n]

        estimate = weights.T @ samples
        filtered_signal[n] = estimate

        error = ref_sample - estimate
        g = P @ samples / (fading + samples.T @ P @ samples)
        
        P = P / fading - fading * g @ samples.T @ P
        weights = weights + g * error

    return filtered_signal, weight_history
