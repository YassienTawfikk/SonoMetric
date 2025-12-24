import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QMessageBox, QGroupBox,
                             QSizePolicy, QDial)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QCloseEvent, QFont
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.utils import config, cleanup
from src.controller import DopplerController
from matplotlib.ticker import MultipleLocator


# --- Main Window (GUI) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SonoMetric: Laminar Flow Simulation with Pulsed Doppler")
        self.resize(1280, 900)

        # Controller Init
        self.controller = DopplerController()
        self.controller.flow_update.connect(self.update_flow_plot)
        self.controller.rf_update.connect(self.update_rf_plot)
        self.controller.spectrum_update.connect(self.update_spectrum_plot)
        self.controller.metrics_update.connect(self.update_metrics)
        self.controller.error_occurred.connect(self.handle_error)

        # Metrics storage
        self.v_true = 0.0
        self.v_measured = 0.0
        self.error_percent = 0.0

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
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
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

        # 2. Angle Controls (Continuous Slider)
        grp_angle = QGroupBox("ANGLE OF INSONATION (θ)")
        grp_angle.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #00e5ff; border: 1px solid #333; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        angle_layout = QVBoxLayout()

        # Label to show current angle
        self.lbl_angle_value = QLabel(f"{config.DEFAULT_ANGLE}°")
        self.lbl_angle_value.setAlignment(Qt.AlignCenter)
        self.lbl_angle_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 5px;")
        angle_layout.addWidget(self.lbl_angle_value)

        # Wheel (QDial)
        self.dial_angle = QDial()
        self.dial_angle.setMinimum(config.MIN_ANGLE)
        self.dial_angle.setMaximum(config.MAX_ANGLE)
        self.dial_angle.setValue(config.DEFAULT_ANGLE)
        self.dial_angle.setNotchesVisible(True)
        self.dial_angle.setWrapping(False)
        self.dial_angle.setCursor(Qt.PointingHandCursor)
        self.dial_angle.setFixedHeight(120)  # Make it big enough to look like a wheel
        self.dial_angle.setStyleSheet("""
            QDial {
                background-color: #222;
                color: #00e5ff;
            }
        """)

        # Connect signals
        self.dial_angle.valueChanged.connect(self.update_angle_label)
        self.dial_angle.sliderReleased.connect(self.on_angle_slider_released)

        angle_layout.addWidget(self.dial_angle)

        lbl_angle_note = QLabel("✓ Rotate wheel to steer beam")
        lbl_angle_note.setStyleSheet("color: #4caf50; font-size: 11px; font-style: italic; margin-top: 5px;")
        angle_layout.addWidget(lbl_angle_note)

        grp_angle.setLayout(angle_layout)
        sidebar_layout.addWidget(grp_angle)

        # 3. Quantitative Analysis (NOW LIVE)
        grp_metrics = QGroupBox("QUANTITATIVE ANALYSIS")
        grp_metrics.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #00e5ff; border: 1px solid #333; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        metrics_layout = QVBoxLayout()

        self.lbl_v_true = self.create_metric_widget("TRUE Vmax:", "-- m/s")
        self.lbl_v_measured = self.create_metric_widget("MEASURED Vmax:", "-- m/s")
        self.lbl_error = self.create_metric_widget("RELATIVE ERROR:", "-- %")

        metrics_layout.addWidget(self.lbl_v_true)
        metrics_layout.addWidget(self.lbl_v_measured)
        metrics_layout.addWidget(self.lbl_error)

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

        # Sidebar added later to appear on right
        # main_layout.addWidget(sidebar)

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
        main_layout.addWidget(sidebar)  # Add sidebar last (Right side)

        self.init_plots()
        self.simulation_running = False

    def create_metric_widget(self, label, initial_value):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 5, 0, 5)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #888; font-size: 12px;")
        val = QLabel(initial_value)
        val.setStyleSheet("color: #00e5ff; font-size: 12px; font-weight: bold;")
        val.setObjectName("value_label")
        l.addWidget(lbl)
        l.addStretch()
        l.addWidget(val)
        return w

    def init_plots(self):
        """Initialize all plots: Flow, RF, Spectrum."""
        # Layout: Top: Flow (span 2 cols), Bottom: RF (left), Spectrum (right)

        self.ax_flow = self.fig.add_subplot(2, 1, 1)  # Top Half
        self.ax_rf = self.fig.add_subplot(2, 2, 3)  # Bottom Left
        self.ax_spec = self.fig.add_subplot(2, 2, 4)  # Bottom Right

        self.fig.subplots_adjust(hspace=0.4, wspace=0.25, top=0.92, bottom=0.08, left=0.08, right=0.95)

        # 1. Laminar Flow
        self.ax_flow.set_facecolor('#000000')
        self.ax_flow.set_title("LAMINAR FLOW SIMULATION (Blood Flow Model)", color='#e0e0e0', fontsize=11, loc='left',
                               pad=10, weight='bold')
        self.ax_flow.set_xlabel("Longitudinal Position [m]", color='#666', fontsize=9)
        self.ax_flow.set_ylabel("Radial Position [m]", color='#666', fontsize=9)

        for spine in self.ax_flow.spines.values():
            spine.set_color('#333')
        self.ax_flow.tick_params(axis='both', colors='#666', labelsize=8)
        self.ax_flow.grid(True, color='#222', linestyle=':', linewidth=0.5)

        # Vessel Walls
        self.ax_flow.axhline(config.VESSEL_RADIUS, color='#555', linewidth=2, linestyle='-')
        self.ax_flow.axhline(-config.VESSEL_RADIUS, color='#555', linewidth=2, linestyle='-')
        self.ax_flow.set_xlim(-config.VESSEL_LENGTH / 2, config.VESSEL_LENGTH / 2)
        self.ax_flow.set_ylim(-config.VESSEL_RADIUS * 2.5, config.VESSEL_RADIUS * 2.5)

        self.scatter_plot = self.ax_flow.scatter([], [], s=12, c='#ff1744', alpha=0.5, edgecolors='none')

        # 2. RF Data Stream
        self.setup_rf_axis()

        # 3. Doppler Spectrum
        self.setup_spectrum_axis()

        self.canvas.draw()

    def setup_rf_axis(self):
        """Setup RF data plot."""
        self.ax_rf.set_facecolor('#000000')
        self.ax_rf.set_title("I/Q BASEBAND SIGNAL", color='#e0e0e0', fontsize=10, loc='left', weight='bold')
        self.ax_rf.set_xlabel("Time [s]", color='#666', fontsize=8)
        self.ax_rf.set_ylabel("Amplitude", color='#666', fontsize=8)
        for spine in self.ax_rf.spines.values():
            spine.set_color('#333')
        self.ax_rf.tick_params(colors='#666', labelsize=7)
        self.ax_rf.grid(True, color='#222', linestyle='-', linewidth=0.5)

        # Initialize empty line plots
        self.line_rf_i, = self.ax_rf.plot([], [], 'c-', linewidth=0.8, alpha=0.7, label='I')
        self.line_rf_q, = self.ax_rf.plot([], [], 'm-', linewidth=0.8, alpha=0.7, label='Q')
        self.ax_rf.legend(loc='upper right', fontsize=7, framealpha=0.3)

    def setup_spectrum_axis(self):
        """Setup Doppler spectrogram plot."""
        self.ax_spec.set_facecolor('#000000')
        self.ax_spec.set_title(
            "DOPPLER SPECTRUM (STFT)",
            color='#e0e0e0',
            fontsize=10,
            loc='left',
            weight='bold'
        )
        self.ax_spec.set_xlabel("Time [s]", color='#666', fontsize=8)
        self.ax_spec.set_ylabel("Velocity [m/s]", color='#666', fontsize=8)

        # Force Y-axis to step by 1
        self.ax_spec.yaxis.set_major_locator(MultipleLocator(0.1))

        for spine in self.ax_spec.spines.values():
            spine.set_color('#333')

        self.ax_spec.tick_params(colors='#666', labelsize=7)
        self.spectrum_image = None

        # 🔴 PyQt part people forget
        self.canvas.draw_idle()

    def toggle_simulation(self):
        if not self.simulation_running:
            current_angle = self.controller.get_current_angle()
            self.controller.start_simulation(angle=current_angle)
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

    def change_angle(self, angle):
        """Handle angle change."""
        self.controller.change_angle(angle)

    def update_angle_label(self, value):
        """Update the label text and simulation as dial turns."""
        self.lbl_angle_value.setText(f"{value}°")
        # Live update
        if hasattr(self, 'controller'):
            self.controller.update_angle_live(value)

    def on_angle_slider_released(self):
        """Final commit of angle (optional, improves clarity)."""
        # With live update, we don't strictly need to do anything here,
        # but we can ensure everything is synced.
        pass

    @pyqtSlot(object, object, object)
    def update_flow_plot(self, x, y, z):
        """Updates the scatter plot with new positions. OPTIMIZED."""
        if hasattr(self, 'scatter_plot'):
            # Downsample for faster rendering (every 2nd point)
            offsets = np.c_[x[::2], y[::2]]
            self.scatter_plot.set_offsets(offsets)

            # Use draw_idle instead of manual blit to ensure background clearing
            self.scatter_plot.set_offsets(offsets)
            self.canvas.draw_idle()

    @pyqtSlot(object, object)
    def update_rf_plot(self, rf_signal, time_axis):
        """Update RF signal plot. OPTIMIZED."""
        if len(rf_signal) == 0:
            return

        # Downsample if signal is too long
        downsample_factor = max(1, len(rf_signal) // 1000)
        rf_signal_ds = rf_signal[::downsample_factor]
        time_axis_ds = time_axis[::downsample_factor]

        # Extract I and Q components
        i_signal = np.real(rf_signal_ds)
        q_signal = np.imag(rf_signal_ds)

        # Update line data
        self.line_rf_i.set_data(time_axis_ds, i_signal)
        self.line_rf_q.set_data(time_axis_ds, q_signal)

        # Only rescale if needed (check bounds)
        xlim = self.ax_rf.get_xlim()
        if time_axis_ds[0] < xlim[0] or time_axis_ds[-1] > xlim[1]:
            self.ax_rf.set_xlim(time_axis_ds[0], time_axis_ds[-1])

        ylim = self.ax_rf.get_ylim()
        ymin, ymax = min(i_signal.min(), q_signal.min()), max(i_signal.max(), q_signal.max())
        if ymin < ylim[0] or ymax > ylim[1]:
            margin = (ymax - ymin) * 0.1
            self.ax_rf.set_ylim(ymin - margin, ymax + margin)

        # Partial redraw
        self.canvas.draw_idle()

    @pyqtSlot(object, object, object)
    def update_spectrum_plot(self, spec_time, velocities, spec_power):
        """Update Doppler spectrogram. OPTIMIZED."""
        if len(spec_time) == 0 or len(velocities) == 0 or spec_power.size == 0:
            return

        # Convert to dB scale with proper floor
        spec_db = 10 * np.log10(spec_power + 1e-12)

        # Focus on physiological velocity range (-1 to +1 m/s)
        vel_mask = (velocities >= -1.0) & (velocities <= 1.0)
        if np.sum(vel_mask) == 0:
            return

        velocities_zoom = velocities[vel_mask]
        spec_db_zoom = spec_db[vel_mask, :]

        # Downsample spectrogram if too large
        if spec_db_zoom.shape[1] > 200:
            step = spec_db_zoom.shape[1] // 200
            spec_db_zoom = spec_db_zoom[:, ::step]
            spec_time = spec_time[::step]

        # Create extent for imshow
        extent = [spec_time[0], spec_time[-1], velocities_zoom[0], velocities_zoom[-1]]

        # Adaptive contrast
        vmin = np.percentile(spec_db_zoom, 10)
        vmax = np.percentile(spec_db_zoom, 99)

        # Update or create image
        if self.spectrum_image is None:
            self.spectrum_image = self.ax_spec.imshow(
                spec_db_zoom, aspect='auto', origin='lower', extent=extent,
                cmap='hot', interpolation='nearest', vmin=vmin, vmax=vmax
            )
        else:
            # Just update data (MUCH faster than recreating)
            self.spectrum_image.set_data(spec_db_zoom)
            self.spectrum_image.set_extent(extent)
            self.spectrum_image.set_clim(vmin, vmax)

        self.ax_spec.set_xlim(spec_time[0], spec_time[-1])
        self.ax_spec.set_ylim(-0.8, 0.8)

        self.canvas.draw_idle()

    @pyqtSlot(float, float, float)
    def update_metrics(self, v_true, v_measured, error):
        """Update quantitative metrics display."""
        self.v_true = v_true
        self.v_measured = v_measured
        self.error_percent = error

        # Update labels
        val_true = self.lbl_v_true.findChild(QLabel, "value_label")
        val_measured = self.lbl_v_measured.findChild(QLabel, "value_label")
        val_error = self.lbl_error.findChild(QLabel, "value_label")

        if val_true:
            val_true.setText(f"{v_true:.3f} m/s")
        if val_measured:
            val_measured.setText(f"{v_measured:.3f} m/s")
        if val_error:
            val_error.setText(f"{error:.2f} %")
            # Color code error
            if error < 5:
                val_error.setStyleSheet("color: #4caf50; font-size: 12px; font-weight: bold;")
            elif error < 15:
                val_error.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
            else:
                val_error.setStyleSheet("color: #f44336; font-size: 12px; font-weight: bold;")

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
