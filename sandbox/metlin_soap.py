masses = (1024.0, 1025.0)
adducts = ("M", "M+H")


def match(masses, adducts, tolerance=30, tolunits="ppm"):

    token = ""

    mass_items = "".join("""\
            <item soapenc:position="[%d]" xsi:type="xsd:float">%.6f</item>""" % p
                           for p in enumerate(masses))
    adduct_items = "".join("""\
            <item soapenc:position="[%d]" xsi:type="xsd:string">%s</item>""" %p
                           for p in enumerate(adducts))

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

                    <mass xsi:type="soapenc:Array" soapenc:arrayType="xsd:float[%d]">
                        %s
                    </mass>

                    <adduct xsi:type="soapenc:Array" soapenc:arrayType="xsd:string[%d]">
                        %s
                    </adduct>

                    <tolerance xsi:type="xsd:float">%d</tolerance>

                    <tolunits xsi:type="xsd:string">%s</tolunits>

                    <token xsi:type="xsd:string">%s</token>

                </MetaboliteSearchRequest>
            </mns:MetaboliteSearch>
        </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>""" % (len(masses), mass_items, len(adducts), adduct_items, tolerance, tolunits, token)

    print message

    import requests
    import xml.etree.ElementTree as E

    r = requests.post("http://metlin.scripps.edu/soap/soapserver.php", data=message)
    root = E.fromstring(r.text.encode("UTF-8"))

    print r.text

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


match(masses, adducts, 300)


masses = [ 1024.0 + i for i in range(501)]
match(masses, ["M", "M+H"], 30)


