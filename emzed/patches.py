from emzed.core.patch_utils import replace, add

def apply_():
    # checking for valid values from beginning:
    import guidata.dataset.qtitemwidgets
    @replace(guidata.dataset.qtitemwidgets.LineEditWidget.__init__)
    def __init__(self, item, parent_layout):
        guidata.dataset.qtitemwidgets.LineEditWidget._orig___init__(self, item, parent_layout)
        if not item.check_value(item.get()):
            self.edit.setStyleSheet("background-color:rgb(255, 175, 90);")


