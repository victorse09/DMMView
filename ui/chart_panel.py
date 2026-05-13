"""
DMMView - Chart Panel
Matplotlib-based charts: temporal line chart and histogram.
Supports export to PNG, JPG, and PDF.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QSpinBox, QComboBox, QFrame, QFileDialog,
)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, AutoDateLocator
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
from ui.styles import COLORS


class TimeChart(FigureCanvas):
    """Real-time temporal line chart using Matplotlib."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor=COLORS['chart_bg'])
        super().__init__(self.fig)

        self.ax = self.fig.add_subplot(111)
        self._setup_axes()
        self._times = []
        self._values = []
        self._line = None
        self.fig.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _setup_axes(self):
        """Configure axes with dark theme."""
        ax = self.ax
        ax.set_facecolor(COLORS['chart_bg'])
        ax.tick_params(colors=COLORS['chart_text'], labelsize=9)
        ax.spines['bottom'].set_color(COLORS['border_dark'])
        ax.spines['left'].set_color(COLORS['border_dark'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, color=COLORS['chart_grid'], alpha=0.3, linestyle='--')
        ax.set_xlabel('Tiempo', color=COLORS['chart_text'], fontsize=10)
        ax.set_ylabel('Valor', color=COLORS['chart_text'], fontsize=10)
        ax.set_title('Medición en Tiempo Real', color=COLORS['text_primary'],
                     fontsize=13, fontweight='bold', pad=10)
        self.fig.tight_layout(pad=2)

        self.annot = self.ax.annotate("", xy=(0,0), xytext=(-20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc=COLORS['bg_card'], ec=COLORS['border_dark']),
                            arrowprops=dict(arrowstyle="->", color=COLORS['accent_orange']))
        self.annot.set_color(COLORS['text_primary'])
        self.annot.set_visible(False)

    def _on_hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.ax and self._line:
            cont, ind = self._line.contains(event)
            if cont:
                pos = self._line.get_xydata()[ind["ind"][0]]
                self.annot.xy = pos
                val = pos[1]
                self.annot.set_text(f"Valor: {val:.4g}")
                self.annot.set_visible(True)
                self.fig.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.fig.canvas.draw_idle()
        else:
            if vis:
                self.annot.set_visible(False)
                self.fig.canvas.draw_idle()

    def add_point(self, timestamp, value):
        """Add a data point to the chart."""
        self._times.append(timestamp)
        self._values.append(value)

    def refresh_chart(self, max_points=500):
        """Redraw the chart with current data."""
        self.ax.clear()
        self._setup_axes()

        if not self._times:
            self.draw()
            return

        # Limit displayed points
        times = self._times[-max_points:]
        values = self._values[-max_points:]

        # Plot line
        lines = self.ax.plot(times, values, color=COLORS['chart_line'],
                    linewidth=1.5, alpha=0.9)
        if lines:
            self._line = lines[0]

        # Fill under curve
        self.ax.fill_between(times, values, alpha=0.08,
                            color=COLORS['chart_line'])

        # Format X axis
        if len(times) > 1:
            self.ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
            self.ax.xaxis.set_major_locator(AutoDateLocator())
            self.fig.autofmt_xdate(rotation=30)

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.tight_layout(pad=2)
        self.draw()

    def clear_data(self):
        """Clear all chart data."""
        self._times.clear()
        self._values.clear()
        self.ax.clear()
        self._setup_axes()
        self.draw()

    def save_image(self, filepath, dpi=150):
        """Save chart to an image file (PNG, JPG, PDF)."""
        self.fig.savefig(filepath, dpi=dpi, facecolor=self.fig.get_facecolor(),
                        edgecolor='none', bbox_inches='tight')


class HistogramChart(FigureCanvas):
    """Histogram distribution chart using Matplotlib."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor=COLORS['chart_bg'])
        super().__init__(self.fig)

        self.ax = self.fig.add_subplot(111)
        self._setup_axes()
        self._values = []

    def _setup_axes(self):
        """Configure axes with dark theme."""
        ax = self.ax
        ax.set_facecolor(COLORS['chart_bg'])
        ax.tick_params(colors=COLORS['chart_text'], labelsize=9)
        ax.spines['bottom'].set_color(COLORS['border_dark'])
        ax.spines['left'].set_color(COLORS['border_dark'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, axis='y', color=COLORS['chart_grid'], alpha=0.3, linestyle='--')
        ax.set_xlabel('Valor', color=COLORS['chart_text'], fontsize=10)
        ax.set_ylabel('Frecuencia', color=COLORS['chart_text'], fontsize=10)
        ax.set_title('Distribución de Mediciones', color=COLORS['text_primary'],
                     fontsize=13, fontweight='bold', pad=10)
        self.fig.tight_layout(pad=2)

    def update_histogram(self, values, bins=30):
        """Update histogram with new data."""
        self.ax.clear()
        self._setup_axes()

        if not values:
            self.draw()
            return

        self._values = values

        # Plot histogram with gradient-like coloring
        n, bin_edges, patches = self.ax.hist(
            values, bins=bins, edgecolor=COLORS['bg_darkest'],
            linewidth=0.5, alpha=0.85, color=COLORS['chart_hist'],
        )

        # Color bars by position
        max_n = max(n) if max(n) > 0 else 1
        for patch, count in zip(patches, n):
            intensity = 0.3 + 0.7 * (count / max_n)
            color = matplotlib.colors.to_rgba(COLORS['chart_hist'], intensity)
            patch.set_facecolor(color)

        # Add mean line
        if values:
            mean_val = sum(values) / len(values)
            self.ax.axvline(mean_val, color=COLORS['accent_orange'],
                           linestyle='--', linewidth=2, alpha=0.8,
                           label=f'Media: {mean_val:.4g}')
            self.ax.legend(facecolor=COLORS['bg_card'],
                          edgecolor=COLORS['border_dark'],
                          labelcolor=COLORS['text_primary'],
                          fontsize=9)

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.tight_layout(pad=2)
        self.draw()

    def clear_data(self):
        """Clear histogram data."""
        self._values.clear()
        self.ax.clear()
        self._setup_axes()
        self.draw()

    def save_image(self, filepath, dpi=150):
        """Save histogram to an image file (PNG, JPG, PDF)."""
        self.fig.savefig(filepath, dpi=dpi, facecolor=self.fig.get_facecolor(),
                        edgecolor='none', bbox_inches='tight')


class ChartPanel(QWidget):
    """Chart panel with tabs for time series and histogram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Controls ─────────────────────────────────────────────
        controls = QFrame()
        controls.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_dark']};
                border-radius: 8px;
            }}
        """)
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(12, 8, 12, 8)

        ctrl_layout.addWidget(QLabel("Puntos m\u00e1ximos:"))
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(50, 10000)
        self.max_points_spin.setValue(500)
        self.max_points_spin.setSingleStep(50)
        ctrl_layout.addWidget(self.max_points_spin)

        ctrl_layout.addWidget(QLabel("Divisiones Histograma:"))
        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(5, 200)
        self.bins_spin.setValue(30)
        ctrl_layout.addWidget(self.bins_spin)

        ctrl_layout.addStretch()

        self.refresh_btn = QPushButton("\u27F3 Actualizar")
        self.refresh_btn.setProperty("cssClass", "primary")
        self.refresh_btn.setStyleSheet("padding: 5px 12px; font-size: 11px; min-height: 14px;")
        ctrl_layout.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("\u2716 Limpiar")
        self.clear_btn.setProperty("cssClass", "danger")
        self.clear_btn.setStyleSheet("padding: 5px 12px; font-size: 11px; min-height: 14px;")
        ctrl_layout.addWidget(self.clear_btn)

        layout.addWidget(controls)

        # ── Export Controls ───────────────────────────────────────
        export_frame = QFrame()
        export_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_dark']};
                border-radius: 8px;
            }}
        """)
        export_layout = QHBoxLayout(export_frame)
        export_layout.setContentsMargins(12, 6, 12, 6)

        export_layout.addWidget(QLabel("Exportar gr\u00e1fico actual:"))
        export_layout.addStretch()

        self.export_png_btn = QPushButton("PNG")
        self.export_png_btn.setToolTip("Exportar como imagen PNG")
        self.export_png_btn.setStyleSheet("padding: 4px 8px; font-size: 10px; min-height: 12px; min-width: 40px;")
        self.export_png_btn.clicked.connect(lambda: self._export_chart("png"))
        export_layout.addWidget(self.export_png_btn)

        self.export_jpg_btn = QPushButton("JPG")
        self.export_jpg_btn.setToolTip("Exportar como imagen JPEG")
        self.export_jpg_btn.setStyleSheet("padding: 4px 8px; font-size: 10px; min-height: 12px; min-width: 40px;")
        self.export_jpg_btn.clicked.connect(lambda: self._export_chart("jpg"))
        export_layout.addWidget(self.export_jpg_btn)

        self.export_pdf_btn = QPushButton("PDF")
        self.export_pdf_btn.setToolTip("Exportar como documento PDF")
        self.export_pdf_btn.setStyleSheet("padding: 4px 8px; font-size: 10px; min-height: 12px; min-width: 40px;")
        self.export_pdf_btn.clicked.connect(lambda: self._export_chart("pdf"))
        export_layout.addWidget(self.export_pdf_btn)

        # DPI selector
        export_layout.addWidget(QLabel("  DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSingleStep(50)
        export_layout.addWidget(self.dpi_spin)

        layout.addWidget(export_frame)

        # ── Tab Widget ───────────────────────────────────────────
        self.tabs = QTabWidget()

        # Time chart tab
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_chart = TimeChart()
        self.time_toolbar = NavigationToolbar2QT(self.time_chart, self)
        self._translate_toolbar(self.time_toolbar)
        time_layout.addWidget(self.time_toolbar)
        time_layout.addWidget(self.time_chart)
        self.tabs.addTab(time_widget, "\u223F Gr\u00e1fico Temporal")

        # Histogram tab
        hist_widget = QWidget()
        hist_layout = QVBoxLayout(hist_widget)
        hist_layout.setContentsMargins(0, 0, 0, 0)
        self.histogram = HistogramChart()
        self.hist_toolbar = NavigationToolbar2QT(self.histogram, self)
        self._translate_toolbar(self.hist_toolbar)
        hist_layout.addWidget(self.hist_toolbar)
        hist_layout.addWidget(self.histogram)
        self.tabs.addTab(hist_widget, "\u2587 Histograma")

        layout.addWidget(self.tabs, 1)

        # Connect signals
        self.refresh_btn.clicked.connect(self._refresh_all)
        self.clear_btn.clicked.connect(self._clear_all)

    def _translate_toolbar(self, toolbar):
        """Translate Matplotlib toolbar tooltips to Spanish."""
        translations = {
            'Home': 'Inicio',
            'Back': 'Atr\u00e1s',
            'Forward': 'Adelante',
            'Pan': 'Panor\u00e1mica',
            'Zoom': 'Zoom',
            'Subplots': 'Configurar ejes',
            'Customize': 'Personalizar',
            'Save': 'Guardar',
        }
        for action in toolbar.actions():
            if action.text() in translations:
                action.setToolTip(translations[action.text()])
            elif action.toolTip() in translations: # Some backends use tooltip directly
                action.setToolTip(translations[action.toolTip()])

    def add_data_point(self, timestamp, value):
        """Add a data point (updates time chart)."""
        self.time_chart.add_point(timestamp, value)

    def refresh_time_chart(self):
        """Refresh the time chart display."""
        self.time_chart.refresh_chart(self.max_points_spin.value())

    def refresh_histogram(self, values=None):
        """Refresh the histogram with provided values."""
        if values is None:
            values = self.time_chart._values
        self.histogram.update_histogram(values, self.bins_spin.value())

    def _refresh_all(self):
        """Refresh both charts."""
        self.refresh_time_chart()
        self.refresh_histogram()

    def _clear_all(self):
        """Clear all chart data."""
        self.time_chart.clear_data()
        self.histogram.clear_data()

    def _export_chart(self, fmt):
        """Export the currently visible chart to an image file."""
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            chart = self.time_chart
            default_name = f"grafico_temporal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            chart = self.histogram
            default_name = f"histograma_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filters = {
            'png': "Imagen PNG (*.png)",
            'jpg': "Imagen JPEG (*.jpg *.jpeg)",
            'pdf': "Documento PDF (*.pdf)",
        }
        file_filter = filters.get(fmt, filters['png'])

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Gr\u00e1fico",
            f"{default_name}.{fmt}",
            f"{file_filter};;Todos los archivos (*)"
        )

        if filepath:
            try:
                dpi = self.dpi_spin.value()
                chart.save_image(filepath, dpi=dpi)
                parent = self.window()
                if hasattr(parent, 'statusbar'):
                    parent.statusbar.showMessage(
                        f"\u2713 Gr\u00e1fico exportado: {filepath}", 5000)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error",
                    f"Error exportando gr\u00e1fico:\n{e}")

    def export_current_chart(self, fmt='png'):
        """Public method to trigger chart export from menus."""
        self._export_chart(fmt)
