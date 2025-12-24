import numpy as np
from src.utils import config
from src.core.beam_angles import AngleManager


# class velocity_estimation:
#     """Small helper to compute theoretical measured vmax and relative error."""
#
#     def calculate_measured_vmax(self, v_true: float, angle_deg: float = None)-> float:
#             """
#             Calculate the theoretical measured Vmax for current angle.
#
#             Args:
#                 v_true: True maximum velocity [m/s]
#                 angle_deg: Doppler angle in degrees. If None uses AngleManager default.
#
#             Returns:
#                 v_measured_theory: Theoretical measured velocity [m/s]
#             """
#             angle_mgr = AngleManager()
#             if angle_deg is not None:
#                 angle_mgr.set_angle(int(angle_deg))
#             # Doppler shift is proportional to cos(theta)
#             # Measured velocity = True velocity * cos(theta)
#             angle_rad = angle_mgr.get_angle_radians()
#             return float(v_true * np.cos(angle_rad))
#
#     def calculate_relative_error(self, v_true: float, v_measured: float, angle_deg: float = None):
#             """
#             Calculate relative error between measured and theoretical values.
#
#             Args:
#                 v_true: True maximum velocity [m/s]
#                 v_measured: Measured maximum velocity [m/s]
#                 angle_deg: Doppler angle in degrees used to compute theoretical value.
#
#             Returns:
#                 error_percent: Relative error [%]
#             """
#             v_theoretical = self.calculate_measured_vmax(v_true, angle_deg=angle_deg)
#             if v_theoretical == 0:
#                 return 0.0
#             error = abs(v_measured - v_theoretical) / v_theoretical * 100
#             return float(error)

class velocity_estimation:
    """Small helper to compute theoretical measured vmax and relative error."""

    def calculate_measured_vmax(self, v_true: float) -> float:
        """
        Returns the Theoretical Measured Vmax (The Target).
        Since the UI applies Angle Correction, the target is simply v_true.
        """
        # The angle doesn't matter for the target value because
        # the system is designed to compensate for it.
        return float(v_true)

    def calculate_relative_error(self, v_true: float, v_measured: float, angle_deg: float = None):
        """
        Calculate relative error between measured and theoretical values.
        """
        # The target is just the True Velocity (0.5)
        v_theoretical = self.calculate_measured_vmax(v_true)

        if v_theoretical == 0:
            return 0.0

        error = abs(v_measured - v_theoretical) / v_theoretical * 100
        return float(error)
