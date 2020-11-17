#!/usr/bin/env bash
path_to_cache="/Users/nwitte/PycharmProjects/biodataNER/cmdis/caches/persons.csv"
cmdi_files="/Users/nwitte/PycharmProjects/biodataNER/cmdis/data"
namespace="http://www.clarin.eu/cmd/1/profiles/clarin.eu:cr1:p_1527668176124"
entity_tag="Contact"
authoritative_tag="AuthoritativeID"
specification="/Users/nwitte/PycharmProjects/biodataNER/cmdis/entity_spec"
entity_type="Personal"

python3 cmdi_extractor.py $path_to_cache $cmdi_files $namespace $entity_tag $authoritative_tag $specification $entity_type
