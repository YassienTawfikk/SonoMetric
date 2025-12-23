import numpy as np
from src.utils import config

class AngleManager:
    """
    Manages Doppler angle configurations and calculates theoretical values.
    """

    def __init__(self):
        self.current_angle = config.DEFAULT_ANGLE  # default

    def set_angle(self, angle_deg):
        """Set the current Doppler angle."""
        if config.MIN_ANGLE <= angle_deg <= config.MAX_ANGLE: # Angle validation (0–180°)
            self.current_angle = angle_deg
        else:
            raise ValueError(f"Angle must be between {config.MIN_ANGLE} and {config.MAX_ANGLE}")

    def get_angle(self):
        """Get current angle in degrees."""
        return self.current_angle

    def get_angle_radians(self):
        """Get current angle in radians."""
        return np.radians(self.current_angle)

    def get_doppler_factor(self):
        """
        Get the Doppler projection factor cos(theta).

        Returns:
            Cosine of current angle
        """
        return np.cos(self.get_angle_radians())

    def get_angle_info(self):
        """
        Get comprehensive information about current angle.

        Returns:
            Dictionary with angle parameters
        """
        angle_rad = self.get_angle_radians()
        return {
            'angle_deg': self.current_angle,
            'angle_rad': angle_rad,
            'cos_theta': np.cos(angle_rad),
            'sin_theta': np.sin(angle_rad),
            'doppler_factor': self.get_doppler_factor()
        }