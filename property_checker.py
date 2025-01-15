import pickle
import rdflib
from rdflib import RDF, Namespace
import requests
def main():
    PROPS = Namespace("http://localhost:8000/properties/")
    SCHEMA = Namespace("https://schema.org/")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    valid_props = {}
    invalid_props = pickle.load(open("saves/properties.pickle", "rb"))
    with open("files/pokemon.ttl", "rb") as file:
        data = file.readlines()
        for line in data:
            if b"ns1:" in line:
                prop = line.split(b"ns1:")[1].split(b" ")[0]
                txt = prop.decode("utf-8")
                url= SCHEMA[txt]
                #test for 404 not found
                if txt not in valid_props and txt not in invalid_props:
                    print(f"Checking {txt}...", end="")
                    response = requests.get(url)
                    if response.status_code == 200:
                        valid_props[txt] = txt
                        print(" is valid")
                    else:
                        invalid_props[txt] = txt
                        print(" is invalid")
    print("Valid properties:", len(valid_props))
    print("Invalid properties:", len(invalid_props))
    #graph = rdflib.Graph()
    #graph.bind("prop", PROPS)
    #graph.bind("schema", SCHEMA)
    #graph.bind("rdfs", RDFS)
    #for prop in invalid_props:
    #    graph.add((PROPS[prop], RDF.type, SCHEMA.Property))
    #    graph.add((PROPS[prop], RDFS.label, rdflib.Literal(prop,lang="en")))
    #with open("files/properties.ttl", "ab") as file:
    #   file.write(graph.serialize(format="turtle").encode("utf-8"))
    pickle.dump(invalid_props, open("saves/properties.pickle", "wb"))

                
main()