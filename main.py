import pywikibot
pokedex = {}
default_rdf_url = 'http://pokedex.exemple.com/object#'
default_rdf_classes = 'http://pokedex.exemple.com/classes#'
site = pywikibot.Site()
# Initialisation de la variable globale pokedex

def add_to_pokedex(page_title):
    page = pywikibot.Page(site, page_title)
    
    if page.isRedirectPage():
        page = page.getRedirectTarget()
    
    text = page.text
    
    # Extraction des informations de l'infobox
    infobox = {}
    lines = text.split('\n')
    infobox_started = False
    
    for line in lines:
        if line.strip().startswith('{{Pokémon Infobox'):
            infobox_started = True
        if infobox_started:
            if line.strip().startswith('|'):
                key_value = line.strip().split('=', 1)
                if len(key_value) == 2:
                    key = key_value[0].strip('|').strip()
                    value = key_value[1].strip()
                    infobox[key] = value
            if line.strip().startswith('}}'):
                break
    
    # Ajout de l'infobox au pokedex
    pokedex[page_title] = infobox

classes = {
    "Pokémon": {

    }
}

def convert_to_rdf(pokemon):
    pok = pokedex[pokemon]
    rdf = ''
    rdf += 'obj:'+ pokemon + ' a class:Pokémon\n'
    rdf += ';   rdfs:label "' + pokemon + '"@en\n'
    for key, value in pok.items():
        #check type of value to convert to corresponding xsd type
        vtype = '@en'
        if value.isdigit():
            vtype = '^xsd:integer'
        elif value.replace('.','',1).isdigit():
            vtype = '^xsd:float'
        elif value.lower() in ['true', 'false']:
            vtype = '^xsd:boolean'
        elif value.startswith('[') and value.endswith(']'):
            vtype = '^xsd:List'
        rdf += ';    prop:'+ key + ' "' + value + '"'+vtype+'\n'

    return rdf + '.\n'

def convert_pokedex_to_rdf():
    rdf = ''
    for pokemon in pokedex:
        rdf += convert_to_rdf(pokemon)
    return rdf

#to do : Créer les classes et catégories

page = pywikibot.Page(site, f'Template:Pokémon Infobox')
params = { 'action': 'parse', 'page': page.title(), 'prop': 'templates', 'format' : 'json' }
r = pywikibot.data.api.Request(site=site, **params).submit()
templates = r['parse']['templates']
print(templates)