import argparse

from cmdi_extractor import read_cmdi, get_names_with_ids
from person_cache import PersonCache
from viaf_extractor import extract_viaf_id



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_cmdi")
    args = parser.parse_args()

    cmdi = read_cmdi(args.path_to_cmdi)
    persons, person2viaf = get_names_with_ids(cmdi, "http://www.clarin.eu/cmd/1/profiles/clarin.eu:cr1:p_1527668176122",
                                              "Person", "AuthoritativeIDs")

