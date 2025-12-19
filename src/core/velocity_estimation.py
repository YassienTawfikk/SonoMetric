import numpy as np
from src.utils import config

class VelocityEstimator:
    """Handles Velocity conversion and estimation."""
    
    @staticmethod
    def calculate_velocity_axis(frequency_axis, angle_deg):
        """Converts frequency axis to velocity axis."""
        theta_rad = np.radians(angle_deg)
        cos_theta = np.cos(theta_rad) if abs(np.cos(theta_rad)) > 1e-4 else 1e-4
        v_axis = frequency_axis * config.C / (2 * config.F0 * cos_theta)
        return v_axis

    @staticmethod
    def estimate_max_velocity(Zxx, v_axis):
        """Estimates max velocity from spectrogram."""
        avg_spec = np.mean(np.abs(Zxx), axis=1)
        if np.max(avg_spec) == 0:
            return 0.0
            
        avg_spec /= np.max(avg_spec)
        threshold = 0.1
        valid = np.where(avg_spec > threshold)[0]
        v_est = np.max(np.abs(v_axis[valid])) if len(valid) > 0 else 0.0
        return v_est
