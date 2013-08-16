
class TestAllWithoutDisplay(object):

    def __init__(self):
        import os
        self.old_display = os.environ.pop("DISPLAY", None)
        print "DISPLAY BEFORE TESTS=",self.old_display
        print os.environ.keys()

    def __del__(self):
        print "RESET DISPLAY"
        import os
        if self.old_display is not None:
            os.environ["DISPLAY"] = self.old_display

# will be constructed before runnint tests
# and desctructed when tests are finished !
_test_all_without_display = TestAllWithoutDisplay()



