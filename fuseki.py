import requests
class Fuseki:
    url = 'http://localhost:3030/pokedex/sparql'
    headers={'Accept': 'application/sparql-results+json', 'encoding': 'utf-8'}
    def __init__(self):
        pass
    def query(self, query):
        response = requests.get(self.url, params={'query': query}, headers=self.headers)
        if response.status_code != 200:
            print("Error: ", response.text)
            return None
        return response.json()