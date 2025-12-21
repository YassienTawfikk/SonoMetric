import numpy as np
from src.utils import config


class AngleManager:
    """
    Manages Doppler angle configurations and calculates theoretical values.
    """
    AVAILABLE_ANGLES = [30, 60, 75]  # degrees

    def __init__(self):
        self.current_angle = 60  # default

    def set_angle(self, angle_deg):
        """Set the current Doppler angle."""
        if angle_deg in self.AVAILABLE_ANGLES:
            self.current_angle = angle_deg
        else:
            raise ValueError(f"Angle must be one of {self.AVAILABLE_ANGLES}")

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

    @staticmethod
    def get_all_angles():
        """Return list of all available angles."""
        return AngleManager.AVAILABLE_ANGLES.copy()

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