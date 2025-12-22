# Physical Parameters
VESSEL_RADIUS = 0.005  # [m] 5mm radius
VESSEL_LENGTH = 0.05   # [m] 5cm length
V_MAX_TRUE = 0.5       # [m/s] Maximum velocity at center

# Simulation Parameters
NUM_SCATTERERS = 2000       # Original value
FPS = 30                    # Original 30 FPS

# Ultrasound Parameters
TRANSDUCER_FREQ = 5e6       # [Hz] 5 MHz center frequency
SPEED_OF_SOUND = 1540       # [m/s] Speed of sound in tissue
SAMPLING_FREQ = 20e6        # [Hz] 20 MHz sampling rate (4x Nyquist)
PRF = 10000                 # [Hz] Pulse Repetition Frequency (Increased for 30 deg)

# Sample Volume (Gate) Parameters
GATE_DEPTH = 0.03           # [m] 3cm depth from surface
GATE_LENGTH = 0.005         # [m] 5mm axial length
GATE_WIDTH = 0.002          # [m] 2mm lateral width

# Doppler Angles
DEFAULT_ANGLE = 60          # [degrees] Default Doppler angle
MIN_ANGLE = 0               # [degrees] Minimum steer angle
MAX_ANGLE = 180             # [degrees] Maximum steer angle

# Signal Processing Parameters
RF_WINDOW_DURATION = 0.05   # REDUCED from 0.1s for faster processing
STFT_WINDOW_SIZE = 128      # REDUCED from 256 for faster FFT
STFT_OVERLAP = 0.5          # REDUCED from 0.75 for less computation