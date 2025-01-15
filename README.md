# SemanticPokedex
Group composed of: 
    - Nicolas REYMOND-FORKANI 
    - Marie-Louise DESSELIER

To launch our project, there are several prerequisites: 
    - Have Fuseki installed on your machine 
    - Have a stable version of Java installed on your machine

We used the following libraries and tools: - Pywikibot - Pickle - rdflib - urllib - Requests
So you must create a file requirement.txt with the key word write above and run the following command : pip install requirement.txt

The Knowledge Graph is in the root folder inside KG.ttl

Steps to follow: 
    - Start Fuseki 
    - Go to the address: "http://localhost:3030/" 
    - Create a new dataset: "pokedex" 
    - If you want to generate the turtle files you must run the file main.py
    - Upload the 6 Turtle files 
    - Run in your terminal : py server.py
    - Go to the address: "http://localhost:8000/" then add the following suffixes to the URL depending on what you want to display: 
        - index/generation/generation_{generation_number} 
        - index/pokemon/{pokemon_name}_{Pokémon}
        - index/Types/{type}
    -Then you could navigate by clicking on the different link on the page 


