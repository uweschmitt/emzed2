# encoding: utf-8
from __future__ import print_function, division

from PyQt4 import QtCore, QtGui

from _image_scaling_widget import _ImageScalingWidget


class ImageScalingWidget(_ImageScalingWidget):

    GAMMA_MIN = 0.05
    GAMMA_MAX = 4.0

    GAMMA_CHANGED = QtCore.pyqtSignal(float)
    USE_LOG_SCALE = QtCore.pyqtSignal(bool)
    IMIN_CHANGED = QtCore.pyqtSignal(float)
    IMAX_CHANGED = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super(ImageScalingWidget, self).__init__(parent)
        self._gamma = None
        self._overall_max_intensity = None
        self._setup()
        self.setEnabled(False)

    def set_max_intensity(self, imax):
        self._overall_max_intensity = imax
        self.current_imax = imax
        self._set_imax_input(imax)
        self._set_imax_slider(imax)
        self._enable_widget_if_data_is_complete()

    def set_gamma(self, gamma):
        self._gamma = gamma
        pos = 100.0 * (self._gamma - self.GAMMA_MIN) / (self.GAMMA_MAX - self.GAMMA_MIN)
        self._gamma_slider.setSliderPosition(pos)
        self._enable_widget_if_data_is_complete()

    def _enable_widget_if_data_is_complete(self):
        self.setEnabled(self._gamma is not None and self._overall_max_intensity is not None)

    def _setup(self):
        self._setup_widgets()
        self._connect_signals()

    def _setup_widgets(self):
        self._imax_input.setValidator(QtGui.QDoubleValidator())
        self._imin_input.setValidator(QtGui.QDoubleValidator())
        self._logarithmic_scale.setChecked(True)

        self._set_imin_input(0)
        self._set_imax_input(1000)

        self._imin_slider.setMinimum(0)
        self._imin_slider.setMaximum(100)
        self._imin_slider.setSliderPosition(0)

        self._imax_slider.setMinimum(0)
        self._imax_slider.setMaximum(100)
        self._imax_slider.setSliderPosition(0)

        self._gamma_slider.setMinimum(0)
        self._gamma_slider.setMaximum(100)

    def _set_intensity_field(self, field, value):
        fmt = "%f" if value < 100000 else "%e"
        field.setText(fmt % value)

    def _set_imin_input(self, imin):
        self._set_intensity_field(self._imin_input, imin)
        self.IMIN_CHANGED.emit(imin)

    def _set_imax_input(self, imax):
        self._set_intensity_field(self._imax_input, imax)
        self.IMAX_CHANGED.emit(imax)

    def _connect_signals(self):

        def _create_slider_update_handler(input_field, set_input_field, set_slider):
            def handler():
                try:
                    value = float(input_field.text())
                except ValueError:
                    return

                # truncate value to range 0 .. self._overall_max_intensity:
                value = max(0, value)
                value = min(value, self._overall_max_intensity)
                set_input_field(value)
                # set slider, we block because setting the slider would write back to the
                # input field:
                self._imin_slider.blockSignals(True)
                self._imax_slider.blockSignals(True)
                set_slider(value)
                self._imin_slider.blockSignals(False)
                self._imax_slider.blockSignals(False)
            return handler

        handler = _create_slider_update_handler(self._imin_input, self._set_imin_input,
                                                self._set_imin_slider)
        self._imin_input.editingFinished.connect(handler)

        handler = _create_slider_update_handler(self._imax_input, self._set_imax_input,
                                                self._set_imax_slider)
        self._imax_input.editingFinished.connect(handler)

        self._imin_slider.valueChanged.connect(self._update_imin_field)
        self._imax_slider.valueChanged.connect(self._update_imax_field)

        self._gamma_slider.valueChanged.connect(self._gamma_slider_changed)
        self._logarithmic_scale.stateChanged.connect(self._log_checkbox_changed)

    def _update_imin_field(self, slider_value):
        value = self._from_slider_pos(slider_value, self._overall_max_intensity)
        self._set_imin_input(value)

    def _update_imax_field(self, slider_value):
        value = self._from_slider_pos(slider_value, self._overall_max_intensity)
        self._set_imax_input(value)

    def _gamma_slider_changed(self, pos):
        value = pos / 100 * (self.GAMMA_MAX - self.GAMMA_MIN) + self.GAMMA_MIN
        self.GAMMA_CHANGED.emit(value)

    def _log_checkbox_changed(self, value):
        self.USE_LOG_SCALE.emit(bool(value))

    def _to_slider_pos(self, val, maxval):
        return (val / maxval) ** 0.3333 * 100.0

    def _from_slider_pos(self, pos, maxval):
        return (pos / 100.0) ** 3 * maxval

    def _set_imin_slider(self, imin):
        pos = self._to_slider_pos(imin, self._overall_max_intensity)
        self._imin_slider.setSliderPosition(pos)

    def _set_imax_slider(self, imax):
        pos = self._to_slider_pos(imax, self._overall_max_intensity)
        self._imax_slider.setSliderPosition(pos)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = ImageScalingWidget()
    widget.set_max_intensity(1000000)
    widget.set_gamma(3)
    widget.show()
    sys.exit(app.exec_())
