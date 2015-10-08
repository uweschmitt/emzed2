# encoding: utf-8
from __future__ import print_function, division

from PyQt4 import QtCore, QtGui

from _image_scaling_widget import ImageScalingWidget as _ImageScalingWidget


class ImageScalingWidget(_ImageScalingWidget):

    GAMMA_MIN = 0.05
    GAMMA_MAX = 4.0

    GAMMA_CHANGED = QtCore.pyqtSignal(float)
    USE_LOG_SCALE = QtCore.pyqtSignal(bool)
    IMIN_CHANGED = QtCore.pyqtSignal(float)
    IMAX_CHANGED = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super(ImageScalingWidget, self).__init__(parent)
        self.gamma = None
        self.overall_max_intensity = None
        self.setup()
        self.setEnabled(False)

    def set_max_intensity(self, imax):
        self.overall_max_intensity = imax
        self.current_imax = imax
        self.set_imax_input(imax)
        self.set_imax_slider(imax)
        self.setEnabled(True)

    def set_gamma(self, gamma):
        self.gamma = gamma
        pos = 100.0 * (self.gamma - self.GAMMA_MIN) / (self.GAMMA_MAX - self.GAMMA_MIN)
        self.gamma_slider.setSliderPosition(pos)

    def setup(self):
        self.setup_widgets()
        self.connect_signals()

    def setup_widgets(self):
        self.imax_input.setValidator(QtGui.QDoubleValidator())
        self.imin_input.setValidator(QtGui.QDoubleValidator())
        self.logarithmic_scale.setChecked(True)

        self.set_imin_input(0)
        self.set_imax_input(1000)

        self.imin_slider.setMinimum(0)
        self.imin_slider.setMaximum(100)
        self.imin_slider.setSliderPosition(0)

        self.imax_slider.setMinimum(0)
        self.imax_slider.setMaximum(100)
        self.imax_slider.setSliderPosition(0)

        self.gamma_slider.setMinimum(0)
        self.gamma_slider.setMaximum(100)

    def _set_intensity_field(self, field, value):
        fmt = "%.0f" if value < 100000 else "%.1e"
        field.setText(fmt % value)

    def set_imin_input(self, imin):
        self._set_intensity_field(self.imin_input, imin)
        self.IMIN_CHANGED.emit(imin)

    def set_imax_input(self, imax):
        self._set_intensity_field(self.imax_input, imax)
        self.IMAX_CHANGED.emit(imax)

    def connect_signals(self):

        def _create_slider_update_handler(input_field, set_input_field, set_slider):
            def handler():
                try:
                    value = float(input_field.text())
                except ValueError:
                    return

                # truncate value to range 0 .. self.overall_max_intensity:
                value = max(0, value)
                value = min(value, self.overall_max_intensity)
                # write back
                set_input_field(value)
                # set slider, we block because setting the slider would write back to the
                # input field:
                self.imin_slider.blockSignals(True)
                self.imax_slider.blockSignals(True)
                set_slider(value)
                self.imin_slider.blockSignals(False)
                self.imax_slider.blockSignals(False)
            return handler

        handler = _create_slider_update_handler(self.imin_input, self.set_imin_input,
                                                self.set_imin_slider)
        self.imin_input.editingFinished.connect(handler)

        handler = _create_slider_update_handler(self.imax_input, self.set_imax_input,
                                                self.set_imax_slider)
        self.imax_input.editingFinished.connect(handler)

        self.imin_slider.valueChanged.connect(self.update_imin_field)
        self.imax_slider.valueChanged.connect(self.update_imax_field)

        self.gamma_slider.valueChanged.connect(self.gamma_slider_changed)
        self.logarithmic_scale.stateChanged.connect(self.log_checkbox_changed)

    def update_imin_field(self, slider_value):
        value = self.from_slider_pos(slider_value, self.overall_max_intensity)
        self.set_imin_input(value)

    def update_imax_field(self, slider_value):
        value = self.from_slider_pos(slider_value, self.overall_max_intensity)
        self.set_imax_input(value)

    def gamma_slider_changed(self, pos):
        value = pos / 100 * (self.GAMMA_MAX - self.GAMMA_MIN) + self.GAMMA_MIN
        self.GAMMA_CHANGED.emit(value)

    def log_checkbox_changed(self, value):
        self.USE_LOG_SCALE.emit(bool(value))

    def update_imin_slider(self):
        try:
            imin = float(self.imin_input.text())
        except ValueError:
            return
        imin = max(0, imin)
        imin = min(imin, self.overall_max_intensity)
        self.set_imin_input(imin)
        self.set_imin_slider(imin)

    def to_slider_pos(self, val, maxval):
        return (val / maxval) ** 0.3333 * 100.0

    def from_slider_pos(self, pos, maxval):
        return (pos / 100.0) ** 3 * maxval

    def set_imin_slider(self, imin):
        pos = self.to_slider_pos(imin, self.overall_max_intensity)
        self.imin_slider.setSliderPosition(pos)

    def set_imax_slider(self, imax):
        pos = self.to_slider_pos(imax, self.overall_max_intensity)
        self.imax_slider.setSliderPosition(pos)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = ImageScalingWidget()
    widget.set_max_intensity(1000000)
    widget.show()
    sys.exit(app.exec_())
