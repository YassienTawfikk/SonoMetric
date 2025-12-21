# # --- Constants & Physics Parameters ---
# C = 1540.0              # Speed of sound (m/s)
# F0 = 5.0e6              # Frequency (Hz)
# FS = 40.0e6             # Sample Rate (Hz)
# PRF = 10000.0           # Pulse Repetition Freq (Hz)
# PULSE_CYCLES = 4        # Number of cycles in transmit pulse
# V_MAX_TRUE = 0.5        # Max Velocity (m/s)
# VESSEL_RADIUS = 0.005   # Vessel radius (m)
# VESSEL_LENGTH = 0.05    # Vessel length (m)
# NUM_SCATTERERS = 2000   # Number of scatterers
# GATE_DEPTH = 0.04       # Depth of vessel center (m)
# GATE_LEN_MM = 2.0       # Gate length (mm)
# NUM_LINES = 128         # Slow time samples per frame

# Physical Parameters
VESSEL_RADIUS = 0.005  # [m] 5mm radius
VESSEL_LENGTH = 0.05   # [m] 5cm length
V_MAX_TRUE = 0.5       # [m/s] Maximum velocity at center

# Simulation Parameters
NUM_SCATTERERS = 2000  # Original value
FPS = 30               # Original 30 FPS

# Ultrasound Parameters
TRANSDUCER_FREQ = 5e6      # [Hz] 5 MHz center frequency
SPEED_OF_SOUND = 1540      # [m/s] Speed of sound in tissue
SAMPLING_FREQ = 20e6       # [Hz] 20 MHz sampling rate (4x Nyquist)
PRF = 10000                 # [Hz] Pulse Repetition Frequency (Increased for 30 deg)

# Sample Volume (Gate) Parameters
GATE_DEPTH = 0.03          # [m] 3cm depth from surface
GATE_LENGTH = 0.005        # [m] 5mm axial length
GATE_WIDTH = 0.002         # [m] 2mm lateral width

# Doppler Angles
DEFAULT_ANGLE = 60         # [degrees] Default Doppler angle
MIN_ANGLE = -180             # [degrees] Minimum steer angle
MAX_ANGLE = 180             # [degrees] Maximum steer angle

# Signal Processing Parameters
RF_WINDOW_DURATION = 0.05  # REDUCED from 0.1s for faster processing
STFT_WINDOW_SIZE = 128     # REDUCED from 256 for faster FFT
STFT_OVERLAP = 0.5         # REDUCED from 0.75 for less computation