# SonoMetric

**Medical-Grade Pulsed Doppler Ultrasound Simulation**

SonoMetric is a high-fidelity PyQt5 application designed to simulate Pulsed Wave (PW) Doppler ultrasound signal acquisition and processing. It features a professional "Medical Dark" user interface, real-time spectral analysis, and custom-built physics simulation engines.

![App Design Overview](https://github.com/user-attachments/assets/466e2356-4d7e-49e5-941a-31ab4d1c1c5b)

## **Video Demo**

<https://github.com/user-attachments/assets/092e29a9-f01c-4ec0-91c7-03a8c9e121d2>

## Features

- **Real-Time Simulation**: Multithreaded physics engine simulating scatterer movement and RF signal backscattering.
- **Spectral Analysis**: Custom signal processing pipeline (STFT) displayed as a dynamic spectrogram.
- **Quantitative Metrics**: Real-time velocity estimation and error tracking.

## Physics Simulation

### Laminar Flow Model

The simulation implements a parabolic flow profile characteristic of laminar flow in a cylindrical vessel. The velocity $v(r)$ of a scatterer at radial distance $r$ is given by:

$$v(r) = v_{max} \cdot \left(1 - \frac{r^2}{R^2}\right)$$

Where:

- $v_{max}$ is the maximum centerline velocity.
- $R$ is the vessel radius.

### RF Signal Generation

The core engine simulates the backscattered RF signal by summing the contributions of individual scatterers within the sample volume.

The Doppler shift $f_d$ for each scatterer is calculated based on the angle of insonation $\theta$:

$$f_d = \frac{2 f_0 v \cos(\theta)}{c}$$

Where:

- $f_0$ is the transducer frequency.
- $c$ is the speed of sound in tissue (1540 m/s).

The total received signal $S(t)$ is modeled as the sum of baseband complex exponentials from all $N$ scatterers in the sample volume:

$$S(t) = \sum_{n=1}^{N} A \cdot e^{j(2\pi f_{d,n} t + \phi_n)} + \text{Noise}$$

This is implemented directly in the physics engine (`src/core/rf_generation.py`):

### I/Q Components (Real & Imaginary)

The generated signal is **complex-valued**, consisting of two orthogonal components:

1. **Real Component ($I$ - In-phase)**: Represents the cosine term of the signal.
2. **Imaginary Component ($Q$ - Quadrature)**: Represents the sine term of the signal.

**Purpose**:
In standard signal processing, a real-valued signal (just cosine) has a symmetric spectrum, making it impossible to distinguish between positive and negative frequencies. By using both **Real ($I$)** and **Imaginary ($Q$)** components, we preserve the phase information, allowing the system to distinguish between **positive Doppler shifts** (flow towards the probe) and **negative Doppler shifts** (flow away from the probe).

## Signal Processing

### STFT Pipeline

The application processes the raw RF data using a Short-Time Fourier Transform (STFT) pipeline to generate the spectral display:

1. **Windowing**: A Hamming window is applied to overlapping segments of the RF signal to reduce spectral leakage.
2. **FFT**: A Fast Fourier Transform (FFT) is computed for each segment.
3. **Power Spectrum**: The squared magnitude of the FFT output is calculated to obtain the power spectrum.

### Velocity Estimation

The frequency axis of the spectrogram is mapped back to velocity units using the inverse Doppler equation. This allows for real-time quantitative velocity estimation and error calculation against the theoretical $v_{max}$.

## Configuration Parameters

The simulation uses medically accurate physical parameters defined in `src/utils/config.py`:

| Parameter | Value | Justification |
| :--- | :--- | :--- |
| **Transducer Frequency** | `5 MHz` | Standard frequency for vascular ultrasound, offering a balance between penetration and resolution. |
| **Speed of Sound** | `1540 m/s` | Average speed of sound in soft biological tissue. |
| **PRF** | `10 kHz` | Pulse Repetition Frequency set to avoid aliasing for expected blood velocities (~0.5 m/s). |
| **Sampling Frequency** | `20 MHz` | High sampling rate (4x Nyquist) to ensure high-fidelity RF signal generation before demodulation. |

> [!NOTE]
> **Visualization Logic**: The application visualizes the **Doppler Shift (Spectrogram)**, not the raw RF signal.
>
> The raw RF signal is a high-frequency amplitude-modulated wave (MHz range) which is not visually intuitive for clinical diagnosis. Instead, we perform spectral analysis to display the Doppler shift, which directly correlates to blood flow velocity over time. This mimics the standard "Spectral Doppler" display found in clinical ultrasound machines.

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/YassienTawfikk/SonoMetric.git
   cd SonoMetric
   ```

2. **Create a virtual environment** (Recommended)

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the application, simply run the main script:

```bash
python main.py
```

## Project Structure

The source code is organized as follows:

```text
src/
├── controller.py    # Application logic & event handling
├── core/            # Physics simulation engines & signal processing
├── ui/              # User Interface implementation (PyQt5)
└── utils/           # Helper functions & utilities
```

## Contributors

<div>
<table align="center">
  <tr>
        <td align="center">
      <a href="https://github.com/YassienTawfikk" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/126521373?v=4" width="150px;" alt="Yassien Tawfik"/>
        <br />
        <sub><b>Yassien Tawfik</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/madonna-mosaad" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/127048836?v=4" width="150px;" alt="Madonna Mosaad"/>
        <br />
        <sub><b>Madonna Mosaad</b></sub>
      </a>
    </td>
        <td align="center">
      <a href="https://github.com/nancymahmoud1" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/125357872?v=4" width="150px;" alt="Nancy Mahmoud"/>
        <br />
        <sub><b>Nancy Mahmoud</b></sub>
      </a>
    </td>
        <td align="center">
      <a href="https://github.com/RawanAhmed444" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/94761201?v=4" width="150px;" alt="Rawan Ahmed"/>
        <br />
        <sub><b>Rawan Ahmed</b></sub>
      </a>
    </td>
        <td align="center">
      <a href="https://github.com/NadaMohamedElBasel" target="_blank">
        <img src="https://avatars.githubusercontent.com/u/110432081?v=4" width="150px;" alt="Nada Mohamed"/>
        <br />
        <sub><b>Nada Mohamed</b></sub>
      </a>
    </td>
  </tr>
</table>
</div>
