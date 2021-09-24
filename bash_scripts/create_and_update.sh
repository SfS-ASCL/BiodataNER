#!/usr/bin/env bash
path_to_cache="cache2.csv"
cmdi_files="data/"
authoritative_tag="AuthoritativeID"
specification="entity_spec.json"
namespace_tag_list="namespaces_tags.csv"
new_cmdis="updated_cmdis"

python3 python_scripts/cmdi_extractor.py $path_to_cache $cmdi_files $authoritative_tag $specification $namespace_tag_list $1 --new_cache
echo "cache created"
echo "begin updating CMDIs"
python3 python_scripts/update_cmdi.py $path_to_cache $cmdi_files $specification $namespace_tag_list $authoritative_tag $new_cmdis