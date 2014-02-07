import emzed
table = emzed.io.loadTable("isotope_clustered.table")
table.info()

delta_C = emzed.mass.C13 - emzed.mass.C12


table = emzed.utils.mergeTables(collected)
emzed.io.storeTable(table, "final.table", True)
#emzed.gui.inspect(table)




