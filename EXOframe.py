import os
import sys
import json

import icFileUtils as icFU

DEFAULT_SECTIONS = {"assets": {},
                    "shots": {},
                    "shaders": {"archive": {}},
                    "other": {},
                    "_trashbin": {}}

DEFAULT_ASSET_STRUCTURE = {"dev": {},
                           "lookdev": {},
                           "sourceimages": {}}

DEFAULT_SHOT_STRUCTURE = {"dev": {},
                          "playblast": {},
                          "lookdev": {},
                          "renders": {},
                          "composite": {},
                          "movies": {}}

DEFAULT_OTHER_STRUCTURE = {"dev": {}}


# TODO: make this all more dynamic.


class Project(object):
    def __init__(self, root):
        self.path = root
        self.assetpath = self.path + r"\assets"
        self.shotpath = self.path + r"\shots"
        self.shaderpath = self.path + r"\shaders"
        self.otherpath = self.path + r"\other"
        self.datafilepath = self.path + r"\.EXOpipeline"
        self.trashpath = self.path + r"\_trashbin"

        self.data = self.get_pipeline_data()

    def get_pipeline_data(self):
        """
        Helper function to load the JSON data in from the datafile.

        :return: dict
        """
        if not os.path.isfile(self.datafilepath):
            print "file not found"
            data = DEFAULT_SECTIONS
            icFU.dict_to_folders(data, self.path)
            icFU.write_json_file(data, self.datafilepath)

        else:
            data = open(self.datafilepath)
            data = json.load(data)

        return data

    def add_asset(self, assetname, assetdata):
        self.data["assets"].update(assetdata)
        icFU.dict_to_folders(DEFAULT_ASSET_STRUCTURE, self.assetpath + "/" + assetname)
        self.update()

    def delete_asset(self, assetname):
        del self.data["assets"][assetname]
        icFU.move_folder(self.assetpath + "/" + assetname, self.trashpath)
        self.update()

    def add_shot(self, shotname, shotdata):
        self.data["shots"].update(shotdata)
        icFU.dict_to_folders(DEFAULT_SHOT_STRUCTURE, self.shotpath + "/" + shotname)
        self.update()

    def delete_shot(self, shotname):
        del self.data["shots"][shotname]
        icFU.move_folder(self.shotpath + "/" + shotname, self.trashpath)
        self.update()

    def add_other(self, othername, otherdata):
        self.data["other"].update(otherdata)
        icFU.dict_to_folders(DEFAULT_OTHER_STRUCTURE, self.otherpath + "/" + othername)
        self.update()

    def delete_other(self, othername):
        del self.data["other"][othername]
        icFU.move_folder(self.otherpath + "/" + othername, self.trashpath)
        self.update()

    def add_setdata(self, setdata):
        if "setdata" not in self.data.keys():
            self.data.update({"setdata": {}})
        self.data["setdata"].update(setdata)
        self.update()

    def delete_setdata(self, setname):
        del self.data["setdata"][setname]
        self.update()

    def update(self):
        icFU.write_json_file(self.data, self.datafilepath)


class Asset(Project):
    _inherited = ["path", "assetpath", "shotpath", "shaderpath", "otherpath", "datafilepath", "trashpath"]

    def __init__(self,
                 project,
                 name,
                 dev=0,
                 lookdev=0,
                 published=False,
                 shaderrelations={}):
        self.name = name
        self.devversions = dev
        self.lookdevversions = lookdev
        self.shaders = shaderrelations
        self.published = published
        self._parent = project

    def __repr__(self):
        return "Name: {0} \n" \
               "DEV Versions: {1} \n" \
               "Published: {2} \n" \
               "LOOKDEV Versions: {3} \n" \
               "Shader relations: {4} \n".format(self.name,
                                                 self.devversions,
                                                 self.published,
                                                 self.lookdevversions,
                                                 self.shaders)

    def __getattr__(self, item):
        if item in self._inherited:
            return getattr(self._parent, item)
        return self.__dict__[item]


class Shot(Project):
    _inherited = ["path", "assetpath", "shotpath", "shaderpath", "otherpath", "datafilepath", "trashpath"]

    def __init__(self,
                 project,
                 name,
                 dev=0,
                 lookdev=0,
                 published=False,
                 camera=""):
        self.name = name
        self.devversions = dev
        self.lookdevversions = lookdev
        self.camera = camera
        self.published = published

        self._parent = project

    def __repr__(self):
        return "Name: {0} \n" \
               "DEV Versions: {1} \n" \
               "Published: {2} \n" \
               "LOOKDEV Versions: {3} \n" \
               "Camera: {4} \n".format(self.name, self.devversions, self.published, self.lookdevversions, self.camera)

    def __getattr__(self, item):
        if item in self._inherited:
            return getattr(self._parent, item)
        return self.__dict__[item]


class Other(Project):
    _inherited = ["path", "assetpath", "shotpath", "shaderpath", "otherpath", "datafilepath", "trashpath"]

    def __init__(self,
                 project,
                 name,
                 dev=0):
        self.name = name
        self.devversions = dev
        self._parent = project

    def __repr__(self):
        return "Name: {0} \n" \
               "DEV Versions: {1} \n".format(self.name, self.devversions)

    def __getattr__(self, item):
        if item in self._inherited:
            return getattr(self._parent, item)
        return self.__dict__[item]