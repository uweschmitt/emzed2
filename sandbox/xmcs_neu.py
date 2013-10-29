import patched_pyper
import sys
import pandas


r = patched_pyper.R(dump_stdout=True)
r_libs = "/home/uschmitt/emzed2_files/r_libs_2.14.1"

df = pandas.DataFrame(dict(a=("1", 2, None)))
r.x = df
print r.x

exit()

r("x<-data.frame()")
print r.x

r("""ok <- require("xcms", lib.loc="%s")""" % r_libs)
print r.ok


r("""source("http://bioconductor.org/biocLite.R")""")
r("""library(xcms)""")


temp_input = "/tmp/emzed_r_script_centwave_00Pgpm/input.mzData"
script = """xs <- xcmsSet('/tmp/emzed_r_script_centwave_RZAo1S/input.mzData', method="centWave",
                                        ppm=3,
                                        peakwidth=c(2, 13),
                                        prefilter=c(150, 100000),
                                        snthresh = 40.000000,
                                        integrate= 1,
                                        mzdiff   = 1.500000,
                                        noise    = 0.000000,
                                        fitgauss = FALSE,
                                        verbose.columns = FALSE,
                                        mzCenterFun = 'wMean') """


print r(script)
r("tab <- data.frame(xs@peaks)")
r("print(tab)")
t = r.tab

#r("""biocLite("xcms", dep=T, lib="%s", destdir="%s", quiet=F)""" % (r_libs, r_libs))

#r("""todo <- old.packages(repos=biocinstallRepos(), lib="%s") """ % r_libs)

#print r.get("todo",[])
