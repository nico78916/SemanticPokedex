import os
import pickle
import time
import pywikibot
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from server import run

# Définir les namespaces
SCHEMA = Namespace("http://schema.org/")
POKEMON = Namespace("http://localhost:8000/pokemon/")
TYPES = Namespace("http://localhost:8000/types/")
GENERATION = Namespace("http://localhost:8000/generation/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
ABILITY = Namespace("http://localhost:8000/ability/")
CLASSES = Namespace("http://localhost:8000/ontology/")
PROPS = Namespace("http://localhost:8000/properties/")

# Créer un site pywikibot pour Bulbapedia
sites = {"en" : pywikibot.Site("en", "bulpedia"),"fr": pywikibot.Site("fr", "bulpedia")}
types, generations, abilities, pokemons, fr_pokemons, own_properties = {}, {}, {}, {}, {}, {}

def get_page_source(page_title): 
    """Récupère le contenu d'une page Bulbapedia."""
    page = pywikibot.Page(sites["en"], page_title) 
    if page.exists(): 
        if page.isRedirectPage(): 
            page = page.getRedirectTarget() 
        return page.get()
    return None

def get_pokemon_list(): 
    """Récupère la liste des Pokémon depuis la catégorie Bulbapedia."""
    return [page.title() for page in pywikibot.Category(sites["en"], "Category:Pokémon").articles()]

def get_fr_pokemon_list():
    """Récupère la liste des Pokémon depuis la catégorie Poképédia."""
    return [page.title() for page in pywikibot.Category(sites["fr"], "Pokémon").articles()]

def get_type_info(type_name):
    """Récupère les informations de type depuis Bulbapedia."""
    text = get_page_source(type_name + " (type)")
    if text is None:
        print("Type not found")
        return None
    
    result, in_type_prop, in_off = {"offense": {}, "defense": {}}, False, False
    for line in text.split("\n"):
        if line.startswith("|") and in_type_prop:
            key, value = map(str.strip, line.split("=", 1))
            if key == "type":
                continue
            if key == "prop":
                in_off = (value == "Off")
                continue
            values = [v.split("|")[1] for v in value.split("}}") if len(v.split("|")) == 2]
            result["offense" if in_off else "defense"][key] = values
        in_type_prop = line.startswith('{{TypeProperties')
    
    print(type_name, "added")
    return result

def get_generation_info(gen_name):
    """Récupère les informations de génération depuis Bulbapedia."""
    text = get_page_source(gen_name)
    if text is None:
        print("Generation not found")
        return []
    
    gen_info_box, in_infobox = [], False
    for line in text.split("\n"):
        if line.startswith("{{Generation"):
            in_infobox = True
        if in_infobox:
            if "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                gen_info_box.append((key, value))
        if line.startswith("}}"):
            in_infobox = False
    
    print(gen_name, "added")
    return gen_info_box

def generation_to_rdf(generations):
    """Convertit les informations de génération en RDF."""
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("pokemon", POKEMON)
    g.bind("types", TYPES)
    g.bind("generation", GENERATION)
    g.bind("rdfs", RDFS)
    g.bind("ability", ABILITY)
    g.bind("classes", CLASSES)
    for gen_name, gen_info in generations.items():
        gen_uri = URIRef(GENERATION[gen_name])
        g.add((gen_uri, RDF.type, CLASSES.Generation))
        g.add((gen_uri, SCHEMA.name, Literal(gen_name)))
        for key, value in gen_info:
            if value.startswith("{{") and value.endswith("}}"):
                for v in value[2:-2].split("|"):
                    g.add((gen_uri, SCHEMA[key], Literal(v)))
            elif key == "remakes":
                g.add((gen_uri, SCHEMA[key], GENERATION["generation_" + value]))
            else:    
                g.add((gen_uri, SCHEMA[key], Literal(value)))
    return g

def get_ability_info(ability_name):
    """Récupère les informations de capacité depuis Bulbapedia."""
    text = get_page_source(ability_name.replace("_", " ") + " (ability)")
    if text is None:
        text = get_page_source(ability_name.replace("_", " ") + " (Ability)")
    if text is None:
        print("Ability '" + ability_name.replace("_", " ") + " (Ability)' not found")
        return []
    
    ability_descs = [line for line in text.split("\n") if line.startswith("{{AbilityInfobox/desc")]
    print("ability", ability_name, "added")
    return ability_descs

def ability_to_rdf(abilities):
    """Convertit les informations de capacité en RDF."""
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("pokemon", POKEMON)
    g.bind("types", TYPES)
    g.bind("generation", GENERATION)
    g.bind("rdfs", RDFS)
    g.bind("ability", ABILITY)
    g.bind("classes", CLASSES)
    for ability_name, ability_info in abilities.items():
        ability_uri = URIRef(ABILITY[ability_name])
        g.add((ability_uri, RDF.type, CLASSES.Ability))
        g.add((ability_uri, SCHEMA.name, Literal(ability_name, lang="en")))
        g.add((ability_uri, RDFS.label, Literal(ability_name, lang="en")))
        for desc in ability_info:
            values = desc.split("|")
            description, generation = values[2], "generation_" + values[1]
            description = description.replace("}}","")
            if generation not in generations:
                generations[generation] = get_generation_info(generation)
            g.add((ability_uri, SCHEMA.description, Literal(description, lang="en")))
    return g
translator = {}
def get_infobox(pokemon_name):
    """Récupère l'infobox d'un Pokémon depuis Bulbapedia."""
    page = pywikibot.Page(sites["en"], pokemon_name)
    if page.isRedirectPage():
        page = page.getRedirectTarget()
    text = page.get()
    infobox_start = text.find("{{Pokémon Infobox")
    infobox_end = text.find("}}", infobox_start) + 2
    lines = text.split("\n")
    i = len(lines) - 1
    langs = ["de", "es", "fr", "ja", "it", "zh"]
    found_one = False
    while i > 0:
        line = lines[i].strip()
        if line.startswith("[["):
            line = line.replace("[[", "").replace("]]", "")
            vals = line.split(":")
            if vals[0] in langs:
                found_one = True
                if not pokemon_name in translator:
                    translator[pokemon_name] = {}
                translator[pokemon_name][vals[0]] = vals[1]
            else:
                if found_one:
                    break
                else:
                    i -= 1
                    continue
        i -= 1

    return text[infobox_start:infobox_end]

def parse_infobox(infobox):
    """Analyse l'infobox pour extraire les propriétés."""
    return {key.strip().replace("|", ""): value.strip() for line in infobox.split("\n") if "=" in line for key, value in [line.split("=", 1)]}

def convert_digit_to_roman(digit):
    """Convertit un chiffre en chiffre romain."""
    return {
        '1': "I", '2': "II", '3': "III", '4': "IV", '5': "V", '6': "VI", '7': "VII", '8': "VIII", '9': "IX", '10': "X"
    }.get(digit, digit)


def get_litteral_type(value) -> str:
    """Retourne le type de la valeur."""
    try:
        int(value)
        return SCHEMA.Integer
    except ValueError:
        try:
            float(value)
            return SCHEMA.Float
        except ValueError:
            #date ?
            if len(value.split("-")) == 3:
                return SCHEMA.Date
            #date time ?
            if len(value.split("-")) == 3 and len(value.split(":")) == 3:
                return SCHEMA.DateTime
            #time ?
            if len(value.split(":")) == 3:
                return SCHEMA.Time
            return SCHEMA.Text

def generate_rdf(pokemons):
    """Génère le RDF pour les Pokémon."""
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("pokemon", POKEMON)
    g.bind("types", TYPES)
    g.bind("generation", GENERATION)
    g.bind("rdfs", RDFS)
    g.bind("ability", ABILITY)
    g.bind("classes", CLASSES)
    for pokemon_name, properties in pokemons.items():
        pokemon_uri = URIRef(POKEMON[pokemon_name.replace(" ", "_")])
        g.add((pokemon_uri, RDF.type, CLASSES.Pokemon))
        url_encoded = pokemon_name.replace(" ", "_").replace("'", "%27")
        g.add((pokemon_uri, SCHEMA.sameAs, URIRef("https://bulbapedia.bulbagarden.net/wiki/" + url_encoded)))
        for key, value in properties.items():
            if key.endswith("type1") or key.endswith("type2"):
                if value not in types:
                    types[value] = get_type_info(value)
                g.add((pokemon_uri, SCHEMA[key], TYPES[value]))
            elif key.startswith("ability") and not any(key.endswith(suffix) for suffix in ["note", "layout", "caption"]) and not key.startswith("abilitycol") and not key.startswith("abilityn"):
                correct_value = value.replace(" ", "_")
                if correct_value not in abilities:
                    abilities[correct_value] = get_ability_info(correct_value)
                g.add((pokemon_uri, SCHEMA[key], ABILITY[correct_value]))
            elif key.startswith("generation"):
                gen = convert_digit_to_roman(value)
                if "generation_" + gen not in generations:
                    generations["generation_" + gen] = get_generation_info("generation " + gen)
            if key == "name":
                g.add((pokemon_uri, RDFS.label, Literal(value, lang="en")))
                g.add((pokemon_uri, SCHEMA.name, Literal(value, lang="en")))

                translations = translator[pokemon_name]
                for lang, name in translations.items():
                    g.add((pokemon_uri, RDFS.label, Literal(name, lang=lang)))
                    g.add((pokemon_uri, SCHEMA.name, Literal(name, lang=lang)))

            if key == "jname":
                g.add((pokemon_uri, RDFS.label, Literal(value, lang="ja")))
                g.add((pokemon_uri, SCHEMA.name, Literal(value, lang="ja")))
            else:
                if key.startswith("<!--"):
                    key = key.split("<!--")[1].strip()
                if key in own_properties:
                    g.add((pokemon_uri, PROPS[key], Literal(value, datatype=get_litteral_type(value))))
                else:
                    g.add((pokemon_uri, SCHEMA[key], Literal(value, datatype=get_litteral_type(value))))
    return g

def types_to_rdf(types):
    """Convertit les informations de type en RDF."""
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("pokemon", POKEMON)
    g.bind("types", TYPES)
    g.bind("generation", GENERATION)
    g.bind("rdfs", RDFS)
    g.bind("ability", ABILITY)
    g.bind("classes", CLASSES)
    for type_name, infos in types.items():
        type_uri = TYPES[type_name]
        g.add((type_uri, RDF.type, CLASSES.ElementaryType))
        g.add((type_uri, SCHEMA.name, Literal(type_name)))
        for key, value in infos.items():
            for k, v in value.items():
                for i in range(len(v)):
                    g.add((type_uri, SCHEMA[key + "_" + k], TYPES[v[i]]))
    return g

def save(graph,filename):
    """Sauvegarde le graphe RDF dans un fichier."""
    with open(filename, "wb") as f:
        f.write(graph.serialize(format="turtle").encode("utf-8"))

def main():
    global types, generations, abilities, pokemons, translator, own_properties
    pokemon_list = get_pokemon_list()
    i = 0
    element_per_sec = 0
    time_elapsed = 0
    own_properties = pickle.load(open("saves/properties.pickle", "rb"))
    start= time.time()
    if os.path.exists("saves/pokemons.pkl"):
        pokemons = pickle.load(open("saves/pokemons.pkl", "rb"))
        translator = pickle.load(open("saves/translator.pkl", "rb"))
    else:
        for pokemon in pokemon_list[1:]:
            print("Processing", pokemon)
            i += 1
            if(i % 10 == 0):
                print(f"Element per second: {element_per_sec} {i}/{len(pokemon_list)}")
            infobox = get_infobox(pokemon)
            properties = parse_infobox(infobox)
            pokemons[pokemon] = properties
            time_elapsed = time.time() - start
            element_per_sec = i / time_elapsed
        #Save all the data
        pickle.dump(pokemons, open("saves/pokemons.pkl", "wb"))
        pickle.dump(translator, open("saves/translator.pkl", "wb"))
    #convert types to rdf
    if os.path.exists("saves/types.pkl"):
        types = pickle.load(open("saves/types.pkl", "rb"))
    if os.path.exists("saves/generations.pkl"):
        generations = pickle.load(open("saves/generations.pkl", "rb"))
    if os.path.exists("saves/abilities.pkl"):
        abilities = pickle.load(open("saves/abilities.pkl", "rb"))

    rdf = generate_rdf(pokemons)
    pickle.dump(types, open("saves/types.pkl", "wb"))
    pickle.dump(generations, open("saves/generations.pkl", "wb"))
    pickle.dump(abilities, open("saves/abilities.pkl", "wb"))

                                
    d = {
        "files/pokemon.ttl":rdf,
        "files/types.ttl":types_to_rdf(types),
        "files/generations.ttl": generation_to_rdf(generations),
        "files/abilities.ttl": ability_to_rdf(abilities)
    }
    for filename, graph in d.items():
        save(graph,filename)
    #start server
    run()


    


if __name__ == "__main__":
    main()
