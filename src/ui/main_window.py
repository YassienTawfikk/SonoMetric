import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGroupBox, QFrame, QMessageBox, QButtonGroup, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QFont
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.utils import config, cleanup
from src.controller import DopplerController

# --- Main Window (GUI) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SonoMetric: Pulsed Doppler Simulation")
        self.resize(1200, 850)
        
        # Data Storage
        self.err_history = [] 
        
        # Controller Init
        self.controller = DopplerController()
        self.controller.results_ready.connect(self.handle_results)
        self.controller.error_occurred.connect(self.handle_error)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Central Widget & Layout
        central_widget = QWidget()
        central_widget.setStyleSheet(
            f"""
                background-color: transparent;
                color: #e6e9ef;
                font-size: 14px;
            """
        )
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
            # For QSS targeting logic in styles.qss which uses class="segment-btn" or [segment="true"]?
            # Creating alias property for cleaner QSS if needed, 
            # but keeping class property as per previous working version.
            # Adding standard Qt property for QSS:
            btn.setProperty("segment", True)
            
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
        font_mono = QFont("Menlo", 13)
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
        self.btn_quit.setCursor(Qt.PointingHandCursor)
        self.btn_quit.setFixedHeight(45)
        self.btn_quit.clicked.connect(self.close)
        sidebar_layout.addWidget(self.btn_quit)
        
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
        """Initialize simulation via Controller."""
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

        # Delegate to Controller
        self.controller.start_acquisition(angle)

    @pyqtSlot(object, object, object, float, int)
    def handle_results(self, v_axis, t_spec, Zxx, v_est, angle):
        """Updates UI and Plots with results from Controller."""
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
        
        self.ax_spec.set_title(f"SPECTRAL DOPPLER (ANGLE: {angle}\u00b0)", color='#e0e0e0', fontsize=10, loc='left', weight='bold')
        self.ax_spec.set_ylabel("VELOCITY (m/s)", color='#777', fontsize=9)
        self.ax_spec.tick_params(colors='#777', which='both', labelsize=9)
        self.ax_spec.set_ylim(-config.V_MAX_TRUE*3.5, config.V_MAX_TRUE*3.5)
        
        # Reference Lines
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
        if self.controller:
            self.controller.stop_acquisition()
        cleanup.clean_project_artifacts()
        event.accept()
