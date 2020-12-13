import pandas as pd
import json


class EntityCache:

    def __init__(self, filepath, delimiter, specification, output_warnings=True, create_new=False):
        """
        This class stores a Cache
        :param filepath:
        :param delimiter:
        :param specification:
        :param create_new:
        """
        # read the specification (you can specify the names of your columns in the json file)
        try:
            print("JSON File:", specification)
            with open(specification) as jsonfile:
                column_spec = json.load(jsonfile)
        except IOError:
            print("json specification could not be read, please check the json file")
        self._filepath = filepath
        self._delimiter = delimiter
        self._name = column_spec["name"]
        self._alias = column_spec["alias"]
        self._candidateVIAF = column_spec["candidateVIAF"]
        self._verifiedVIAF = column_spec["verifiedVIAF"]
        self._warnings = output_warnings
        if create_new:
            self._cache = pd.DataFrame(columns=list(column_spec.keys()))
        else:
            try:
                self._cache = pd.read_csv(filepath, delimiter=delimiter, index_col=0)
            except IOError:
                print("csv file could not be read, please check your database")

    def get_entity_candidate_viafs(self, name):
        """
        This method returns the candidate VIAF IDs as a string, if there are several IDs, they are separated by a comma
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: the candidate IDs of a given first and last name, prints a warning and returns None if there are no
        candidate IDs
        """
        if self.has_candidate_viaf(name):
            return self.get_entry(name)[self.candidateVIAF]
        else:
            print("the entity %s has no candidate VIAF IDs in the cache" % name)
            return None

    def get_entity_verified_viaf(self, name):
        """
        This method returns the verified VIAF IDs as a string.
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: the verified VIAF ID of a given first and last name, prints a warning  and returns None if there is
        no verified ID or if the entity is ambiguous
        """
        if self.has_verified_viaf(name):
            return self.get_entry(name)[self.verifiedVIAF]
        else:
            print("the entity %s has no candidate VIAF IDs in the cache" % name)
            return None

    def enter_entity(self, name):
        """
        This method will enter a new entity into the cache if the entity does not have an existing entry
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        """
        if self.has_entry(name):
            print("the entity %s already has an entry in the dataframe" % name)
        else:
            current_index = self.size
            self._cache.at[current_index, self.name] = name

    def get_entry(self, name):
        """
        This method will return the entry of a entity, based on the first and last name
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: a DataFrame object, containing the entry matching the entity or None if there is no entry in the cache
        """
        if self.has_entry(name):
            return self._cache.loc[
                (self._cache[self.name] == name)]
        else:
            print("the entity %s has no entry in the cache" % name)

    def has_entry(self, name):
        """
        Checks whether there is an existing entry in the cache for a specific entity
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: a boolean, true if the entity has an entry and false if not
        """
        existing_entry = self._cache.loc[
            (self._cache[self.name] == name)]
        if existing_entry.empty:
            return False
        return True

    def has_verified_viaf(self, name):
        """
        This method checks whether the given entity has a verified VIAF ID in the cache
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: True if there is a verified VIAF ID, else False (either there has not been entered a verified ID or the
        entity is ambigous
        """
        if self.has_entry(name):
            entry = self.get_entry(name)
            if pd.isnull(entry[self.verifiedVIAF].item()) or entry[self.verifiedVIAF].item() == "ambig":
                return False
            else:
                return True
        return False

    def has_candidate_viaf(self, name):
        """
        This method checks whether the given entity has candidate VIAF IDs in the cache
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: True if there is are candidate VIAF IDs, else False
        """
        if self.has_entry(name):
            entry = self.get_entry(name)
            if pd.isnull(entry[self.candidateVIAF].item()):
                return False
            else:
                return True
        return False

    def get_index(self, name):
        """
        This method returns the value of the index of a given input name
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :return: None (with warning) if the entity is not in the index, else the index [int]
        """
        if self.has_entry(name):
            return self.get_entry(name).index.values[0]
        else:
            print("the entity %s has no entry in the cache" % name)
            return None

    def enter_candidate_viafs(self, name, candidate_ids):
        """
        This method allows to enter a string of candidate VIAF IDs given a first and last name
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :param candidate_ids: a String of candidate IDs, each ID is separated by a comma. Can also consist of a
        single ID.
        """
        if self.has_candidate_viaf(name):
            print("the entity %s already has verified IDs in the dataframe" % name)
        elif candidate_ids.isnumeric or candidate_ids.split(",").strip()[0].isnumeric():
            index = self.get_index(name)
            self._cache.at[index, self.candidateVIAF] = candidate_ids
        else:
            print("the input id is not a valid number")

    def enter_verified_viaf(self, name, verified_viaf):
        """
        This method allows to enter a string of candidate VIAF IDs given a first and last name
        :param name: [String] the name of the entity, e.g. Thorsten Trippel
        :param candidate_ids: a String of candidate IDs, each ID is separated by a comma. Can also consist of a
        single ID
        """
        if self.has_verified_viaf(name):
            print("the entity %s already has verified IDs in the dataframe or the entity is ambigious" % name)
        elif verified_viaf.isnumeric():
            index = self.get_index(name)
            self._cache.at[index, self.verifiedVIAF] = verified_viaf
        else:
            print("the input id is not a valid number")

    def write_cache(self):
        """
        This method dumps the column-based cache to a csv
        """
        self.cache.to_csv(self.filepath, sep=self.delimiter)

    @property
    def size(self):
        return len(self._cache.index)

    @property
    def cache(self):
        return self._cache

    @property
    def name(self):
        return self._name

    @property
    def alias(self):
        return self._alias

    @property
    def candidateVIAF(self):
        return self._candidateVIAF

    @property
    def verifiedVIAF(self):
        return self._verifiedVIAF

    @property
    def filepath(self):
        return self._filepath

    @property
    def delimiter(self):
        return self._delimiter

    @property
    def warnings(self):
        return self._warnings
