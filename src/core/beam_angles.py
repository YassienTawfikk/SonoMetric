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

    def calculate_theoretical_vmax(self, v_true):
        """
        Calculate the theoretical measured Vmax for current angle.

        Args:
            v_true: True maximum velocity [m/s]

        Returns:
            v_measured_theory: Theoretical measured velocity [m/s]
        """
        # Doppler shift is proportional to cos(theta)
        # Measured velocity = True velocity * cos(theta)
        angle_rad = self.get_angle_radians()
        return v_true * np.cos(angle_rad)

    def calculate_relative_error(self, v_true, v_measured):
        """
        Calculate relative error between measured and theoretical values.

        Args:
            v_true: True maximum velocity [m/s]
            v_measured: Measured maximum velocity [m/s]

        Returns:
            error_percent: Relative error [%]
        """
        v_theoretical = self.calculate_theoretical_vmax(v_true)
        if v_theoretical == 0:
            return 0.0
        error = abs(v_measured - v_theoretical) / v_theoretical * 100
        return error

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