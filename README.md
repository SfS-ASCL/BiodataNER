# BiodataNER

## General Info

This repository contains the code for a use case project, that can be used for the BioData project.

The goal is to extract a number of entities from given CMDI metadata records (possible entities have to be specified with tag names (e.g. an entity can be listed under 'Person' or 'Organization'. For the extracted entities for a given metadata tag a cache of candidate VIAF IDs and verified VIAF IDs is constructed. From these caches, the CMDI can be updated to contain the candidate or verified VIAF IDs for the entities, if they were not already present in the original data.
