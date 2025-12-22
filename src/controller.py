import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from src.utils import config
from src.core.laminar_flow import VesselPhantom
from src.core.rf_generation import RFGenerator
from src.core.stft_processing import SpectrogramGenerator
from src.core.beam_angles import AngleManager
from src.core.velocity_estimation import velocity_estimation


class SimulationWorker(QThread):
    """
    Runs the laminar flow simulation with RF generation in a separate thread.
    Emits scatterer positions, RF data, and spectrograms for visualization.
    OPTIMIZED: Reduced update frequency and smarter buffering.
    """
    flow_updated = pyqtSignal(object, object, object)  # x, y, z arrays
    rf_updated = pyqtSignal(object, object)  # rf_signal, time_axis
    spectrum_updated = pyqtSignal(object, object, object)  # time, velocities, power
    metrics_updated = pyqtSignal(float, float, float)  # v_true, v_measured, error
    error = pyqtSignal(str)

    def __init__(self, doppler_angle=60):
        super().__init__()
        self._is_running = True
        self.doppler_angle = doppler_angle

    def stop(self):
        self._is_running = False

    def set_angle(self, angle_deg):
        """Update simulation angle dynamically."""
        self.doppler_angle = angle_deg
        # Update components if they exist
        if hasattr(self, 'rf_gen'):
            self.rf_gen.set_angle(angle_deg)
        if hasattr(self, 'angle_mgr'):
            self.angle_mgr.set_angle(angle_deg)
        # Note: SpectrogramGenerator currently ignores live updates in compute_spectrogram, 
        # but re-init isn't needed if it just uses constants or we don't change f0/c.
        # Ideally SpecGen should also have set_angle if it cached cos_theta.
        # Based on code, it uses self.doppler_angle in init, so we should update it.
        if hasattr(self, 'spec_gen'):
            self.spec_gen.doppler_angle = np.radians(angle_deg)

    def run(self):
        try:
            # Initialize Physics Objects
            phantom = VesselPhantom(
                config.VESSEL_RADIUS, config.VESSEL_LENGTH,
                config.V_MAX_TRUE, config.NUM_SCATTERERS, config.GATE_DEPTH
            )

            # Initialize RF generator and spectrogram processor
            self.rf_gen = RFGenerator(doppler_angle_deg=self.doppler_angle)
            self.spec_gen = SpectrogramGenerator(doppler_angle_deg=self.doppler_angle)
            self.angle_mgr = AngleManager()
            velocity_est = velocity_estimation()
            self.angle_mgr.set_angle(self.doppler_angle)

            # Simulation parameters
            fps = 30  # REDUCED from 30 for better performance
            dt = 1.0 / fps
            rf_duration = config.RF_WINDOW_DURATION

            # Optimized buffering
            rf_buffer = []
            rf_time_buffer = []
            max_buffer_size = 5  # REDUCED from 10

            frame_count = 0
            flow_update_interval = 2     # Update flow plot every 2 frames
            rf_update_interval = 5       # Update RF every 5 frames (was 3)
            spec_update_interval = 10    # Update spectrogram every 10 frames

            # Loop
            while self._is_running:
                # Move Scatterers
                phantom.update(dt)

                # Emit flow positions (LESS FREQUENTLY)
                if frame_count % flow_update_interval == 0:
                    self.flow_updated.emit(
                        phantom.x.copy(),
                        phantom.y.copy(),
                        phantom.z_rel.copy()
                    )

                # Generate RF data periodically
                if frame_count % rf_update_interval == 0:
                    # Generate RF sample
                    rf_signal, time_axis = self.rf_gen.generate_rf_sample(
                        phantom, rf_duration
                    )

                    # Emit RF signal
                    self.rf_updated.emit(rf_signal.copy(), time_axis.copy())

                    # Accumulate for spectrogram
                    rf_buffer.append(rf_signal)
                    rf_time_buffer.append(time_axis)

                    # Keep buffer size limited
                    if len(rf_buffer) > max_buffer_size:
                        rf_buffer.pop(0)
                        rf_time_buffer.pop(0)

                # Generate spectrogram LESS FREQUENTLY
                if frame_count % spec_update_interval == 0 and len(rf_buffer) >= 3:
                    # Concatenate RF data (only when needed)
                    rf_combined = np.concatenate(rf_buffer)
                    time_combined = np.concatenate(rf_time_buffer)

                    # Compute spectrogram
                    spec_time, velocities, spec_power = self.spec_gen.compute_spectrogram(
                        rf_combined, time_combined,
                        window_size=config.STFT_WINDOW_SIZE,
                        overlap=config.STFT_OVERLAP
                    )

                    # Emit spectrogram
                    self.spectrum_updated.emit(
                        spec_time.copy(),
                        velocities.copy(),
                        spec_power.copy()
                    )

                    # Calculate metrics
                    v_measured = self.spec_gen.estimate_max_velocity(
                        velocities, spec_power
                    )
                    v_true = config.V_MAX_TRUE

                    # Debug info (less frequent)
                    if frame_count % 30 == 0:  # Only every 30 frames
                        num_in_gate = np.sum(self.rf_gen._scatterers_in_gate(phantom))
                        pass
                        # print(f"[DEBUG] Angle: {self.doppler_angle}° | "
                        #       f"Scatterers: {num_in_gate} | "
                        #       f"V_measured: {v_measured:.3f} m/s")

                    error = velocity_est.calculate_relative_error(v_true, v_measured, angle_deg=self.doppler_angle)

                    # Emit metrics
                    self.metrics_updated.emit(float(v_true), float(v_measured), float(error))

                frame_count += 1

                # Control frame rate
                self.msleep(int(dt * 1000))

        except Exception as e:
            self.error.emit(str(e))


class DopplerController(QObject):
    """
    Orchestrates the interaction between the UI and the Simulation logic.
    Manages angle changes and coordinates multi-angle acquisitions.
    """
    # Signals to UI
    flow_update = pyqtSignal(object, object, object)
    rf_update = pyqtSignal(object, object)
    spectrum_update = pyqtSignal(object, object, object)
    metrics_update = pyqtSignal(float, float, float)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.worker = None
        self.angle_manager = AngleManager()
        self.current_angle = self.angle_manager.get_angle()

    def start_simulation(self, angle=None):
        """Start simulation with specified angle."""
        if self.worker is not None and self.worker.isRunning():
            return

        if angle is not None:
            self.current_angle = angle
            self.angle_manager.set_angle(angle)

        self.worker = SimulationWorker(doppler_angle=self.current_angle)
        self.worker.flow_updated.connect(self._handle_flow_update)
        self.worker.rf_updated.connect(self._handle_rf_update)
        self.worker.spectrum_updated.connect(self._handle_spectrum_update)
        self.worker.metrics_updated.connect(self._handle_metrics_update)
        self.worker.error.connect(self._handle_worker_error)
        self.worker.start()

    def update_angle_live(self, angle):
        """Update angle live without restarting simulation."""
        self.current_angle = angle
        self.angle_manager.set_angle(angle)
        if self.worker is not None and self.worker.isRunning():
            self.worker.set_angle(angle)

    def change_angle(self, new_angle):
        """Change Doppler angle (requires restart)."""
        was_running = self.worker is not None and self.worker.isRunning()

        if was_running:
            # For massive changes or logic that requires restart, use this.
            # But for simple steering, update_angle_live is better.
            self.update_angle_live(new_angle)
        else:
            self.current_angle = new_angle
            self.angle_manager.set_angle(new_angle)
            if was_running:
                self.start_simulation(angle=new_angle)

    def _handle_flow_update(self, x, y, z):
        self.flow_update.emit(x, y, z)

    def _handle_rf_update(self, rf_signal, time_axis):
        self.rf_update.emit(rf_signal, time_axis)

    def _handle_spectrum_update(self, time, velocities, power):
        self.spectrum_update.emit(time, velocities, power)

    def _handle_metrics_update(self, v_true, v_measured, error):
        self.metrics_update.emit(v_true, v_measured, error)

    def _handle_worker_error(self, msg):
        self.error_occurred.emit(msg)
        self._cleanup_worker()

    def stop_simulation(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self._cleanup_worker()

    def _cleanup_worker(self):
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def get_current_angle(self):
        """Return current Doppler angle."""
        return self.current_angle
