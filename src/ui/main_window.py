import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGroupBox, QFrame, QMessageBox, QButtonGroup, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.utils import config, cleanup
from src.core.simulation import VesselPhantom, UltrasoundSim
from src.core.processing import SignalProcessor

# --- Worker Thread (Physics & DSP) ---
class SimulationWorker(QThread):
    """
    Runs the simulation in a separate thread to keep the UI responsive.
    """
    # progress signal removed as requested (no progress bar)
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
                # No progress emit needed
                
            # 4. Signal Processing
            v_axis, t_spec, Zxx, v_est = SignalProcessor.process_frame(rf_frame, self.angle)
            self.finished.emit(v_axis, t_spec, Zxx, v_est)
            
        except Exception as e:
            self.error.emit(str(e))

# --- Main Window (GUI) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SonoMetric: Pulsed Doppler Simulation")
        self.resize(1200, 850)
        
        # Data Storage
        self.err_history = [] 
        
        self.setup_ui()
        self.apply_theme()
        
    def apply_theme(self):
        """Applies a 'Medical Grade' Dark Theme from external stylesheet."""
        try:
            import os
            # Build absolute path to styles.qss relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            style_path = os.path.join(current_dir, "styles.qss")
            
            with open(style_path, "r") as f:
                qss = f.read()
                self.setStyleSheet(qss)
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            # Fallback basic dark theme if file fails
            self.setStyleSheet("QMainWindow { background-color: #121212; color: white; }")
        
    def setup_ui(self):
        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- LEFT SIDEBAR (Controls) ---
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setStyleSheet("background-color: #121212; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setContentsMargins(25, 30, 25, 30)
        
        # Title / Brand
        lbl_title = QLabel("SONOMETRIC")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; letter-spacing: 2px; color: #e0e0e0;")
        sidebar_layout.addWidget(lbl_title)
        
        # 1. Controls Group
        grp_ctrl = QGroupBox("ACQUISITION PARAMETERS")
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setSpacing(15)
        
        ctrl_layout.addWidget(QLabel("ANGLE OF INSONATION (\u03b8)"))
        
        # Segmented Control (Angle Selection)
        seg_layout = QHBoxLayout()
        seg_layout.setSpacing(0) 
        self.group_angle = QButtonGroup(self)
        self.group_angle.setExclusive(True)
        
        angles = ["30", "60", "75"]
        for i, angle in enumerate(angles):
            btn = QPushButton(angle + "\u00b0")
            btn.setCheckable(True)
            btn.setProperty("class", "segment-btn")
            
            if i == 0:
                btn.setObjectName("seg_first")
            elif i == len(angles) - 1:
                btn.setObjectName("seg_last")
            else:
                btn.setObjectName("seg_middle")
                
            self.group_angle.addButton(btn)
            seg_layout.addWidget(btn)
            
            if angle == "60":
                btn.setChecked(True)
                
        ctrl_layout.addLayout(seg_layout)
        grp_ctrl.setLayout(ctrl_layout)
        sidebar_layout.addWidget(grp_ctrl)
        
        # 2. Simulation Action
        self.btn_start = QPushButton("INITIALIZE ACQUISITION")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(45)
        self.btn_start.clicked.connect(self.start_simulation)
        sidebar_layout.addWidget(self.btn_start)
                
        sidebar_layout.addSpacing(20)
        
        # 4. Metrics Group
        grp_res = QGroupBox("QUANTITATIVE ANALYSIS")
        res_layout = QVBoxLayout()
        res_layout.setSpacing(15)
        
        self.lbl_vtrue = QLabel(f"TRUE Vmax:      {config.V_MAX_TRUE} m/s")
        self.lbl_vest = QLabel("MEASURED Vmax:  --")
        self.lbl_err = QLabel("RELATIVE ERROR: --")
        
        # Monospace font for data alignment
        font_mono = QFont("Consolas", 13)
        self.lbl_vtrue.setFont(font_mono)
        self.lbl_vest.setFont(font_mono)
        self.lbl_err.setFont(font_mono)
        
        self.lbl_vtrue.setStyleSheet("color: #777;")
        self.lbl_vest.setStyleSheet("color: #00e5ff; font-weight: bold;")
        self.lbl_err.setStyleSheet("color: #e0e0e0;")
        
        res_layout.addWidget(self.lbl_vtrue)
        res_layout.addWidget(self.lbl_vest)
        res_layout.addWidget(self.lbl_err)
        grp_res.setLayout(res_layout)
        sidebar_layout.addWidget(grp_res)
        
        sidebar_layout.addStretch()
        
        # Quit Button
        self.btn_quit = QPushButton("SYSTEM SHUTDOWN")
        self.btn_quit.setObjectName("btnQuit")
        self.btn_quit.clicked.connect(self.close)
        sidebar_layout.addWidget(self.btn_quit)
        
        # Footer
        lbl_foot = QLabel("SYS ID: SONOMETRIC-V1\nVER: 2.1.0-MED")
        lbl_foot.setObjectName("lblFooter")
        lbl_foot.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_foot)
        
        main_layout.addWidget(sidebar)
        
        # --- RIGHT VISUALIZATION AREA ---
        # Container for plots
        plot_container = QWidget()
        plot_container.setStyleSheet("background-color: #121212;")
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(20, 20, 20, 20)
        
        self.fig = Figure(facecolor='#121212') # Seamless background
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: #121212;")
        plot_layout.addWidget(self.canvas)
        
        main_layout.addWidget(plot_container, stretch=1)
        
        # Initialize Subplots
        self.ax_spec = self.fig.add_subplot(211)
        self.ax_err  = self.fig.add_subplot(212)
        self.fig.subplots_adjust(hspace=0.4, top=0.92, bottom=0.08, left=0.08, right=0.95)
        
        self.init_plots()

    def init_plots(self):
        """Medical Style Plot Initialization."""
        # Spectrogram Axis
        self.ax_spec.set_facecolor('#121212')
        self.ax_spec.set_title("SPECTRAL DOPPLER WAVEFORM", color='#777', fontsize=10, loc='left', weight='bold')
        self.ax_spec.set_ylabel("VELOCITY (m/s)", color='#777', fontsize=9)
        self.ax_spec.tick_params(axis='both', colors='#555', labelsize=9)
        
        # Remove spines for clean look
        for spine in self.ax_spec.spines.values():
            spine.set_visible(False)
        self.ax_spec.grid(True, color='#222', linestyle='-', linewidth=0.5)
        
        # Placeholder
        self.text_placeholder = self.ax_spec.text(0.5, 0.5, "SYSTEM IDLE\nINITIATE ACQUISITION", 
                                                  color='#333', ha='center', va='center',
                                                  fontsize=14, weight='bold',
                                                  transform=self.ax_spec.transAxes)

        # Error Axis
        self.ax_err.set_facecolor('#121212')
        self.ax_err.set_title("ERROR TRACKING LOG (%)", color='#777', fontsize=10, loc='left', weight='bold')
        self.ax_err.set_xlabel("ACQUISITION EVENT", color='#777', fontsize=9)
        self.ax_err.set_ylabel("ABS ERROR (%)", color='#777', fontsize=9)
        self.ax_err.tick_params(axis='both', colors='#555', labelsize=9)
        
        for spine in self.ax_err.spines.values():
            spine.set_visible(False)
        self.ax_err.grid(True, color='#222', linestyle='-', linewidth=0.5, axis='y')

    def start_simulation(self):
        """Initialize and start the worker thread."""
        btn = self.group_angle.checkedButton()
        if not btn: return 
        # Extract angle from "60°"
        text = btn.text().replace("\u00b0","")
        angle = int(text)
        
        # Lock UI
        self.btn_start.setEnabled(False)
        self.btn_start.setText("ACQUIRING SIGNAL...")
        
        for btn in self.group_angle.buttons():
            btn.setEnabled(False)
            
        # Clear placeholder
        if hasattr(self, 'text_placeholder') and self.text_placeholder:
            self.text_placeholder.remove()
            self.text_placeholder = None
            self.canvas.draw_idle()

        # Run Worker
        self.worker = SimulationWorker(angle)
        self.worker.finished.connect(self.handle_results)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    @pyqtSlot(object, object, object, float)
    def handle_results(self, v_axis, t_spec, Zxx, v_est):
        """Updates UI and Plots."""
        # Unlock UI
        self.btn_start.setEnabled(True)
        self.btn_start.setText("INITIALIZE ACQUISITION")
        
        for btn in self.group_angle.buttons():
            btn.setEnabled(True)
        
        # 1. Update Metrics
        err = abs(v_est - config.V_MAX_TRUE) / config.V_MAX_TRUE * 100
        self.err_history.append(err)
        
        self.lbl_vest.setText(f"MEASURED Vmax:  {v_est:.3f} m/s")
        self.lbl_err.setText(f"RELATIVE ERROR: {err:.1f}%")
        
        # Medical Alert Colors
        if err > 15:
            self.lbl_err.setStyleSheet("color: #cf6679; font-weight: bold;") # Red/Error
        else:
            self.lbl_err.setStyleSheet("color: #00c853; font-weight: bold;") # Green/Good
        
        # 2. Update Spectrogram
        self.ax_spec.clear()
        
        Sxx_dB = 10 * np.log10(np.abs(Zxx)**2 + 1e-12)
        # Inferno map fits well with dark medical UI
        self.ax_spec.pcolormesh(t_spec, v_axis, Sxx_dB, shading='gouraud', cmap='inferno')
        
        self.ax_spec.set_title(f"SPECTRAL DOPPLER (ANGLE: {self.worker.angle}\u00b0)", color='#e0e0e0', fontsize=10, loc='left', weight='bold')
        self.ax_spec.set_ylabel("VELOCITY (m/s)", color='#777', fontsize=9)
        self.ax_spec.tick_params(colors='#777', which='both', labelsize=9)
        self.ax_spec.set_ylim(-config.V_MAX_TRUE*3.5, config.V_MAX_TRUE*3.5)
        
        # Reference Lines shouldn't be too distracting
        self.ax_spec.axhline(config.V_MAX_TRUE, color='#00e5ff', linestyle='--', alpha=0.3, linewidth=1)
        self.ax_spec.axhline(-config.V_MAX_TRUE, color='#00e5ff', linestyle='--', alpha=0.3, linewidth=1)
        
        # 3. Update Error Bar Chart (Minimalist)
        self.ax_err.clear()
        
        if self.err_history:
            trials = range(1, len(self.err_history)+1)
            # Use Medical Cyan for bars
            self.ax_err.bar(trials, self.err_history, color='#00e5ff', width=0.5, alpha=0.8)
            
            max_val = max(self.err_history)
            top_lim = max(100, max_val * 1.2) 
            self.ax_err.set_ylim(0, top_lim)
        
        self.ax_err.set_title("ERROR TRACKING (%)", color='#e0e0e0', fontsize=10, loc='left', weight='bold')
        self.ax_err.set_xlabel("ACQUISITION EVENT", color='#777', fontsize=9)
        
        # 4. Re-Apply Styles
        for ax in [self.ax_spec, self.ax_err]:
            ax.set_facecolor('#121212') # Match bg
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.grid(True, color='#222', linestyle='-', linewidth=0.5, alpha=0.5)

        self.canvas.draw_idle()

    @pyqtSlot(str)
    def handle_error(self, msg):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("INITIALIZE ACQUISITION")
        QMessageBox.critical(self, "System Error", f"Acquisition Failed:\n{msg}")

    def closeEvent(self, event):
        """Ensure cleanup of artifacts on exit."""
        cleanup.clean_project_artifacts()
        event.accept()
