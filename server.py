from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib
from fuseki import Fuseki

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    fuseki = Fuseki()

    def get_info(self, category, item):
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX {category}: <http://localhost:8000/{category}/>
        SELECT *
        WHERE {{
            {category}:{item} rdfs:label ?label .
            FILTER(lang(?label) = 'en')
        }}
        """
        response = self.fuseki.query(query)
        if response is None:
            return None
        if len(response['results']['bindings']) == 0:
            return None
        return response['results']['bindings'][0]

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        
        if len(path_parts) == 4 and path_parts[1] == 'index':
            category = path_parts[2]
            item = path_parts[3]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            #generate a simple table view of the query result
            info = self.get_info(category, item)
            if info is None:
                response = "<html><body><h1>404 Not Found</h1></body></html>"
            else:
                response = "<html><body><table>"
                for key in info:
                    response += f"<tr><td>{key}</td><td>{info[key]['value']}</td></tr>"
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