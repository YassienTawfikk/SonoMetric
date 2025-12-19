import numpy as np
import scipy.signal as signal
from src.utils import config

class SignalProcessor:
    """DSP Pipeline."""
    @staticmethod
    def process_frame(rf_frame, angle_deg):
        # 1. Demodulation
        num_fast, num_slow = rf_frame.shape
        t_axis = np.arange(num_fast) / config.FS
        mixer = np.exp(-1j * 2 * np.pi * config.F0 * t_axis)
        iq_raw = rf_frame * mixer[:, np.newaxis]
        b, a = signal.butter(4, config.F0/config.FS, btype='low')
        iq_demod = signal.filtfilt(b, a, iq_raw, axis=0)
        
        # 2. Gate Extraction
        depth_start = 0.02
        t_start = 2 * depth_start / config.C
        gate_center_idx = int((2 * config.GATE_DEPTH / config.C - t_start) * config.FS)
        gate_width_samples = int((2 * config.GATE_LEN_MM/1000 / config.C) * config.FS)
        
        gate_signal = np.sum(iq_demod[gate_center_idx-gate_width_samples//2 : 
                                      gate_center_idx+gate_width_samples//2, :], axis=0)
                                      
        # 3. Wall Filter
        nyq = config.PRF / 2
        norm_cutoff = 150 / nyq
        b_hp, a_hp = signal.butter(4, norm_cutoff, btype='high')
        filtered = signal.filtfilt(b_hp, a_hp, gate_signal)
        
        # 4. STFT
        f, t, Zxx = signal.stft(filtered, fs=config.PRF, nperseg=32, noverlap=28, nfft=128, return_onesided=False)
        Zxx = np.fft.fftshift(Zxx, axes=0)
        f = np.fft.fftshift(f)
        
        # 5. Velocity Conversion
        theta_rad = np.radians(angle_deg)
        cos_theta = np.cos(theta_rad) if abs(np.cos(theta_rad)) > 1e-4 else 1e-4
        v_axis = f * config.C / (2 * config.F0 * cos_theta)
        
        # 6. V_max Estimation
        avg_spec = np.mean(np.abs(Zxx), axis=1)
        avg_spec /= np.max(avg_spec)
        threshold = 0.1
        valid = np.where(avg_spec > threshold)[0]
        v_est = np.max(np.abs(v_axis[valid])) if len(valid) > 0 else 0.0
        
        return v_axis, t, Zxx, v_est
