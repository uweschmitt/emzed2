import pdb
#encoding:latin-1
import requests
import urllib2

from collections import OrderedDict


from data_types import Table
import config


class MetlinMatcher(object):

    ws_col_names = [ "formula", "mass", "name", "molid"]
    ws_col_types = [ str, float, str, int]
    ws_col_formats = [ "%s", "%.5f", "%s", "%d" ]

    url = "http://metlin.scripps.edu/REST/search/index.php"
    info_url = "http://metlin.scripps.edu/metabo_info.php?molid=%d"

    batch_size = 97 # should be 500 as metlin promises, but this is false

    # the REST webserive of METLIN returns a result set which does not explain
    # which combination of theoretical mass and adduct results in a match,
    # which is not what we want.  eg one gets the same result set for
    # masses=[195.0877, 194.07904], adducts=["M"] and for masses=[195.0877],
    # adducts = ["M", "M+H"]
    # so we start a separate query for mass and each adduct !

    @staticmethod
    def _query(masses, adduct, ppm):

        token = config.global_config.get("metlin_token")
        if not token:
            raise Exception("metlin token not configured. call emzed.core.config.global_config.edit()")

        params = OrderedDict()
        params["token"] = token # "DqeN7qBNEAzVNm9n"
        params["mass[]"] = masses
        params["adduct[]"] = [adduct]
        params["tolunits"] = "ppm"
        params["tolerance"] = ppm

        r = requests.get(MetlinMatcher.url, params=params)
        if r.status_code != 200:
            raise Exception("matlin query %s failed: %s" %
                                              (urllib2.unquote(r.url), r.text))

        try:
            j = r.json()
        except:
            print r.content
            raise Exception("invalid answer from %s" % r.url)
        ws_col_names = MetlinMatcher.ws_col_names
        ws_col_types = MetlinMatcher.ws_col_types
        ws_col_formats = MetlinMatcher.ws_col_formats
        info_url = MetlinMatcher.info_url

        tables = []
        for m_z, ji in zip(masses, j):
            rows = []
            if isinstance(ji, dict):
                ji = ji.values()
            for jii in ji:
                if jii:
                    rows.append([t(jii[n])\
                                  for t, n in zip(ws_col_types, ws_col_names)])
            if rows:
                ti = Table(ws_col_names, ws_col_types, ws_col_formats, rows[:])
                ti.addColumn("m_z", m_z, insertBefore=0)
                ti.addColumn("adduct", adduct, insertBefore=1)
                ti.addColumn("link", ti.molid.apply(lambda d: info_url % d))
                tables.append(ti)
        return tables

    @staticmethod
    def query(masses, adducts, ppm):
        all_tables = []
        for adduct in adducts:
            for i0 in range(0, len(masses), MetlinMatcher.batch_size):
                mass_slice = masses[i0:i0 + MetlinMatcher.batch_size]
                tables = MetlinMatcher._query(mass_slice, adduct, ppm)
                all_tables.extend(tables)
        result_table = all_tables[0]
        result_table.append(all_tables[1:])

        return result_table



if 0:
    t = MetlinMatcher.query(["282.222813", "292.229272"], 50, "-")
    t.info()

    t._print()
