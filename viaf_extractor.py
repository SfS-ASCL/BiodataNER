#!/usr/bin/env python3

import requests
import xml.etree.ElementTree as et
import re
import json
import unicodedata as unicode


class Candidate:
    def __init__(self, viaf_id, name, birthyear, wiki_links, nation):
        self.viaf_id = viaf_id  # str
        self.name = name  # the name (as it appears in the dataset)
        self.birthyear = birthyear  # str
        self.wiki_links = wiki_links  # list with wikipedia links
        self.nation = nation  # set

    def __repr__(self):
        return str(self.viaf_id) + " : " + self.name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.viaf_id == other.viaf_id


def extract_viaf_id(authority_name, authority_type):
    """Extract Viaf IDs for given authority_name
    Parameters:
    -----------
    authority_name: given name to search ID
    authority_type: Type to search for
                    "Personal" to search for a Person ID
                    "Geographic" to search for a Location ID
                    "Corporate" to search for an Organization ID
    Returns: results, list with all IDs for given name
    """
    # authority_type: Personal=Person, Geographic=Location, Org=Corporate
    base_url = "https://viaf.org/viaf/search?sortKeys=holdingscount&httpAccept=text/xml&recordSchema=http://viaf.org" \
               "/BriefVIAFCluster&maximumRecords=250&query=local.mainHeadingEl%20all%20%22"
    url = ''.join([base_url, authority_name, "%22"])

    r = requests.get(url)
    xml_content = r.text

    tree = et.ElementTree(et.fromstring(xml_content))
    root = tree.getroot()

    name_regex = re.compile(r"(, )?[0-9]{3,}.*$")  # regex to remove potential year numbers after a name
    candidate_count = 0
    results = []

    # search for name using SRU Search
    for record in root.findall(".//{http://www.loc.gov/zing/srw/}record"):

        if candidate_count == 10:
            return results

        viaf_id = record.find(".//{http://viaf.org/viaf/terms#}viafID").text

        # extract name from xml
        for name in record.findall(".//{http://viaf.org/viaf/terms#}text"):

            if record.find(".//{http://viaf.org/viaf/terms#}nameType").text == authority_type:
                name_mod = re.sub(name_regex, "", name.text)

                # put last and first name in the correct order (first_name last_name)
                if ',' in name_mod:
                    tmp_name = name_mod.split(',')
                    name_mod = tmp_name[1].strip() + " " + tmp_name[0].strip()

                if unicode.normalize('NFC', name_mod) == authority_name or unicode.normalize('NFC',
                                                                                             name_mod) == \
                        authority_name[
                        :-1]:
                    candidate_count += 1
                    tmp_tuple = extract_information(viaf_id)
                    results.append(Candidate(viaf_id, authority_name, tmp_tuple[0], tmp_tuple[1], tmp_tuple[2]))
                    break

    # if search via xml not successful, try AutoSuggest
    if candidate_count == 0:
        base_url = "http://viaf.org/viaf/AutoSuggest?query="
        url = ''.join([base_url, authority_name])

        r = requests.get(url)
        data = json.loads(r.text)

        if data["result"]:
            for record in data["result"]:
                name = record["term"]
                viaf_id = record["viafid"]

                name_mod = re.sub(name_regex, "", name).strip()

                # put last and first name in the correct order (first_name last_name)
                if ',' in name_mod:
                    tmp_name = name_mod.split(',')
                    name_mod = tmp_name[1].strip() + " " + tmp_name[0].strip()

                if (unicode.normalize('NFC', name_mod) == authority_name or unicode.normalize('NFC',
                                                                                              name_mod) ==
                    authority_name[
                    :-1]) and \
                        record["nametype"] == authority_type.lower():
                    tmp_tuple = extract_information(viaf_id)
                    results.append(Candidate(viaf_id, authority_name, tmp_tuple[0], tmp_tuple[1], tmp_tuple[2]))

    # experimental, try full search
    base_url = "http://viaf.org/viaf/search?&sortKeys=holdingscount&httpAccept=text/xml&query=local.names%20all%20%22"
    url = ''.join([base_url, authority_name, "\""])

    r = requests.get(url)
    xml_content = r.text
    tree = et.ElementTree(et.fromstring(xml_content))
    root = tree.getroot()

    for record in root.findall(".//{http://www.loc.gov/zing/srw/}record"):

        if candidate_count == 10:
            return results

        viaf_id = record.find(".//{http://viaf.org/viaf/terms#}viafID").text

        # extract name from xml
        for entry in record.findall(".//{http://viaf.org/viaf/terms#}x400"):

            if record.find(".//{http://viaf.org/viaf/terms#}nameType").text == authority_type:

                cur_cand_count = candidate_count

                for name in entry.findall(".//{http://viaf.org/viaf/terms#}subfield"):

                    if record.find(".//{http://viaf.org/viaf/terms#}nameType").text == authority_type:
                        name_mod = re.sub(name_regex, "", name.text)

                        # put last and first name in the correct order (first_name last_name)
                        if ',' in name_mod:
                            tmp_name = name_mod.split(',')
                            name_mod = tmp_name[1].strip() + " " + tmp_name[0].strip()

                        if unicode.normalize('NFC', name_mod) == authority_name or unicode.normalize('NFC',
                                                                                                     name_mod) == \
                                authority_name[
                                :-1]:
                            candidate_count += 1
                            tmp_tuple = extract_information(viaf_id)
                            c = Candidate(viaf_id, authority_name, tmp_tuple[0], tmp_tuple[1], tmp_tuple[2])

                            if c not in results:
                                results.append(c)
                            break

                if cur_cand_count != candidate_count:
                    break

    return results


def extract_information(viaf_id):
    """Extract various informations such as birthday, nationality or wikipedia links for a given viaf_id
    """
    url = "https://viaf.org/viaf/" + viaf_id + "/viaf.xml"
    r = requests.get(url)
    xml_content = r.text

    tree = et.ElementTree(et.fromstring(xml_content))
    root = tree.getroot()

    # get birthyear
    birthdate = root.find(".//{http://viaf.org/viaf/terms#}birthDate").text

    # get nationality
    nation = set()
    for nationality in root.findall(
            ".//{http://viaf.org/viaf/terms#}nationalityOfEntity//{http://viaf.org/viaf/terms#}text"):
        nation.add(nationality.text)

    # get wikipedia links
    links = []
    for link in root.findall(".//{http://viaf.org/viaf/terms#}xLink[@type='Wikipedia']"):
        links.append(link.text)

    return (birthdate, links, nation)
