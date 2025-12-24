import numpy as np
from src.utils import config


class SpectrogramGenerator:
    """
    Computes Doppler spectrogram from RF data using STFT.
    """

    def __init__(self, doppler_angle_deg=60.0):
        self.doppler_angle = np.radians(doppler_angle_deg)
        self.f0 = config.TRANSDUCER_FREQ
        self.c = config.SPEED_OF_SOUND
        self.fs = config.PRF  # Use PRF for slow-time baseband simulation

    def compute_spectrogram(self, rf_signal, time_axis, window_size=256, overlap=0.75):
        """
        Compute velocity spectrogram from RF signal.

        Args:
            rf_signal: Complex RF signal
            time_axis: Time array
            window_size: FFT window size
            overlap: Overlap fraction (0-1)

        Returns:
            spec_time: Time axis for spectrogram
            velocities: Velocity array [m/s]
            spec_power: Power spectrogram (2D array)
        """
        hop_size = int(window_size * (1 - overlap))

        # Number of segments
        n_segments = (len(rf_signal) - window_size) // hop_size + 1

        # Frequency axis (Doppler shifts)
        freqs = np.fft.fftshift(np.fft.fftfreq(window_size, 1 / self.fs))

        # Convert to velocities using Doppler equation
        # velocities = freqs * self.c / (2 * self.f0 * np.cos(self.doppler_angle))
        # Doppler frequency f_d = 2*f0*(v_proj)/c where v_proj = v_true * cos(theta)
        # Corrected (Clinical Flow Velocity):
        # We divide by cos(theta) to restore the true velocity scale
        cos_theta = np.cos(self.doppler_angle)
        if abs(cos_theta) < 1e-3:  # Handle 90 degree case
            cos_theta = 1e-3 * np.sign(cos_theta) if cos_theta != 0 else 1e-3

        velocities = freqs * self.c / (2 * self.f0 * cos_theta)

        # Initialize spectrogram
        spec_power = np.zeros((len(freqs), n_segments))
        spec_time = np.zeros(n_segments)

        # Hamming window
        window = np.hamming(window_size)

        for i in range(n_segments):
            start_idx = i * hop_size
            end_idx = start_idx + window_size

            if end_idx > len(rf_signal):
                break

            segment = rf_signal[start_idx:end_idx] * window

            # FFT
            spectrum = np.fft.fftshift(np.fft.fft(segment))
            spec_power[:, i] = np.abs(spectrum) ** 2

            # Time stamp (center of window)
            spec_time[i] = time_axis[start_idx + window_size // 2]

        # Remove unused columns
        spec_power = spec_power[:, :n_segments]

        return spec_time, velocities, spec_power

    def estimate_max_velocity(self, velocities, spec_power):
        """
        Estimate maximum velocity from spectrogram.
        Uses peak detection on mean spectrum.

        Returns:
            v_max_measured: Estimated maximum velocity [m/s]
        """
        # Average spectrum over time
        mean_spectrum = np.mean(spec_power, axis=1)

        # Find peak in positive velocities
        positive_vel_idx = velocities > 0
        if np.sum(positive_vel_idx) == 0:
            return 0.0

        peak_idx = np.argmax(mean_spectrum[positive_vel_idx])
        v_max_measured = velocities[positive_vel_idx][peak_idx]

        return v_max_measured
