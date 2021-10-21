from dataclasses import dataclass
from flask import Flask, Response, request

import os, sys
# add local files in the module path; uwsgi doesn't work otherwise
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cmdi_extractor import read_cmdi_fromsource, cmdi_to_cache
from update_cmdi import cache_to_cmdi, cmdi_to_string
from entity_cache import EntityCache

@dataclass
class Args:
    new_cache = False
    path_to_cache = "cache.csv"
    delimiter = "\t"
    specification = "entity_spec.json"
    namespace_tag_list = "namespaces_tags.csv"
    authoritative_tag = "AuthoritativeID"
    new_cmdis = "updated_cmdis"
    cmdi_files = "data/"

args = Args();
cache = EntityCache(filepath=args.path_to_cache, 
                    delimiter=args.delimiter,
                    specification=args.specification,
                    create_new=args.new_cache)

app = Flask(__name__)
 
htmlinfo = """
<h1>BiodataNER</h1>
<p>Send CMDI data to this service to have it enriched with VIAF info.</p>
<p>Example:</p>
<pre>curl -d @CMDI.xml -H 'content-type:application/xml' https://.../BiodataNER</pre>
"""

@app.route("/")
def index():
    return Response(htmlinfo, status=400)

@app.route("/BiodataNER", methods=['GET', 'POST'])
def biodataner():
    if request.method == 'GET':
        return Response(htmlinfo, status=400)
    if not request.data:
        return Response("POST data expected (a CMDI file)", status=400)
    if request.mimetype != 'application/xml':
        return Response("Accepts only application/xml", status=400)

    cmdi = read_cmdi_fromsource(request.data)
    cmdi_to_cache(cmdi, cache, args)
    cache_to_cmdi(cache, cmdi, args);
    return Response(cmdi_to_string(cmdi), status=200)
    

__version__ = '0.1.0'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
