import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from src.utils import config


class SimulationWorker(QThread):
    """
    Runs the simulation in a separate thread to keep the UI responsive.
    """
    finished = pyqtSignal(object, object, object, float) # v_axis, t, Zxx, v_est
    error = pyqtSignal(str)

    def __init__(self, angle):
        super().__init__()
        self.angle = angle
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            # 1. Initialize Physics Objects
            from src.core.laminar_flow import VesselPhantom
            from src.core.rf_generation import UltrasoundSim
            from src.core.stft_processing import STFTProcessor
            from src.core.velocity_estimation import VelocityEstimator
            
            phantom = VesselPhantom(
                config.VESSEL_RADIUS, config.VESSEL_LENGTH,
                config.V_MAX_TRUE, config.NUM_SCATTERERS, config.GATE_DEPTH
            )
            sim = UltrasoundSim(config.FS, config.F0, config.C, config.PULSE_CYCLES)

            # 2. Setup Time Axis
            depth_strt, depth_end = 0.02, 0.06
            t_ax = np.arange(2*depth_strt/config.C, 2*depth_end/config.C, 1/config.FS)

            rf_frame = np.zeros((len(t_ax), config.NUM_LINES))
            dt_slow = 1.0/config.PRF

            # 3. Acquisition Loop
            for k in range(config.NUM_LINES):
                if not self._is_running: return

                # Acquire single line
                rf_line = sim.acquire_rf_line(phantom, self.angle, t_ax)
                rf_frame[:, k] = rf_line

                # Move Scatterers
                phantom.update(dt_slow)

            # 4. Signal Processing using new modules
            # a. STFT
            v_axis_temp_unused, t_spec, Zxx = STFTProcessor.compute_spectrogram(rf_frame)
            
            # b. Velocity Axis & Estimation
            v_axis = VelocityEstimator.calculate_velocity_axis(v_axis_temp_unused, self.angle)
            # wait, compute_spectrogram returns f (freq), t, Zxx. 
            # We need to map freq to velocity.
            # let's fix the unpacking.
            # STFTProcessor returns f, t, Zxx 
            f_axis, t_spec, Zxx = STFTProcessor.compute_spectrogram(rf_frame)
            v_axis = VelocityEstimator.calculate_velocity_axis(f_axis, self.angle)
            v_est = VelocityEstimator.estimate_max_velocity(Zxx, v_axis)
            
            self.finished.emit(v_axis, t_spec, Zxx, v_est)

        except Exception as e:
            self.error.emit(str(e))

class DopplerController(QObject):
    """
    Orchestrates the interaction between the UI and the Simulation/Processing logic.
    """
    # Signals to UI
    results_ready = pyqtSignal(object, object, object, float, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None

    def start_acquisition(self, angle):
        if self.worker is not None and self.worker.isRunning():
            return

        self.worker = SimulationWorker(angle)
        self.worker.finished.connect(self._handle_worker_finished)
        self.worker.error.connect(self._handle_worker_error)
        self.worker.start()

    def _handle_worker_finished(self, v_axis, t_spec, Zxx, v_est):
        # Pass angle back to UI
        angle = self.worker.angle
        self.results_ready.emit(v_axis, t_spec, Zxx, v_est, angle)
        
        if self.worker:
             self.worker.deleteLater() # clean up
        self.worker = None

    def _handle_worker_error(self, msg):
        self.error_occurred.emit(msg)
        if self.worker:
             self.worker.deleteLater()
        self.worker = None

    def stop_acquisition(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
