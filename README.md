# BiodataNER

## General Info

This repository contains the code for a use case project, that can be used for the BioData project.

The goal is to extract a number of entities from given CMDI metadata records (possible entities have to be specified with tag names (e.g. an entity can be listed under 'Person' or 'Organization'. For the extracted entities for a given metadata tag a cache of candidate VIAF IDs and verified VIAF IDs is constructed. From these caches, the CMDI can be updated to contain the candidate or verified VIAF IDs for the entities, if they were not already present in the original data.


## prerequisites
you need the following packages in your python3 enviroment:

- lxml (4.6.1)
- pandas (1-1-4)

## usage


you can use two functionilities. either you want to create or update a cache object for a specific entity type based on a bunch of cmdis

### create or update a cache

the file that is reponsible for that is python_scripts/cmdi_extractor.py 

you can either call it manually or use the script bash_scripts/create_cache.sh with your arguments. You have to specifiy the directory where your cmdi files are located which you want to extract entities for. you can start with creating a new cache and then run the script several times to update the existing cache. for example you may want to start a new cache for persons with the script similar to the example script in bash_scripts. This will extract IDs for all names that can be found under the "Person" tag in any of the cmdis, given the specified profile. in the next run, remove the flag --new_cache to update this cache with a different profile (and so on). Afterwards to the same for all names found under the tag "LegalOwner" or "Author" etc. Do the same for organizations, but this time change the argument "entity_type". All arguments are described in the help for the python script.

### update cmdi files with cache

the file that is reponsible for that is python_scripts/update_cmdi.py

you can either call it manually or use the script bash_scripts/update_cmdis.sh with your arguments. it works similar to the first script. This script iterates over all cmdi files and extracts all names that were asked for (as in the first script). then it looks up a name in the cache and adds an ID if available to a new cmdi. it stores a new cmdi in the given directory. the script reproduces the original structure of all cmdi files in the new directory, that can be specified as an argument. the name of the cmdi will be exactly the same as the one of the original. The original directory cannot be specified so that the original cmdi files cannot be overwritten. 

