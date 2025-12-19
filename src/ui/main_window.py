import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QMessageBox, QGroupBox, QButtonGroup, QSizePolicy)
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
        self.setWindowTitle("SonoMetric: Laminar Flow Simulation")
        self.resize(1280, 900)
        
        # Controller Init
        self.controller = DopplerController()
        self.controller.flow_update.connect(self.update_flow_plot)
        self.controller.error_occurred.connect(self.handle_error)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Central Widget & Layout
        central_widget = QWidget()
        central_widget.setStyleSheet(
            f"""
                background-color: #121212;
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
        sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setContentsMargins(25, 30, 25, 30)
        
        # Title / Brand
        lbl_title = QLabel("SONOMETRIC")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; letter-spacing: 2px; color: #ff5252;")
        sidebar_layout.addWidget(lbl_title)
        
        # 1. Flow Control (Active)
        btn_layout = QVBoxLayout()
        self.btn_start = QPushButton("START FLOW SIMULATION")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: #fff;
                border-radius: 4px;
                font-weight: bold;
                letter-spacing: 1px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        self.btn_start.clicked.connect(self.toggle_simulation)
        btn_layout.addWidget(self.btn_start)
        sidebar_layout.addLayout(btn_layout)
        
        sidebar_layout.addSpacing(10)
        hr = QFrame()
        hr.setFrameShape(QFrame.HLine)
        hr.setStyleSheet("color: #444;")
        sidebar_layout.addWidget(hr)

        # 2. Angle Controls (Placeholder)
        grp_angle = QGroupBox("ANGLE OF INSONATION (\u03b8)")
        grp_angle.setStyleSheet("QGroupBox { font-weight: bold; color: #888; border: 1px solid #333; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        angle_layout = QVBoxLayout()
        
        angle_btn_layout = QHBoxLayout()
        self.angle_group = QButtonGroup(self)
        self.angle_group.setExclusive(True)
        
        for angle in ["30\u00b0", "60\u00b0", "75\u00b0"]:
            btn = QPushButton(angle)
            btn.setCheckable(True)
            if "60" in angle:
                btn.setChecked(True)
            
            # Styling for clickable buttons
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333; 
                    color: #aaa; 
                    border: 1px solid #444; 
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:checked {
                    background-color: #00e5ff;
                    color: #000;
                    font-weight: bold;
                    border: 1px solid #00e5ff;
                }
                QPushButton:hover {
                    background-color: #444;
                }
            """)
            
            self.angle_group.addButton(btn)
            angle_btn_layout.addWidget(btn)
        
        angle_layout.addLayout(angle_btn_layout)
        lbl_angle_note = QLabel("Future Implementation: Beam Steering")
        lbl_angle_note.setStyleSheet("color: #555; font-size: 11px; font-style: italic;")
        angle_layout.addWidget(lbl_angle_note)
        grp_angle.setLayout(angle_layout)
        sidebar_layout.addWidget(grp_angle)

        # 3. Quantitative Analysis (Placeholder)
        grp_metrics = QGroupBox("QUANTITATIVE ANALYSIS")
        grp_metrics.setStyleSheet("QGroupBox { font-weight: bold; color: #888; border: 1px solid #333; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        metrics_layout = QVBoxLayout()
        
        metrics_layout.addWidget(self.create_metric_placeholder("TRUE Vmax:", "-- m/s"))
        metrics_layout.addWidget(self.create_metric_placeholder("MEASURED Vmax:", "-- m/s"))
        metrics_layout.addWidget(self.create_metric_placeholder("RELATIVE ERROR:", "-- %"))
        
        grp_metrics.setLayout(metrics_layout)
        sidebar_layout.addWidget(grp_metrics)

        sidebar_layout.addStretch()
        
        # Quit Button
        self.btn_quit = QPushButton("EXIT SYSTEM")
        self.btn_quit.setCursor(Qt.PointingHandCursor)
        self.btn_quit.setFixedHeight(45)
        self.btn_quit.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #aaa;
                border-radius: 4px;
                border: 1px solid #444;
            }
            QPushButton:hover {
                background-color: #444;
                color: #fff;
            }
        """)
        self.btn_quit.clicked.connect(self.close)
        sidebar_layout.addWidget(self.btn_quit)
        
        main_layout.addWidget(sidebar)
        
        # --- RIGHT VISUALIZATION AREA ---
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Matplotlib Figure for all plots (using subplots)
        self.fig = Figure(facecolor='#121212') 
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: #121212; border: 1px solid #333;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.canvas)
        
        main_layout.addWidget(content_area)
        
        self.init_plots()
        self.simulation_running = False

    def create_metric_placeholder(self, label, value):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0,0,0,0)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #666;")
        val = QLabel(value)
        l.addWidget(lbl)
        l.addStretch()
        l.addWidget(val)
        return w

    def init_plots(self):
        """Initialize all plots: Flow (Active), RF (Blank), Spectrum (Blank)."""
        # Layout:
        # Top: Laminar Flow (Span 2 cols)
        # Bottom Left: RF Data
        # Bottom Right: Spectrum
        
        self.ax_flow = self.fig.add_subplot(2, 1, 1) # Top Half
        self.ax_rf   = self.fig.add_subplot(2, 2, 3) # Bottom Left
        self.ax_spec = self.fig.add_subplot(2, 2, 4) # Bottom Right
        
        self.fig.subplots_adjust(hspace=0.4, wspace=0.25, top=0.92, bottom=0.08, left=0.08, right=0.95)

        # 1. Laminar Flow (ACTIVE)
        self.ax_flow.set_facecolor('#000000') 
        self.ax_flow.set_title("LAMINAR FLOW SIMULATION (Blood Flow Model)", color='#e0e0e0', fontsize=11, loc='left', pad=10, weight='bold')
        self.ax_flow.set_xlabel("Longitudinal Position [m]", color='#666', fontsize=9)
        self.ax_flow.set_ylabel("Radial Position [m]", color='#666', fontsize=9)
        
        forAE = self.ax_flow.spines.values()
        for spine in forAE: spine.set_color('#333')
        self.ax_flow.tick_params(axis='both', colors='#666', labelsize=8)
        self.ax_flow.grid(True, color='#222', linestyle=':', linewidth=0.5)
        
        # Vessel Walls
        self.ax_flow.axhline(config.VESSEL_RADIUS, color='#555', linewidth=2, linestyle='-')
        self.ax_flow.axhline(-config.VESSEL_RADIUS, color='#555', linewidth=2, linestyle='-')
        self.ax_flow.set_xlim(-config.VESSEL_LENGTH/2, config.VESSEL_LENGTH/2)
        self.ax_flow.set_ylim(-config.VESSEL_RADIUS*2.5, config.VESSEL_RADIUS*2.5) # More vertical space
        
        # Red Scatter
        self.scatter_plot = self.ax_flow.scatter([], [], s=12, c='#ff1744', alpha=0.5, edgecolors='none')

        # 2. RF Data Stream (BLANK)
        self.setup_blank_axis(self.ax_rf, "RF DATA STREAM (Raw Signal)", "Time [s]", "Amplitude [V]")

        # 3. Doppler Spectrum (BLANK)
        self.setup_blank_axis(self.ax_spec, "DOPPLER SPECTRUM (STFT)", "Time [s]", "Velocity [m/s]")

        self.canvas.draw()

    def setup_blank_axis(self, ax, title, xlabel, ylabel):
        ax.set_facecolor('#121212')
        ax.set_title(title, color='#777', fontsize=10, loc='left', weight='bold')
        ax.set_xlabel(xlabel, color='#555', fontsize=8)
        ax.set_ylabel(ylabel, color='#555', fontsize=8)
        for spine in ax.spines.values():
            spine.set_color('#333')
        ax.tick_params(colors='#555', labelsize=7)
        ax.grid(True, color='#222', linestyle='-', linewidth=0.5)
        
        # Add "Empty" text
        ax.text(0.5, 0.5, "NO SIGNAL\n(Awaiting Implementation)", 
                transform=ax.transAxes, color='#333', ha='center', va='center', fontsize=9)

    def toggle_simulation(self):
        if not self.simulation_running:
            self.controller.start_simulation()
            self.simulation_running = True
            self.btn_start.setText("STOP SIMULATION")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: #000;
                    border-radius: 4px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background-color: #ffb74d;
                }
            """)
        else:
            self.controller.stop_simulation()
            self.simulation_running = False
            self.btn_start.setText("START FLOW SIMULATION")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: #fff;
                    border-radius: 4px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background-color: #f44336;
                }
            """)

    @pyqtSlot(object, object, object)
    def update_flow_plot(self, x, y, z):
        """Updates the scatter plot with new positions."""
        if hasattr(self, 'scatter_plot'):
            self.scatter_plot.set_offsets(np.c_[x, y])
            self.canvas.draw_idle()

    @pyqtSlot(str)
    def handle_error(self, msg):
        self.simulation_running = False
        self.btn_start.setText("START FLOW SIMULATION")
        QMessageBox.critical(self, "System Error", f"Simulation Failed:\n{msg}")

    def closeEvent(self, event):
        """Ensure cleanup of artifacts on exit."""
        if self.controller:
            self.controller.stop_simulation()
        cleanup.clean_project_artifacts()
        event.accept()
