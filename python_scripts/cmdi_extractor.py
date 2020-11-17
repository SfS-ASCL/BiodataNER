import xml.etree.ElementTree as ET
from entity_cache import EntityCache
from viaf_extractor import extract_viaf_id
import re
import argparse
import os


def get_name(node):
    """
    This method tries to extract a name (String) given a node. it is assumed that the name is specified by one or
    several
    subchildren of the node (e.g. firstname, lastname, fundingAgency). if no match can be found, None is returned
    :param node: the elment to which a corresponding name should be extracted
    :return: None, if no name can be found, or the name (String)
    """
    name = ""
    for child in node:
        if "name" in child.tag.lower() or "agency" in child.tag.lower():
            if name != "":
                name += " " + child.text
            else:
                if child.text:
                    name += child.text
    if name == "":
        return None
    return name


def get_names_with_ids(cmdi, namespace, tag, authoritytag):
    """
    This method takes a cmdi element tree as input. For a given entity type it returns all corresponding names.
    If authority IDs available (XML tag defined by 'authoritytag'), the map returned will contain a name with the
    corresponding VIAF ID found in the xml
    :param cmdi: the CMDI file as element tree
    :param namespace: the namespace of the CMDI file
    :param tag: the tag for all entities that should be searched for within the CMDI (e.g. 'Person', 'Contact'...)
    :param authoritytag: the tag for authority files (e.g. 'AuthoritativeID')
    :return: a tuple of (set: names, dict: name2viaf). the set contains all names found in the CMDI (corresponding to
    the given entity tag. the dictionary contains names with their corresponding VIAF IDs (if that information is in
    the given CMDI
    """
    # this will keep track of all found named entities
    names = set()
    # this will store a name with a corresponding VIAF ID
    name2viaf = {}
    # this pattern matches any (longer) number, e.g. '234'
    number = re.compile("\d+")
    # this query extracts all entities from the CMDI, e.g. if the XML element you are interested in is 'Person' this
    # query will extract all 'Persons' form the CMDI
    query = './/{%s}%s' % (namespace, tag)
    entities = cmdi.findall(query)
    # iterate over all entities that were found
    for entity in entities:
        # search for authority files, the tag under which they are listed can be specified as an argument
        authorityquery = './/{%s}%s' % (namespace, authoritytag)
        authorities = entity.findall(authorityquery)
        # try to retrieve the name of the entity, this can be specified by one or several children of the current
        # element
        name = get_name(entity)
        # if there were no children of the entity, the name might be specified in the entity element itself (i.e. in
        # <LegalOwner xml:lang="en">Thorsten Trippel</LegalOwner>, the name 'Thorsten Trippel' is the content of the
        # element itself
        if not name and entity.text:
            # this will be the content of the element and thus now the name
            name = entity.text.strip()
        if name:
            names.add(name)
            # if there are children containing authority files
            if authorities:
                for authority in authorities:
                    # find the authority type "VIAF" and store the id and the corresponding name in the dictionary
                    id = authority.find('{%s}id' % namespace).text
                    if id:
                        id = re.search(number, id).group(0)
                        type = authority.find('{%s}issuingAuthority' % namespace).text
                        if id and type and "VIAF" in type and name not in name2viaf:
                            print(str(int(id)))
                            name2viaf[name] = str(int(id))
    return names, name2viaf


def read_cmdi(cmdi_path):
    """
    Given a path to a cmdi file, read in the XML with elemt tree
    :param cmdi_path: a path to a CMDI xml file
    :return: the parsed XML as element tree
    """
    # given a path to a cmdi xml, read in the xml
    with open(cmdi_path) as in_f:
        try:
            tree = ET.parse(in_f)
        except ET.ParseError as e:
            print("error while parsing xml -- valid CMDI file?")
            return str(e)
    root = tree.getroot()
    return root


def create_cache(save_path, delimiter, specification, new):
    """
    This method creates a new cache with the given specifications. The cache will be stored under the save_path.
    :param save_path: The path where the cache will be stored to
    :param delimiter: The delimiter for the column-based format
    :param specification: the specification of the column (column names can be specified in there)
    :param new: if the cache is new, a new will be created, if the cache exists, the exiting cache will be read in
    and can be updated
    :return: the cache object that can be used to enter new entities
    """
    cache = EntityCache(filepath=save_path,
                        delimiter=delimiter,
                        specification=specification, create_new=new)
    return cache


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_cache",
                        help="the path for the cache that stores the entities and their authorative IDs. If there is "
                             "no existing cache under the specified path, set the flac new_cache to create a new "
                             "cache. if the cache is already present do not set the flag. the cache will be used and "
                             "updated.", type=str)
    parser.add_argument("cmdi_files", type=str,
                        help="the path to the directory that contains all cmdi files. can be a complex hierachy.")
    parser.add_argument("namespace", type=str,
                        help="the namespace of the cmdi files you work with, "
                             "e.g. 'http://www.clarin.eu/cmd/1/profiles/clarin.eu:cr1:p_1527668176122'")
    parser.add_argument("entity_tag", type=str,
                        help="the XML element for which you would like to extract IDs, e.g. 'Person' or 'Contact'")
    parser.add_argument("authoritative_tag", type=str,
                        help="the XML element which is the parent of the authority IDs, e.g. AuthoritativeID")
    parser.add_argument("specification", type=str,
                        help="this json file lets you specifiy your own column names for the cache")
    parser.add_argument("entity_type", type=str, help="which type of entity are we looking for?",
                        choices=["Personal", "Geographic", "Corporate"])
    parser.add_argument("--delimiter", help="the delimiter to save the cache with", type=str, default="\t")
    parser.add_argument("--new_cache", help="set this flag if you want to create a new cache",
                        action="store_true")
    args = parser.parse_args()

    cache = create_cache(save_path=args.path_to_cache, new=args.new_cache, delimiter=args.delimiter,
                         specification=args.specification)
    for subdir, dirs, files in os.walk(args.cmdi_files):
        if files:
            cmdi = read_cmdi(subdir + "/" + files[0])
            print(subdir + "/" + files[0])
            entities, entity2viaf = get_names_with_ids(cmdi, args.namespace, args.entity_tag, args.authoritative_tag)
            for e in entities:
                if e in entity2viaf and not cache.has_verified_viaf(e):
                    cache.enter_entity(e)
                    verified_viaf = entity2viaf[e]
                    cache.enter_verified_viaf(e, verified_viaf)
                if not cache.has_candidate_viaf(e) and not cache.has_verified_viaf(e):
                    ids = extract_viaf_id(authority_name=e, authority_type=args.entity_type)
                    candidate_ids = [el.viaf_id for el in ids]
                    if candidate_ids:
                        cache.enter_entity(e)
                        candidate_ids = ",".join(candidate_ids)
                        entry = cache.get_entry(e)
                        cache.enter_candidate_viafs(e, candidate_ids.strip())
    cache.write_cache()
    print("cache stored to %s" % args.path_to_cache)
