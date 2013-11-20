
import emzed.gui as gui

class TestFrontend(gui.WorkflowFrontend):
    """TestFrontEnd
    The first line of this docstring appeas as windows title,
    the following text (the text you read right now) appears
    as instructions at the top of the dialog.
    """

    parameter = gui.FloatItem("parameter")
    name = gui.StringItem("name", notempty=True)
    optional = gui.StringItem("optional")
    path = gui.FileOpenItem("path")

    method_one = gui.RunJobButton("patricks method")
    method_two = gui.RunJobButton("uwes method", method_name="uwe")

    def run_method_one(self):
        print "you called method one"
        print "repr(self.name)=", repr(self.name)
        print "str(self.name)=", str(self.name)

        print "path", self.path

        print "self.parameter=", self.parameter
        print
        self.name = "patrick"
        self.parameter = "42"


    def uwe(self):
        print "you called method two"
        print "self.name=", self.name
        print "self.parameter=", self.parameter
        print
        self.name = "uwe"
        self.parameter = "23"


TestFrontend().show()
