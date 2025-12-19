import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from src.utils import config
from src.core.laminar_flow import VesselPhantom


class SimulationWorker(QThread):
    """
    Runs the laminar flow simulation in a separate thread.
    Emits scatterer positions continuously for visualization.
    """
    updated = pyqtSignal(object, object, object) # x, y, z arrays
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            # 1. Initialize Physics Objects
            phantom = VesselPhantom(
                config.VESSEL_RADIUS, config.VESSEL_LENGTH,
                config.V_MAX_TRUE, config.NUM_SCATTERERS, config.GATE_DEPTH
            )

            # Simulation parameters
            fps = 30
            dt = 1.0 / fps
            
            # Loop
            while self._is_running:
                # Move Scatterers
                phantom.update(dt)
                
                # Emit positions
                self.updated.emit(phantom.x.copy(), phantom.y.copy(), phantom.z_rel.copy())
                
                # Control frame rate
                self.msleep(int(dt * 1000))

        except Exception as e:
            self.error.emit(str(e))


class DopplerController(QObject):
    """
    Orchestrates the interaction between the UI and the Simulation logic.
    """
    # Signals to UI
    flow_update = pyqtSignal(object, object, object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None

    def start_simulation(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self.worker = SimulationWorker()
        self.worker.updated.connect(self._handle_worker_update)
        self.worker.error.connect(self._handle_worker_error)
        self.worker.start()

    def _handle_worker_update(self, x, y, z):
        self.flow_update.emit(x, y, z)
        
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
