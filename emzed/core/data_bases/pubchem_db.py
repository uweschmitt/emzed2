import requests
import time, os, sys
import xml.etree.ElementTree  as etree

from ..chemistry.tools import monoisotopicMass
from ..data_types import Table
from ... import version

import shutil

def dom_tree_from_bytes(data):
    if isinstance(data, unicode):
        return etree.fromstring(data.encode("utf-8"))
    return etree.fromstring(data)


class PubChemDB(object):

    colNames = ["m0", "mw", "cid", "mf", "iupac", "synonyms", "url",
            "is_in_kegg", "is_in_hmdb"]
    colTypes = [float, float, int, str, str, str, str, int, int ]
    colFormats=["%.6f", "%.6f", "%s", "%s", "%s", None, "%s", "%d", "%d" ]

    @staticmethod
    def _get_count():
        url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        data = dict(db="pccompound",
                    rettype="count",
                    term="metabolic[SRCC] AND 0[TFC]",
                    tool="emzed",
                    email="tools@emzed.ethz.ch",
                    )
        r = requests.get(url, params=data)
        if r.status_code != 200:
            raise Exception("request %s failed.\nanswer : %s" % (r.url, r.text))
        doc = dom_tree_from_bytes(r.content)
        counts = doc.findall("Count")
        assert len(counts)==1
        count = int(counts[0].text)
        return count

    @staticmethod
    def _get_uilist(retmax=None, source=None):
        term="metabolic[SRCC] AND 0[TFC]"
        if source is not None:
            term +=' AND "%s"[SRC]' % source
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
        url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        r = requests.get(url, params=data)
        if r.status_code != 200:
            raise Exception("request %s failed.\nanswer : %s" % (r.url, r.text))
        doc = dom_tree_from_bytes(r.content)
        if not doc.findall("IdList"):
            raise Exception("Pubchem returned data in unknown format")
        idlist = [int(id_.text) for id_ in  doc.findall("IdList")[0].findall("Id")]
        return idlist

    @staticmethod
    def _get_summary_data(ids):
        data = dict(db="pccompound",
                    tool="emzed",
                    email="tools@emzed.ethz.ch",
                    id=",".join(str(id_) for id_ in ids),
                    version="2.0"
                    )
        url="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        r = requests.get(url, params=data)
        if r.status_code != 200:
            raise Exception("request %s failed.\nanswer : %s" % (r.url, r.text))
        return r.text

    @staticmethod
    def _parse_data(data, keggIds=None, humanMBdbIds=None):
        doc = dom_tree_from_bytes(data)
        items = []
        for summary in doc[0].findall("DocumentSummary"):
            if len(summary.findall("error")):
                print "RETRIEVAL FOR ID=%s FAILED" % (summary.attrib.get("uid"))
                continue

            dd = dict()
            for name, type_, colName in [ ("CID", int, "cid"),
                                          ("MolecularWeight", float, "mw"),
                                          ("MolecularFormula", str, "mf"),
                                          ("IUPACName", str, "iupac")]:
                element = summary.find(name)
                text = element.text
                value = type_(text)
                dd[colName] = value

            synonyms = ";".join(t.text for t in summary.find("SynonymList"))
            dd["synonyms"] = synonyms
            dd["is_in_kegg"]=dd["cid"] in (keggIds or [])
            dd["is_in_hmdb"]=dd["cid"] in (humanMBdbIds or [])
            items.append(dd)
        return items


    @staticmethod
    def _download(idlist, keggIds=None, humanMBdbIds=None):
        print
        print "START DOWNLOAD OF", len(idlist), "ITEMS"
        sys.stdout.flush()
        started = time.time()
        batchsize = 500
        jobs = [idlist[i:i+batchsize] for i in range(0, len(idlist), batchsize)]
        items = []
        for i, j in enumerate(jobs):
            data = PubChemDB._get_summary_data(j)
            if data is None:
                print "FAILED TO CONNECT"
                data = []

            items.extend(PubChemDB._parse_data(data, keggIds, humanMBdbIds))
            print "   %3d %%" % (100.0 * (i+1)/len(jobs)), "done",
            needed = time.time()-started
            time_per_batch = needed / (i+1)
            remaining = time_per_batch * (len(jobs)-i-1)
            print "   end of download in %.fm %.fs" % divmod(remaining, 60)
            sys.stdout.flush()

        needed = time.time()-started
        print
        print "TOTAL TIME %.fm %.fs" % divmod(needed,60)
        return items

    def __init__(self, path=None):
        self.path = path
        self.reload_()

    def reload_(self):
        path = self.path
        if path is not None and os.path.exists(path):
            self.table = Table.load(path)
            self.table.resetInternals()
        else:
            self.table = self._emptyTable()

    def _emptyTable(self):
        return Table(PubChemDB.colNames, PubChemDB.colTypes,
                     PubChemDB.colFormats, [], "PubChem")

    def __len__(self):
        return len(self.table)

    def getDiff(self, maxIds = None):
        try:
            counts = PubChemDB._get_count()
            unknown = []
            missing = []
            if counts!=len(self.table):
                uis = set(PubChemDB._get_uilist(maxIds))
                if uis is not None:
                    known_uis = set(self.table.cid.values)
                    unknown = list(uis - known_uis)
                    missing = list(known_uis-uis)
            return unknown, missing
        except Exception, e:
            import traceback; traceback.print_exc()
            return [], [] # failed

    def reset(self):
        self.table = self._emptyTable()
        self.update()
        self.store()

    def massCalculator(self, table, row, name):
        return monoisotopicMass(table.getValue(row, "mf"))

    def update(self, maxIds=None):
            self._update(maxIds)

    def _update(self, maxIds):

        newIds, missingIds = self.getDiff()
        if maxIds is not None:
            newIds = newIds[:maxIds] # for testing

        keggids = set(PubChemDB._get_uilist(source="KEGG"))
        hmdbids = set(PubChemDB._get_uilist(source="Human Metabolome Database"))

        print "FETCH", len(newIds), "ITEMS"
        if newIds:
            for dd in PubChemDB._download(newIds, keggids, hmdbids):
                row = [ dd.get(n) for n in self._colNames ]
                self.table.rows.append(row)
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
        self.table.addColumn("url", url+self.table.cid.apply(str), type_=str)
        self.table.addColumn("m0", self.massCalculator, type_=float, format_="%.7f", insertBefore="mw")
        self.table.sortBy("m0")# build index

    def store(self, path=None):
        if path is None:
            path = self.path
        assert path is not None, "no path given in constructor nor as argument"
        self.table.store(path, forceOverwrite=True)

    def __getattr__(self, colName):
        return getattr(self.table, colName)


FILE_NAME = "pubchem.table"

def db_path(target_dir):
    version_str = "%d.%d.%d" % version.version
    path = os.path.join(target_dir, version_str, FILE_NAME)
    return path

from .. import updaters

class PubChemUpdateImpl(updaters.AbstractUpdaterImpl):

    def __init__(self, data_home, exchange_folder):
        self.db = PubChemDB(db_path(data_home))

    @staticmethod
    def get_id():
        return "pubchem_updater"

    def get_update_time_delta_in_seconds(self):
        days = 1
        return days * 24 * 60 * 60

    def query_update_info(self):
        assert self.db is not None
        unknown, missing = self.db.getDiff()
        if unknown or missing:
            return "%d unknown and %d deleted entries on website" % (len(unknown), len(missing))
        return "data on website unchanged"

    def trigger_update(self, data_home, limit):
        assert self.db is not None
        self.db.update(maxIds=limit)
        target_path = db_path(data_home)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.db.store(target_path)

    def upload_to_exchange_folder(self, __, exchange_folder):
        assert self.db is not None
        target_path = db_path(exchange_folder)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.db.store(target_path)

    def check_for_newer_version_on_exchange_folder(self, data_home, exchange_folder):
        return os.stat(db_path(data_home)).st_mtime \
            <  os.stat(db_path(exchange_folder)).st_mtime

    def update_from_exchange_folder(self, data_home, exchange_folder):
        assert self.db is not None
        source_path = db_path(exchange_folder)
        target_path = db_path(data_home)

        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        shutil.copy(source_path, target_path)
        self.db.reload_()


