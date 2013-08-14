masses = (1024.0, 1025.0)
adducts = ("M", "M+H")

token = "DqeN7qBNEAzVNm9n"
tolerance = 300
tolunits = "ppm"

message = """<SOAP-ENV:Envelope
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="Metlin"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <SOAP-ENV:Body>
        <mns:MetaboliteSearch xmlns:mns="Metlin"
            SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <MetaboliteSearchRequest xsi:type="tns:MetaboliteSearchRequest">

                <mass xsi:type="soapenc:Array" soapenc:arrayType="xsd:float[2]">
                    <item soapenc:position="[0]" xsi:type="xsd:float">%f</item>
                    <item soapenc:position="[1]" xsi:type="xsd:float">%f</item>
                </mass>

                <adduct xsi:type="soapenc:Array" soapenc:arrayType="xsd:string[2]">
                    <item soapenc:position="[0]" xsi:type="xsd:string">%s</item>
                    <item soapenc:position="[1]" xsi:type="xsd:string">%s</item>
                </adduct>

                <tolerance xsi:type="xsd:float">%d</tolerance>

                <tolunits xsi:type="xsd:string">%s</tolunits>

                <token xsi:type="xsd:string">%s</token>

            </MetaboliteSearchRequest>
        </mns:MetaboliteSearch>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>""" % (masses + adducts+ (tolerance, tolunits, token))

import requests
import xml.etree.ElementTree as E

r = requests.post("http://metlin.scripps.edu/soap/soapserver.php", data=message)
root = E.fromstring(r.text.encode("UTF-8"))

nodes = root.findall('.//item[@{http://www.w3.org/2001/XMLSchema-instance}type="ns1:singleSearchResult"]')

import itertools

keys = ("mass", "molid", "formula", "name")

for (adduct, mass), e in zip(itertools.product(adducts, masses), nodes):

    print
    print "RESULT FOR", adduct, mass

    for c in e.getchildren():
        print
        for k in keys:
            print "  %-7s: %s" % (k, c.find(k).text)

