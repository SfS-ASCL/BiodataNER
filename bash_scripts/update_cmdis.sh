#!/usr/bin/env bash
path_to_cache="/Users/nwitte/PycharmProjects/biodataNER/cmdis/caches/persons.csv"
cmdi_files="cmdis/data"
namespace="http://www.clarin.eu/cmd/1/profiles/clarin.eu:cr1:p_1527668176124"
entity_tag="Person"
authoritative_tag="AuthoritativeID"
specification="/Users/nwitte/PycharmProjects/biodataNER/cmdis/entity_spec"
new_cmdis="/Users/nwitte/PycharmProjects/biodataNER/cmdis/updated_cmdis"

python3 update_cmdi.py $path_to_cache $cmdi_files $namespace $entity_tag $authoritative_tag $specification $new_cmdis --add_candidates
