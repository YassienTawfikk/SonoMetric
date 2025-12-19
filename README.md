# SonoMetric

**Medical-Grade Pulsed Doppler Ultrasound Simulation**

SonoMetric is a high-fidelity PyQt5 application designed to simulate Pulsed Wave (PW) Doppler ultrasound signal acquisition and processing. It features a professional "Medical Dark" user interface, real-time spectral analysis, and custom-built physics simulation engines.

## Features

- **Medical Grade UI**: Deep dark theme (`#121212`) with "Medical Cyan" accents, designed for radiology environments.
- **Real-Time Simulation**: Multithreaded physics engine simulating scatterer movement and RF signal backscattering.
- **Spectral Analysis**: Custom signal processing pipeline (STFT) displayed as a dynamic spectrogram.
- **Interactive Controls**:
  - Segmented Angle Control (30°, 60°, 75°).
  - Status Indication System.
- **Quantitative Metrics**: Real-time velocity estimation and error tracking.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/YourUsername/SonoMetric.git
   cd SonoMetric
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main application:

```bash
python main.py
```

## Technology Stack

- **Python 3.8+**
- **PyQt5**: Core UI framework.
- **Matplotlib**: high-performance plotting.
- **NumPy / SciPy**: Signal processing and math backend.

## License

MIT License
