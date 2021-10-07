from unicodedata import name
from lxml import etree as ET
from entity_cache import EntityCache
from viaf_extractor import extract_viaf_id
from cmdi_extractor import read_cmdi, get_name, tag_list, get_namespace
import re
import argparse
import os
import csv


def load_cache(save_path, delimiter, specification):
    """
    This method loads a cache from a given save_path
    :param save_path: The path where the cache is stored
    :param delimiter: The delimiter used in the CSV for the cache
    :specification: the specification of the column
    :return: the cache object that can be used to modify the CMDIs
    """
    cache = EntityCache(filepath=save_path,
                        delimiter=delimiter,
                        specification=specification,
                        create_new=False)
    return cache


def add_auth_ids(cmdi, namespace, tag, authoritytag, cache):
    """
    This method adds all authoritative IDs to a specified CMDI
    :param cmdi: The CMDI file as XML element tree
    :param namespace: The namespace URI for the tag
    :param tag: The parent tag where the authoritytag should be located
    :param authoritytag: The Name of the authority tag
    :param cache: The cache object
    :return: The modified CMDI file
    """
    parent_auth_tag = authoritytag + "s"
    # query to search for specified tag
    query = './/{%s}%s' % (namespace, tag)
    entities = cmdi.findall(query)

    # iterate through all entities and add ids
    for entity in entities:
        cmdi, contains_ver_id = _add_ver_id(cmdi, namespace, tag, authoritytag, cache, entity)

        # if a verified id is already in the CMDI, delete all (possibly) remaining candidate IDs
        if contains_ver_id:
            try:
                entity.remove(entity.find("{"+namespace+"}" + ("candidate"+parent_auth_tag)))
            except Exception:
                pass
        # if no verified id is found, add candidate ids from the cache
        else:
            cmdi = _add_cand_id(cmdi, namespace, tag, ("candidate"+authoritytag), cache, entity)

    return cmdi


def _add_ver_id(cmdi, namespace, tag, authoritytag, cache, entity):
    parent_auth_tag = authoritytag + "s"
    name = get_name(entity)
    authority_ids = cache.get_entity_verified_viaf(name)

    # return unmodified cmdi if no id in cache
    if authority_ids is None:
        return cmdi, False
    
    # add parent tag (e.g. "AuthoritativeIDs") in case there is none
    auth_ids_tag = entity.find("{"+namespace+"}" + parent_auth_tag)
    if auth_ids_tag is None:
        auth_ids_tag = ET.SubElement(entity, "{"+namespace+"}"+parent_auth_tag)
    
    # if there is a parent tag, check if it contains a VIAF id
    else:
        auth_id_child2 = auth_ids_tag.xpath('.//cmdp:issuingAuthority[text()="VIAF"]', namespaces={'cmdp':namespace})
        if len(auth_id_child2) > 0:
            return cmdi, True

    # add the VIAF id if none was found so far
    auth_id = ET.SubElement(auth_ids_tag, "{"+namespace+"}"+authoritytag)
    auth_id_child = ET.SubElement(auth_id, "{"+namespace+"}id").text = f"http://viaf.org/viaf/{authority_ids.item()}"
    auth_id_child2 = ET.SubElement(auth_id, "{"+namespace+"}issuingAuthority").text = "VIAF"
    return cmdi, True



def _add_cand_id(cmdi, namespace, tag, authoritytag, cache, entity):
    parent_auth_tag = authoritytag + "s"
    name = get_name(entity)
    authority_ids = cache.get_entity_candidate_viafs(name)

    # return unmodified cmdi if no id in cache
    if authority_ids is None:
        return cmdi
    
    # add parent tag (e.g. "candidateAuthoritativeIDs") in case there is none
    auth_ids_tag = entity.find("{"+namespace+"}" + parent_auth_tag)
    ids_in_cmdi = []
    if auth_ids_tag is None:
        auth_ids_tag = ET.SubElement(entity, "{"+namespace+"}"+parent_auth_tag)
    # if there is a parent tag, get all candidate ids that are already in the CMDI to avoid repitition
    else:
        for cand_id in entity.findall(".//{%s}%s" % (namespace, "id")):
            ids_in_cmdi.append(cand_id.text)

    # add all remaining ids from the cache that are not already in the CMDI
    for a_id in authority_ids:
        for a_id_split in a_id.split(','):
            if a_id_split not in ids_in_cmdi:
                auth_id = ET.SubElement(auth_ids_tag, "{"+namespace+"}"+authoritytag)
                auth_id_child = ET.SubElement(auth_id, "{"+namespace+"}id").text = a_id_split
                auth_id_child2 = ET.SubElement(auth_id, "{"+namespace+"}issuingAuthority").text = "VIAF"

    return cmdi

def cache_to_cmdi(cache, cmdi, args):
    # traverse through all namespaces:tags and modify the CMDI
    tag_l = tag_list(args.namespace_tag_list)
    for prefix, tag, entity_type in tag_l:
        namespace = get_namespace(cmdi, prefix)
        cmdi = add_auth_ids(cmdi, namespace, tag, args.authoritative_tag, cache)


def cmdi_to_string(cmdi):
    return ET.tostring(cmdi, pretty_print=True, encoding="utf-8")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_cache",
                        help="the path for the cache that stores the entities and their authorative IDs.", type=str)
    parser.add_argument("cmdi_files", type=str,
                        help="the path to the directory that contains all cmdi files. can be a complex hierachy.")
    parser.add_argument("specification", type=str,
                        help="this json file lets you specifiy your own column names for the cache")
    parser.add_argument("namespace_tag_list", type=str, nargs="?", default="", 
                        help="a CSV containing namespaces, tags and entity type (Personal, Geographic, Corporate) ")
    parser.add_argument("authoritative_tag", help="the authoritative_tag", type=str)
    parser.add_argument("new_cmdis", help="the path for the updated CMDIs. Can't be the input directory", type=str)
    parser.add_argument("--delimiter", help="the delimiter to save the cache with", type=str, default="\t")
    args = parser.parse_args()

    cache = load_cache(args.path_to_cache, args.delimiter, args.specification)

    # check that output directory is not the same as input directory to avoid overwriting the original CMDIs
    if os.path.exists(args.new_cmdis):
        if os.path.samefile(args.cmdi_files, args.new_cmdis):
            print("Output directory can't be the input directory. Please specify a new one.")
            quit()

    c = 0
    # traverse through directory structure
    for subdir, dirs, files in os.walk(args.cmdi_files):
        if files:
            for file in files:
                cmdi = read_cmdi(subdir + "/" + file)

                cache_to_cmdi(cache, cmdi, args)
                # create the path (mirroring the original one) and save the modified CMDI there
                new_save_path = args.new_cmdis + "/" + subdir[len(args.cmdi_files):] + "/" + file
                os.makedirs(os.path.dirname(new_save_path), exist_ok=True)
                et = ET.ElementTree(cmdi)
                et.write(new_save_path, pretty_print=True, encoding="utf-8")
                print(new_save_path)
                c += 1
    print("CMDIs found:", c)

