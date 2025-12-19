import numpy as np
import scipy.signal as signal
from src.utils import config

class UltrasoundSim:
    """Handles Pulse Generation and RF Acquisition."""
    def __init__(self, fs, f0, c, pulse_cycles):
        self.fs = fs
        self.f0 = f0
        self.c = c
        self.dt = 1.0/fs
        
        # Transmit Pulse
        t_pulse = np.arange(-2/f0, 2/f0, self.dt)
        sigma = pulse_cycles / (2 * np.pi * f0)
        envelope = np.exp(-t_pulse**2 / (2 * sigma**2))
        self.pulse = envelope * np.cos(2 * np.pi * f0 * t_pulse)

    def acquire_rf_line(self, phantom, angle_deg, t_axis):
        """Generates one RF line for a given angle."""
        theta_rad = np.radians(angle_deg)
        
        # Coordinate Rotation for Distance (Z) Calculation
        z_i = phantom.center_depth + phantom.x * np.cos(theta_rad) + phantom.z_rel * np.sin(theta_rad)
        
        # Lateral Distance for Beam Profile
        lat_x = phantom.x * np.sin(theta_rad) - phantom.z_rel * np.cos(theta_rad)
        r_lat_sq = lat_x**2 + phantom.y**2
        
        # Beam Profile (4mm width)
        beam_width = 0.004
        amp = np.exp(-r_lat_sq / (2 * beam_width**2))
        
        # Delay and Sum
        tau = 2 * z_i / self.c
        delays_idx = (tau * self.fs).astype(int)
        
        # Sparse accumulation
        spike_train = np.zeros_like(t_axis)
        valid = (delays_idx >= 0) & (delays_idx < len(t_axis) - len(self.pulse))
        np.add.at(spike_train, delays_idx[valid], amp[valid])
        
        # Convolve
        rf = signal.convolve(spike_train, self.pulse, mode='full')
        return rf[:len(t_axis)]
