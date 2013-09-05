import requests
import cStringIO
assert requests.get("http://localhost:54321/").json() == dict(packages=dict())

data = cStringIO.StringIO("abc123")
#requests.put("http://localhost:54321/fahrrad/patrick_kiefer/_private.txt", data=data)

assert requests.get("http://localhost:54321/fahrrad/patrick_kiefer/").json() == dict(packages=["_private.txt"])

assert requests.delete("http://localhost:54321/fahrrad/patrick_kiefer/").content == ""

"""
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/private")
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/private/")
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/private/").tojson()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/private/").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/private/abcde.py").content
requests.get("http://localhost:54321/fahrradx/patrick_kiefer/private/abcde.py").content
requests.get("http://localhost:54321/fahrradx/patrick_kiefer/private/abcde.py").content
requests.get("http://localhost:54321/")
requests.get("http://localhost:54321/").json()
requests.get("http://localhost:54321/").json()
requests.get("http://localhost:54321/").json()
requests.get("http://localhost:54321/patrick_kiefer").json()
requests.get("http://localhost:54321/patrick_kiefer/").json()
requests.get("http://localhost:54321/:/patrick_kiefer/").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/_abcde.py").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/_abcde.py").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/_abcde.py")
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/_abcde.py").content
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/_abcde.py").content
requests.put("http://localhost:54321/fahrrad/patrick_kiefer/private/abcde.py", data=open("minimal.py", "r"))
requests.put("http://localhost:54321/fahrrad/patrick_kiefer/abcde.py", data=open("minimal.py", "r"))
requests.put("http://localhost:54321/fahrrad/patrick_kiefer/_xabcde.py", data=open("minimal.py", "r"))
requests.get("http://localhost:54321/")
requests.get("http://localhost:54321/").json()
requests.put("http://localhost:54321/fahrrad/patrick_kiefer/_xabcde.py", data=open("minimal.py", "r"))
requests.get("http://localhost:54321/").json()
requests.get("http://localhost:54321/").json()
requests.get("http://localhost:54321/patrick_kiefer").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer")
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/")
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/").json()
requests.get("http://localhost:54321/fahrrad/patrick_kiefer/_xabcde.py").content

%history
%history > x.out
%history?
%history -r -f mintest.py
"""
