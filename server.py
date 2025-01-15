from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib
from fuseki import Fuseki

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    fuseki = Fuseki()
    def get_info(self, category, item):
        item = item.replace('(','\(').replace(')','\)').replace('\'','\\\'')
        print(category, item)
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX properties: <http://localhost:8000/properties/>
        PREFIX """+category+""": <http://localhost:8000/"""+category+"""/>
        PREFIX class: <http://localhost:8000/ontology/>
        PREFIX schema: <http://schema.org/>
        SELECT DISTINCT ?name ?class ?class_name ?prop ?prop_name ?val WHERE {
        """+category+":"+item+""" a ?class;
        ?prop ?val;
        rdfs:label ?name.
        ?prop rdfs:label ?prop_name.
        ?class rdfs:label ?class_name.
        FILTER(lang(?name) = 'en')
        }
        """
        response = self.fuseki.query(query)
        if response is None:
            return None
        if len(response['results']['bindings']) == 0:
            return None
        return response['results']['bindings']

    def do_GET(self):
        print("GET")
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        print(len(path_parts))
        if len(path_parts) == 4 and path_parts[1] == 'index':
            category = path_parts[2]
            item = path_parts[3]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            #generate a simple table view of the query result
            print("fetching infos")
            decoded_item = urllib.parse.unquote(item)
            decoded_category = urllib.parse.unquote(category)
            info = self.get_info(decoded_category, decoded_item)
            if info is None:
                response = "<html><body><h1>404 Not Found</h1></body></html>"
            else:
                response = "<html><header><meta charset='utf8'/></header><body><table>"
                response += f"<tr><th colspan='2'>{info[0]['name']['value']}</th><th><a href='{info[0]['class']['value']}'>{info[0]['class_name']['value']}</a></th></tr>"
                response += f"<tr><th>Property</th><th>Value</th></tr>"
                i = 0
                for line in info:
                    i += 1
                    if i % 2 == 0:
                        if 'xml:lang' in line['val']:
                            lang = '('+line['val']['xml:lang']+')'
                        else: 
                            lang = ''
                        response += f"<tr><td>{line['prop_name']['value']}</td><td>{line['val']['value']}{lang}</td></tr>"
                response += "</table></body></html>"
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = "<html><body><h1>404 Not Found</h1></body></html>"
            self.wfile.write(response.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('Starting server at http://localhost:8000')
    httpd.serve_forever()

if __name__ == "__main__":
    run()