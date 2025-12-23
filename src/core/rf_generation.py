import numpy as np
from src.utils import config

class RFGenerator:
    """
    Generates pulsed Doppler RF signals from moving scatterers.
    Simulates a sample volume at vessel center with specified Doppler angle.
    """

    def __init__(self, doppler_angle_deg=60.0):
        """
        Args:
            doppler_angle_deg: Angle between ultrasound beam and flow direction
        """
        self.set_angle(doppler_angle_deg)
        self.f0 = config.TRANSDUCER_FREQ    # ultrasound center frequency

    def set_angle(self, angle_deg):
        """Update the Doppler angle dynamically."""
        self.doppler_angle = np.radians(angle_deg)
        self.c = config.SPEED_OF_SOUND
        self.fs = config.PRF  # Use PRF for slow-time baseband simulation

        # Sample volume definition
        self.gate_depth = config.GATE_DEPTH
        self.gate_length = config.GATE_LENGTH
        self.gate_width = config.GATE_WIDTH

        # Time tracking
        self.time = 0.0

    def generate_rf_sample(self, phantom, duration):
        """
        Generate RF data for a time window.

        Args:
            phantom: VesselPhantom object with scatterer positions/velocities
            duration: Time duration to simulate [s]

        Returns:
            rf_signal: Complex RF signal (I+jQ)
            time_axis: Time array
        """
        # Number of samples
        n_samples = int(duration * self.fs)
        time_axis = np.arange(n_samples) / self.fs + self.time      # Offset by self.time for phase continuity

        # Filter scatterers within sample volume (gate)
        in_gate = self._scatterers_in_gate(phantom)

        if np.sum(in_gate) == 0:
            # No scatterers in sample volume
            return np.zeros(n_samples, dtype=complex), time_axis

        # Get velocities of scatterers in gate (projected onto beam axis)
        vx_gate = phantom.vx[in_gate]
        v_doppler = vx_gate * np.cos(self.doppler_angle)

        # Calculate Doppler shifts for each scatterer
        doppler_shifts = 2 * self.f0 * v_doppler / self.c

        # Get initial phases (based on position along beam axis)
        x_gate = phantom.x[in_gate]
        y_gate = phantom.y[in_gate]
        z_gate = phantom.z_rel[in_gate]

        # Distance along beam axis (accounting for angle)
        # Beam points at angle to x-axis
        beam_distance = (x_gate * np.cos(self.doppler_angle) +
                         y_gate * np.sin(self.doppler_angle))

        initial_phases = 2 * np.pi * self.f0 * 2 * beam_distance / self.c

        # Generate RF signal as sum of complex exponentials
        rf_signal = np.zeros(n_samples, dtype=complex)

        amplitude = 1.0 / np.sqrt(len(doppler_shifts))  # Normalize

        for i, (f_d, phi0) in enumerate(zip(doppler_shifts, initial_phases)):
            # Each scatterer contributes a tone at (f0 + f_doppler)
            # We'll work at baseband after demodulation, so just use f_doppler
            rf_signal += amplitude * np.exp(1j * (2 * np.pi * f_d * time_axis + phi0))

        # Add noise
        noise_power = 0.1
        noise = (np.random.randn(n_samples) + 1j * np.random.randn(n_samples)) * noise_power
        rf_signal += noise

        # Update time
        self.time += duration

        return rf_signal, time_axis

    def _scatterers_in_gate(self, phantom):
        """
        Determine which scatterers are within the sample volume.

        Returns:
            Boolean array indicating scatterers in gate
        """
        # Define gate boundaries
        # Axial (depth): around gate_depth
        depth_from_surface = self.gate_depth + phantom.y  # y is radial position
        in_axial = np.abs(depth_from_surface - self.gate_depth) < self.gate_length / 2

        # Lateral: small region around centerline
        in_lateral = np.abs(phantom.z_rel) < self.gate_width / 2

        # Elevation: small range in x-direction
        in_elevation = np.abs(phantom.x) < self.gate_width / 2

        return in_axial & in_lateral & in_elevation

    def reset_time(self):
        """Reset the time counter for new acquisition."""
        self.time = 0.0


