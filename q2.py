import pywikibot
from rdflib import Graph, Literal, RDF, URIRef, Namespace

# Définir les namespaces
SCHEMA = Namespace("http://schema.org/")
POKEMON = Namespace("http://example.org/pokemon/")
TYPES = Namespace("http://example.org/types/")
GENERATION = Namespace("http://example.org/generation/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
ABILITY = Namespace("http://example.org/ability/")

# Créer un site pywikibot pour Bulbapedia
site = pywikibot.Site()

types = {}
generations = {}
abilities = {}
pokemons = {}

def get_page_source(page_title): 
    page = pywikibot.Page(site, page_title) 
    if page.exists(): 
        if page.isRedirectPage(): 
            page = page.getRedirectTarget() 
        text = page.get()
        return text 
    else: 
        return None

def get_pokemon_list(): 
    pokemon_list = [] 
    category = pywikibot.Category(site, "Category:Pokémon") 
    for page in category.articles(): 
        pokemon_list.append(page.title()) 
    return pokemon_list

def get_type_info(type_name):
    text = get_page_source(type_name+" (type)")
    if text is None:
        print("Type not found")
        return None
    #Il y a deux  TypeProperties -> prop=Def et prop=Off
    result = {"offense":{}, "defense":{}}
    in_type_prop = False
    in_off = False
    for line in text.split("\n"):
        if line.startswith("|") and in_type_prop:
            key, value = line.split("=", 1)
            key = key.strip().replace("|", "")
            value = value.strip()
            if(key == "type"):
                continue
            if(key == "prop"):
                if(value == "Off"):
                    in_off = True
                    continue
                else:
                    in_off = False
                    continue
            # value est de la forme : {{...|...}}{{...|...}}...
            #extraire ...|... et ...|...
            value = value.split("}}")
            values = []
            for v in value:
                v = v.split("|")
                if(len(v) != 2):
                    continue
                values += [v[1]]
            if in_off:
                result["offense"][key] = values
            else:
                result["defense"][key] = values
        else:
            if line.startswith('{{TypeProperties'):
                in_type_prop = True
            else:
                in_type_prop = False
    print(type_name, "added")
    return result

def get_generation_info(gen_name):
    text = get_page_source(gen_name)
    if text is None:
        print("Generation not found")
        return []
    gen_info_box = []
    in_infobox = False
    for line in text.split("\n"):
        if line.startswith("{{Generation"):
            in_infobox = True
        if in_infobox:
            els = line.split("=")
            if len(els) == 2:
                key = els[0].strip().replace("|", "")
                value = els[1].strip()
                gen_info_box.append((key, value))
        if line.startswith("}}"):
            in_infobox = False
    print(gen_name, "added")
    return gen_info_box

def generation_to_rdf(generations):
    g = Graph()
    for gen_name, gen_info in generations.items():
        gen_uri = URIRef(GENERATION[gen_name])
        g.add((gen_uri, RDF.type, SCHEMA.Thing))
        g.add((gen_uri, SCHEMA.name, Literal(gen_name)))
        for key, value in gen_info:
            if value.stratsWith("{{") and value.endswith("}}"):
                value = value[2:-2]
                value = value.split("|")
                for i in range(len(value)):
                    g.add((gen_uri, SCHEMA[key], Literal(value[i])))

            elif key == "remakes":
                g.add((gen_uri, SCHEMA[key], GENERATION["generation_"+value]))
            else:    
                g.add((gen_uri, SCHEMA[key], Literal(value)))
    return g

def get_ability_info(ability_name):
    text = get_page_source(ability_name.replace("_"," ")+" (ability)")
    if text is None:
        print("Ability '"+ability_name+" (ability)' not found")
        return []
    ability_descs = []
    for line in text.split("\n"):
        if line.startswith("{{AbilityInfobox/desc"):
            ability_descs.append(line)
    print("ability",ability_name, "added")
    return ability_descs

def ability_to_rdf(abilities):
    g = Graph()
    for ability_name, ability_info in abilities.items():
        print("rdfying", ability_name)
        ability_uri = URIRef(ABILITY[ability_name])
        g.add((ability_uri, RDF.type, SCHEMA.Thing))
        g.add((ability_uri, SCHEMA.name, Literal(ability_name)))
        for desc in ability_info:
            values = desc.split("|")
            description = values[2]
            generation = "generation_"+values[1]
            if not generation in generations:
                generations[generation] = get_generation_info(generation)
            g.add((ability_uri, SCHEMA.description, Literal(description)))
    return g

def get_infobox(pokemon_name):
    page = pywikibot.Page(site, pokemon_name)
    if page.isRedirectPage():
        page = page.getRedirectTarget()
    text = page.get()
    infobox_start = text.find("{{Pokémon Infobox")
    infobox_end = text.find("}}", infobox_start) + 2
    infobox = text[infobox_start:infobox_end]
    return infobox

def parse_infobox(infobox):
    properties = {}
    lines = infobox.split("\n")
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip().replace("|", "")
            value = value.strip()
            properties[key] = value
    return properties

def convert_digit_to_roman(digit):
    roman = {
        '1': "I",
        '2': "II",
        '3': "III",
        '4': "IV",
        '5': "V",
        '6': "VI",
        '7': "VII",
        '8': "VIII",
        '9': "IX",
        '10': "X"
    }
    return roman[digit]

def generate_rdf(pokemons):
    g = Graph()
    for pokemon_name, properties in pokemons.items():
        pokemon_uri = URIRef(POKEMON[pokemon_name.replace(" ", "_")])
        g.add((pokemon_uri, RDF.type, SCHEMA.Thing))
        g.add((pokemon_uri, SCHEMA.name, Literal(pokemon_name)))
        url_encoded = pokemon_name.replace(" ", "_").replace("'", "%27")
        g.add((pokemon_uri, SCHEMA.SameAs, URIRef("https://bulbapedia.bulbagarden.net/wiki/"+url_encoded)))
        for key, value in properties.items():
            if key.endswith("type1") or key.endswith("type2"):
                if not value in types:
                    types[value] = get_type_info(value)
                g.add((pokemon_uri, SCHEMA[key], TYPES[value]))
            elif key.startswith("ability") and not ( key.endswith("note") or key.endswith("layout") or key.endswith("caption") or key.startswith("abilitycol") or key.startswith("abilityn") ):
                if not value in abilities:
                    abilities[value.replace(" ","_")] = get_ability_info(value.replace(" ", "_"))
                g.add((pokemon_uri, SCHEMA[key], ABILITY[value.replace(" ", "_")]))
            elif key.startswith("generation"):
                gen = convert_digit_to_roman(value)
                if not "generation "+gen in generations:
                    generations["generation_"+gen] = get_generation_info("generation "+gen)
            else:
                g.add((pokemon_uri, SCHEMA[key], Literal(value)))
        
    return g

def types_to_rdf():
    g = Graph()
    for type_name, infos in types.items():
        type_uri = TYPES[type_name]
        g.add((type_uri, RDF.type, SCHEMA.Thing))
        g.add((type_uri, SCHEMA.name, Literal(type_name)))
        for key, value in infos.items():
            
            for k, v in value.items():
                for i in range(len(v)):
                    g.add((type_uri, SCHEMA[key+"_"+k], TYPES[v[i]]))
    return g

def main():
    pokemon_list = get_pokemon_list()
    i = 0
    for pokemon in pokemon_list:
        print(pokemon)
        i += 1
        if(i > 10):
            break
        infobox = get_infobox(pokemon)
        properties = parse_infobox(infobox)
        pokemons[pokemon] = properties
    #convert types to rdf
    rdf_graph = generate_rdf(pokemons)
    ttl = types_to_rdf().serialize(format="turtle")
    with open("types.ttl", "wb") as f:
        f.write(ttl.encode("utf-8"))
    with open("pokemon.ttl", "wb") as f:
        f.write(rdf_graph.serialize(format="turtle").encode("utf-8"))
    with open("generations.ttl", "wb") as f:
        ttl = generation_to_rdf(generations).serialize(format="turtle")
        f.write(ttl.encode("utf-8"))
    with open("abilities.ttl", "wb") as f:
        ttl = ability_to_rdf(abilities).serialize(format="turtle")
        f.write(ttl.encode("utf-8"))

    


if __name__ == "__main__":
    main()
