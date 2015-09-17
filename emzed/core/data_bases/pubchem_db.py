import requests
import time
import os
import sys
import xml.etree.ElementTree as etree

from ..chemistry.tools import monoisotopicMass
from ..data_types import Table


def dom_tree_from_bytes(data):
    if isinstance(data, unicode):
        return etree.fromstring(data.encode("utf-8"))
    return etree.fromstring(data)


class PubChemDB(object):

    colNames = ["m0", "mw", "cid", "mf", "iupac", "synonyms", "url",
                "is_in_kegg", "is_in_hmdb", "is_in_bioycyc", "inchi"]
    colTypes = [float, float, int, str, str, str, str, int, int, int, str]
    syn_formatter = "str(o) if len(o) < 60 else str(o)[:57]+'...'"
    colFormats = ["%.6f", "%.6f", "%s", "%s", "%s", syn_formatter, "%s", "%d", "%d", "%d", "%s"]

    @staticmethod
    def _get_count():
        url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        data = dict(db="pccompound",
                    rettype="count",
                    term="""((0:0[TotalFormalCharge]) AND ( ("KEGG"[SourceName]) or ("Human
                    Metabolome Database"[SourceName]) or "(Biocyc"[SourceName]) )) """,
                    tool="emzed",
                    email="tools@emzed.ethz.ch",
                    )
        r = requests.get(url, params=data)
        if r.status_code != 200:
            raise Exception("request %s failed.\nanswer : %s" % (r.url, r.text))
        doc = dom_tree_from_bytes(r.content)
        counts = doc.findall("Count")
        assert len(counts) == 1
        count = int(counts[0].text)
        return count

    @staticmethod
    def _get_uilist(retmax=None, source=None):
        if source is None:
            term="""((0:0[TotalFormalCharge]) AND ( ("KEGG"[SourceName]) or ("Human
            Metabolome Database"[SourceName]) or "(Biocyc"[SourceName]) )) """
        else:
            term="""((0:0[TotalFormalCharge]) AND ( ("%s"[SourceName]) ))""" % source
        if retmax is None:
            retmax = 99999999
        data = dict(db="pccompound",
                    rettype="uilist",
                    term=term,
                    retmax=retmax,
                    tool="emzed",
                    email="tools@emzed.ethz.ch",
                    usehistory="Y"
                    )
        url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        r = requests.get(url, params=data)
        if r.status_code != 200:
            raise Exception("request %s failed.\nanswer : %s" % (r.url, r.text))
        doc = dom_tree_from_bytes(r.content)
        if not doc.findall("IdList"):
            raise Exception("Pubchem returned data in unknown format")
        idlist = [int(id_.text) for id_ in doc.findall("IdList")[0].findall("Id")]
        return idlist

    @staticmethod
    def _get_summary_data(ids):
        data = dict(db="pccompound",
                    tool="emzed",
                    email="tools@emzed.ethz.ch",
                    id=",".join(str(id_) for id_ in ids),
                    version="2.0"
                    )
        url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        r = requests.get(url, params=data)
        if r.status_code != 200:
            raise Exception("request %s failed.\nanswer : %s" % (r.url, r.text))
        return r.text

    @staticmethod
    def _parse_data(data, keggIds=None, humanMBdbIds=None, biocycIds=None):
        doc = dom_tree_from_bytes(data)
        items = []
        for summary in doc[0].findall("DocumentSummary"):
            if len(summary.findall("error")):
                print "RETRIEVAL FOR ID=%s FAILED" % (summary.attrib.get("uid"))
                continue

            dd = dict()
            for name, type_, colName in [("CID", int, "cid"),
                                         ("MolecularWeight", float, "mw"),
                                         ("MolecularFormula", str, "mf"),
                                         ("IUPACName", str, "iupac"),
                                         ("InChI", str, "inchi")]:
                element = summary.find(name)
                text = element.text
                value = type_(text)
                dd[colName] = value

            synonyms = ";".join(t.text for t in summary.find("SynonymList"))
            dd["synonyms"] = synonyms
            dd["is_in_kegg"] = dd["cid"] in (keggIds or [])
            dd["is_in_hmdb"] = dd["cid"] in (humanMBdbIds or [])
            dd["is_in_bioycyc"] = dd["cid"] in (biocycIds or [])
            items.append(dd)
        return items

    @staticmethod
    def _download(idlist, keggIds=None, humanMBdbIds=None, biocycIds=None):
        print
        print "START DOWNLOAD OF", len(idlist), "ITEMS"
        sys.stdout.flush()
        started = time.time()
        batchsize = 500
        jobs = [idlist[i:i + batchsize] for i in range(0, len(idlist), batchsize)]
        for i, j in enumerate(jobs):
            data = PubChemDB._get_summary_data(j)
            if data is None:
                print "FAILED TO CONNECT"
                data = []

            bulk_data = PubChemDB._parse_data(data, keggIds, humanMBdbIds, biocycIds)
            for item in bulk_data:
                yield item
            print "   %3d %%" % (100.0 * (i + 1) / len(jobs)), "done",
            needed = time.time() - started
            time_per_batch = needed / (i + 1)
            remaining = time_per_batch * (len(jobs) - i - 1)
            print "   end of download in %.fm %.fs" % divmod(remaining, 60)
            sys.stdout.flush()

        needed = time.time() - started
        print
        print "TOTAL TIME %.fm %.fs" % divmod(needed, 60)

    _instances = dict()

    @staticmethod
    def cached_load_from(path):
        if path not in PubChemDB._instances:
            PubChemDB._instances[path] = PubChemDB(path)
        return PubChemDB._instances[path]

    def __init__(self, path):
        self.path = path
        self.reload_()

    def reload_(self):
        path = self.path
        if path is not None and os.path.exists(path):
            self.table = Table.load(path)
            if self.table.getColNames() != PubChemDB.colNames:
                cmd = "import emzed; emzed.db.reset_pubchem()"
                raise Exception("local pubchem data base has old format, please run %r to refresh, "
                                "this might take a while" % cmd)
            self.table.resetInternals()
        else:
            self.table = self._emptyTable()

    def _emptyTable(self):
        return Table(PubChemDB.colNames, PubChemDB.colTypes, PubChemDB.colFormats, [], "PubChem")

    def __len__(self):
        return len(self.table)

    def getDiff(self, maxIds=None):
        counts = PubChemDB._get_count()
        unknown = []
        missing = []
        if counts != len(self.table):
            uis = set(PubChemDB._get_uilist(maxIds))
            if uis is not None:
                known_uis = set(self.table.cid.values)
                unknown = list(uis - known_uis)
                missing = list(known_uis - uis)
        return unknown, missing

    def reset(self):
        self.table = self._emptyTable()
        self.update()
        self.store()

    def massCalculator(self, table, row, name):
        return monoisotopicMass(table.getValue(row, "mf"))

    def update(self, maxIds=None, callback=None):
            self._update(maxIds, callback)

    def _update(self, maxIds, callback):

        newIds, missingIds = self.getDiff()
        if maxIds is not None:
            newIds = newIds[:maxIds]  # for testing

        keggids = set(PubChemDB._get_uilist(source="KEGG"))
        hmdbids = set(PubChemDB._get_uilist(source="Human Metabolome Database"))
        biocycids = set(PubChemDB._get_uilist(source="Biocyc"))

        if callback is None:
            callback = lambda i, imax: None

        print "FETCH", len(newIds), "ITEMS"
        if newIds:
            try:
                callback(0, len(newIds))
                for i, dd in enumerate(PubChemDB._download(newIds, keggids, hmdbids, biocycids)):
                    row = [dd.get(n) for n in PubChemDB.colNames]
                    self.table.rows.append(row)
                    if i % 20 == 0:
                        callback(i, len(newIds))
                callback(i, len(newIds))
            except BaseException, e:
                if e != "aborted":
                    self.store()  # in case of bad internet connection save immediate result
                    raise
        try:
            self.table.dropColumns("url")
        except:
            pass
        try:
            self.table.dropColumns("m0")
        except:
            pass
        if len(missingIds):
            print "DELETE", len(missingIds), "ENTRIES FROM LOCAL DB"
            self.table = self.table.filter(~self.table.cid.isIn(missingIds))
        url = "http://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid="
        self.table.addColumn("url", url + self.table.cid.apply(str), type_=str, insertBefore="is_in_kegg")
        self.table.addColumn(
            "m0", self.massCalculator, type_=float, format_="%.7f", insertBefore="mw")
        self.table.sortBy("m0")  # build index

    def store(self, path=None):
        if path is None:
            path = self.path
        assert path is not None, "no path given in constructor nor as argument"
        self.table.store(path, forceOverwrite=True)
        PubChemDB._instances[path] = self

    def __getattr__(self, colName):
        if hasattr(self, "table"):      # might be undefined eg during unpickling
            return getattr(self.table, colName)
        raise AttributeError("attribute table of %r not set" % self)
