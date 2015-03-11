import os
import sys
import subprocess

import xml.etree.ElementTree as xml
from cStringIO import StringIO

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import pysideuic
import shiboken

import json
import collections

import maya.OpenMayaUI
import maya.cmds as mc
import maya.mel as mel

import EXOframe
import icFileUtils as icFU


def get_pyside_class(ui_file):
    """
    Pablo Winant
    """
    parsed = xml.parse( ui_file )
    widget_class = parsed.find( 'widget' ).get( 'class' )
    form_class = parsed.find( 'class' ).text

    with open( ui_file, 'r' ) as f:
        o = StringIO()
        frame = {}

        pysideuic.compileUi( f, o, indent = 0 )
        pyc = compile( o.getvalue(), '<string>', 'exec' )
        exec pyc in frame

        # Fetch the base_class and form class based on their type in the xml from designer
        form_class = frame['Ui_{0}'.format( form_class )]
        base_class = eval( 'QtGui.{0}'.format( widget_class ) )

    return form_class, base_class


def wrapinstance(ptr, base=None):
    """
    Nathan Horne
    """
    if ptr is None:
        return None

    ptr = long( ptr ) #Ensure type
    if globals().has_key( 'shiboken' ):
        if base is None:
            qObj = shiboken.wrapInstance( long( ptr ), QtCore.QObject )
            metaObj = qObj.metaObject()
            cls = metaObj.className()
            superCls = metaObj.superClass().className()

            if hasattr( QtGui, cls ):
                base = getattr( QtGui, cls )

            elif hasattr( QtGui, superCls ):
                base = getattr( QtGui, superCls )

            else:
                base = QtGui.QWidget

        return shiboken.wrapInstance( long( ptr ), base )

    elif globals().has_key( 'sip' ):
        base = QtCore.QObject

        return sip.wrapinstance( long( ptr ), base )

    else:
        return None


def get_maya_window():
    maya_window_util = maya.OpenMayaUI.MQtUtil.mainWindow()
    maya_window = wrapinstance( long( maya_window_util ), QtGui.QWidget )

    return maya_window

WINDOW_TITLE = "EXO Pipeline"
WINDOW_VERSION = "Alpha"
WINDOW_NAME = "exopipeline_window"

TOOLPATH = os.path.dirname(__file__)
UI_FILE = os.path.join(TOOLPATH, "EXOpipelineUI.ui")
UI_OBJECT, BASE_CLASS = get_pyside_class(UI_FILE)

DATAFILENAME = ".EXOpipeline"


class EXOpipeline(BASE_CLASS, UI_OBJECT):
    def __init__(self, parent=get_maya_window()):
        """
        Constructor for the UI

        Connect events like this:
                self.<OBJECT>.<EVENT>.connect( self.<METHOD> )
        """
        super(EXOpipeline, self).__init__(parent)
        self.setupUi(self)  # inherited

        self.setWindowTitle("{0} - {1}".format(WINDOW_TITLE, str(WINDOW_VERSION)))

        self.currentlistsection = ""
        self.devtype = ""
        self.activeasset = ""
        self.librarysection = ""
        # BUTTON EVENTS
        self.btn_setproject.clicked.connect(self.set_project)
        self.btn_showassets.clicked.connect(self.view_assets)
        self.btn_showlookdevassets.clicked.connect(self.view_assets_lookdev)
        self.btn_showanimation.clicked.connect(self.view_shots)
        self.btn_showlookdevshots.clicked.connect(self.view_shots_lookdev)
        self.btn_showother.clicked.connect(self.view_other)

        self.btn_newasset.clicked.connect(self.create_asset)
        self.btn_newshot.clicked.connect(self.create_shot)
        self.btn_newother.clicked.connect(self.hello_world)

        self.btn_open.clicked.connect(self.open_selected)
        self.btn_delete.clicked.connect(self.delete_item)
        self.btn_browse.clicked.connect(self.open_asset_dir)

        self.btn_libassets.clicked.connect(self.update_list_library_assets)
        self.btn_libsets.clicked.connect(self.update_list_library_sets)
        self.btn_libcreateset.clicked.connect(self.create_set)
        self.btn_libsaveset.clicked.connect(self.save_set)
        self.btn_libdeleteset.clicked.connect(self.delete_set)
        self.btn_libimport.clicked.connect(self.import_from_library)

        #                        self.list_library

        self.btn_save.clicked.connect(self.save_active_asset)
        self.btn_publish.clicked.connect(self.publish_active_asset)

        self.actionAbout.triggered.connect(self.display_about)

        self.action_re_load_shaders.triggered.connect(self.re_load_shaders)

        # OTHER EVENTS
        self.list_content.itemSelectionChanged.connect(self.updated_selection)

        # EXECUTE METHODS
        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, False)
        self.tabWidget.setTabEnabled(4, False)

        # SHOW
        self.show()
        self.set_project("Z:\Bestanden\Dropbox\SCRIPTBOX\EXO Project")
        self.disable_set_buttons()

    def disable_set_buttons(self):
        self.btn_libcreateset.setEnabled(False)
        self.btn_libsaveset.setEnabled(False)
        self.btn_libdeleteset.setEnabled(False)

    def enable_set_buttons(self):
        self.btn_libcreateset.setEnabled(True)
        self.btn_libsaveset.setEnabled(True)
        self.btn_libdeleteset.setEnabled(True)

    def display_about(self):
        dialog = QtGui.QMessageBox()
        dialog.setWindowTitle("About")
        dialog.setText("Developed by: Nico Klaassen \n"
                       "For purposes of managing the assets of EXO 22 - a student short film \n"
                       "\n"
                       "             www.nicoklaassen.nl \n"
                       "             klaassen.nico@gmail.com")
        dialog.exec_()

    def hello_world(self):
        print "Hello world!"

    def set_project(self, path=None):
        """
        Main function to set the project and fetch all the proper data associated with the project.
        """
        if path:
            projectpath = path
            self.textline_project.setText(path)
        else:
            projectpath = self.show_file_dialog()

        self.PROJECT = EXOframe.Project(projectpath)

        self.enable_tabs()
        self.view_assets()

    def enable_tabs(self):
        self.tabWidget.setTabEnabled(1, True)
        self.tabWidget.setTabEnabled(2, True)
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setTabEnabled(4, True)

    def warning_test(self):
        self.display_warning("test")
        raise RuntimeError("Woah! You messed up!")

    def display_warning(self, warning, title="Warning!"):
        warningdialog = QtGui.QMessageBox()
        warningdialog.setText("{0}".format(warning))
        warningdialog.setWindowTitle("{0}".format(title))
        warningdialog.exec_()

    def confirmation_test(self):
        print self.confirmation_dialog("Weet je het zeker man?")

    def confirmation_dialog(self, customtext, title="Confirmation"):
        dialog = QtGui.QMessageBox()
        dialog.setText("{0}".format(customtext))
        dialog.setWindowTitle("{0}".format(title))
        dialog.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        answer = dialog.exec_()
        if answer == QtGui.QMessageBox.Yes:
            return True
        else:
            return False

    def show_file_dialog(self):
        """
        Helper function to show a file dialogue and get the folder name from a user.

        :return: string
        """
        foldername = QtGui.QFileDialog.getExistingDirectory(self, "Select project folder.", "/home")
        self.textline_project.setText(foldername)
        return foldername

    def create_asset(self):
        assetname = self.input_assetname.text()

        if not assetname:
            raise RuntimeError("No asset name given!")
        elif assetname in self.PROJECT.data["assets"]:
            raise RuntimeError("Asset name not unique!")

        else:
            assetdata = {assetname: {"dev": 0,
                                     "lookdev": 0,
                                     "published": False,
                                     "shaderrelations": {}}}

            self.PROJECT.add_asset(assetname, assetdata)

        self.input_assetname.clear()

        self.view_assets()

    def create_shot(self):
        shotnumber = self.make_three_digit_string(int(self.input_shotnumber.text()))
        shotname = self.input_shotname.text()
        totalshotname = "shot_" + shotnumber + "_" + shotname

        if not shotname or not shotnumber or totalshotname in self.PROJECT.data["shots"]:
            raise RuntimeError("Shotname and/or number is not unique!")

        for k in self.PROJECT.data["shots"]:
            if shotnumber in k:
                raise RuntimeError("Shotnumber not unique!")

        shotdata = {totalshotname: {"dev": 0,
                                    "lookdev": 0,
                                    "published": False,
                                    "camera": ""}}

        self.PROJECT.add_shot(totalshotname, shotdata)

        self.input_shotnumber.clear()
        self.input_shotname.clear()

        self.view_shots()

    def create_other(self):
        othername = self.input_othername.text()

        if not othername:
            raise RuntimeError("No name given!")
        elif othername in self.PROJECT.data["other"]:
            raise RuntimeError("Name not unique!")

        else:
            otherdata = {othername: {"dev": 0}}

            self.PROJECT.add_other(othername, otherdata)

        self.input_othername.clear()

        self.view_other()

    def update_list_content(self, section):
        """
        Main function to show the contents of a section in the content-listwidget.

        :param section: string
        """
        self.list_content.clear()
        if self.PROJECT.data:
            for key in self.PROJECT.data["{0}".format(section)]:
                # TODO if published:
                if self.devtype == "lookdev":
                    if not self.PROJECT.data["{0}".format(section)][key]["published"]:
                        continue
                item = QtGui.QListWidgetItem("{0}".format(key))
                self.list_content.addItem(item)

    def update_version_list(self, versions):
        for i in range(versions + 1):
            if i == 0 and versions == 0:
                self.combobox_versions.insertItem(i, "new")

            elif i == 0 and versions > 0:
                self.combobox_versions.insertItem(i, "latest")

            else:
                self.combobox_versions.insertItem(i, str(i))

    def view_assets(self):
        self.currentlistsection = "assets"
        self.devtype = "dev"
        self.update_list_content("assets")

    def view_assets_lookdev(self):
        self.currentlistsection = "assets"
        self.devtype = "lookdev"
        self.update_list_content("assets")

    def view_shots(self):
        self.currentlistsection = "shots"
        self.devtype = "dev"
        self.update_list_content("shots")

    def view_shots_lookdev(self):
        self.currentlistsection = "shots"
        self.devtype = "lookdev"
        self.update_list_content("shots")

    def view_other(self):
        self.currentlistsection = "other"
        self.devtype = "dev"
        self.update_list_content("other")

    # ############################## LIBRARY

    def update_list_library_assets(self):
        self.list_library.clear()
        self.librarysection = "assets"

        for each in self.PROJECT.data["assets"]:
            published = self.PROJECT.data["assets"][each]["published"]
            if published:
                item = QtGui.QListWidgetItem("{0}".format(each))
                self.list_library.addItem(item)

        self.disable_set_buttons()

    def update_list_library_sets(self):
        self.list_library.clear()
        self.librarysection = "sets"

        if "setdata" not in self.PROJECT.data:
            self.PROJECT.data.update({"setdata": {}})

        for each in self.PROJECT.data["setdata"]:
            item = QtGui.QListWidgetItem("{0}".format(each))
            self.list_library.addItem(item)

        self.enable_set_buttons()

    def import_from_library(self):
        if not self.librarysection:
            raise RuntimeError("First view assets or sets.")

        if self.librarysection == "assets":
            self.import_selected_assets()

        if self.librarysection == "sets":
            self.import_selected_set()

    def import_selected_assets(self):
        selectedassets = self.list_library.selectedItems()
        if selectedassets:
            for each in selectedassets:
                each = each.text()
                publishname = each + "_published.ma"
                publishpath = self.PROJECT.assetpath + "/" + each + "/" + publishname
                mc.file(publishpath, r=True, ns=each)

    def import_selected_set(self):
        selectedset = self.list_library.selectedItems()
        if selectedset and not len(selectedset) > 1:
            setdata = self.PROJECT.data["setdata"][selectedset[0].text()]
            for each in setdata:
                publishname = each + "_published.ma"
                publishpath = self.PROJECT.assetpath + "/" + each + "/" + publishname
                mc.file(publishpath, r=True, ns=each)

            referencelist = mc.ls(type="reference")

            for each in referencelist:
                assetname = each[:-2]
                mc.select("{0}:*".format(assetname))
                items = mc.ls(sl=True, type="transform")
                for item in items:
                    transformmatrix = setdata[assetname][item]
                    mc.xform(item, matrix=transformmatrix)

    def create_set(self):
        mc.file(new=True)
        self.update_workingon_label("New set")

    def save_set(self):
        setname, ok = QtGui.QInputDialog.getText(self, "Saving set", "Set name: ")
        if ok:
            if "setdata" in self.PROJECT.data:
                if setname in self.PROJECT.data["setdata"]:
                    raise RuntimeError("Name for set is not unique!")
        else:
            raise RuntimeError("Set isn't saved!")

        referencelist = mc.ls(type="reference")

        if not referencelist:
            raise RuntimeError("There are no references in this scene.")

        positiondata = {}

        for each in referencelist:
            assetname = each[:-2]
            mc.select("{0}:*".format(assetname))
            items = mc.ls(sl=True, type="transform")
            for item in items:
                transformmatrix = mc.xform(item, q=True, matrix=True)
                positiondata.update({item: transformmatrix})

        setdata = {setname: {assetname: positiondata}}
        self.PROJECT.add_setdata(setdata)

    def open_asset_dir(self):
        path = ""

        selected = self.list_content.currentItem()
        if not selected:
            raise RuntimeError("No item selected!")

        else:
            selected = selected.text()

        if self.currentlistsection == "assets":
            path = os.path.join(self.PROJECT.assetpath, selected)

        if self.currentlistsection == "shots":
            path = os.ath.join(self.PROJECT.shotpath, selected)

        if path:
            print "browsepath: ", path
            subprocess.Popen(r'explorer "{0}"'.format(path))

    def delete_set(self):
        selectedsets = self.list_library.selectedItems()
        if not selectedsets or len(selectedsets) > 1:
            raise RuntimeError("Please only select 1 set.")

        selectedset = selectedsets[0].text()

        if not selectedset:
            raise RuntimeError("You have no set selected to delete.")

        self.PROJECT.delete_setdata(selectedset)
        self.update_list_library_sets()

    def re_load_shaders(self):
        # TODO: reload...not just load.
        referencelist = mc.ls(type="reference")

        for each in referencelist:
            assetname = each[:-2]
            shaderrelations = self.PROJECT.data["assets"][assetname]["shaderrelations"]
            n = 0
            for r in shaderrelations:
                n += 1
                shaderpath = self.PROJECT.shaderpath.replace("\\", "/") + "/" + assetname + "_" + r + ".ma"
                shadername = "{0}_shaders{1}:{2}".format(assetname, n, r)
                mc.file(shaderpath, r=True, ns="{0}_shaders{1}".format(assetname, n))
                rSG = mc.sets(renderable=True, noSurfaceShader=True, empty=True)
                mc.connectAttr("{0}.outColor".format(shadername), "{0}.surfaceShader".format(rSG))
                objects = shaderrelations[r]
                if objects:
                    for o in objects:
                        mc.select(o)
                        mc.sets(e=True, forceElement=rSG)

    # #############################
    def get_total_versions(self, contenttype, name, devtype):
        totalversions = self.PROJECT.data[contenttype][name][devtype]
        return totalversions

    def get_content_path(self, contenttype, name, devtype, version):
        filename = name + self.version_text(version) + ".ma"
        filepath = "{0}/{1}/{2}/{3}/{4}".format(self.PROJECT.path,
                                                contenttype,
                                                name,
                                                devtype,
                                                filename)
        return filepath

    def open_selected(self):
        selected = self.list_content.currentItem().text()
        if not selected:
            raise RuntimeError("No item selected!")

        self.update_workingon_label(selected)

        if self.currentlistsection == "assets":
            if self.devtype == "dev":
                versions = self.activeasset.devversions

                if versions > 0:
                    desiredversion = self.combobox_versions.currentIndex()
                    print "desired version: ", desiredversion
                    if desiredversion == 0:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, versions)
                    else:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, desiredversion)

                    self.open_maya_file(path)
                    print "Opened file: {0}".format(path)

                else:
                    mc.file(f=True, new=True)

            if self.devtype == "lookdev":
                versions = self.activeasset.lookdevversions

                if versions > 0:
                    desiredversion = self.combobox_versions.currentIndex()
                    print "desired version: ", desiredversion
                    if desiredversion == 0:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, versions)
                    else:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, desiredversion)

                    self.open_maya_file(path)
                    print "Opened file: {0}".format(path)

                else:
                    mc.file(f=True, new=True)
                    path = self.get_content_path(self.currentlistsection, selected, self.devtype, versions)
                    removelength = len("/lookdev/{0}_v000.ma".format(self.activeasset.name)) + 2
                    path = path[:-removelength] + "/{0}_published.ma".format(self.activeasset.name)
                    mc.file("{0}".format(path), r=True, ns="{0}".format(self.activeasset.name))

        if self.currentlistsection == "shots":
            if self.devtype == "dev":
                versions = self.activeasset.devversions

                if versions > 0:
                    desiredversion = self.combobox_versions.currentIndex()
                    print "desired version: ", desiredversion
                    if desiredversion == 0:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, versions)
                    else:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, desiredversion)

                    self.open_maya_file(path)
                    print "Opened file: {0}".format(path)

                else:
                    mc.file(f=True, new=True)

            if self.devtype == "lookdev":
                versions = self.activeasset.lookdevversions

                if versions > 0:
                    desiredversion = self.combobox_versions.currentIndex()
                    print "desired version: ", desiredversion
                    if desiredversion == 0:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, versions)
                    else:
                        path = self.get_content_path(self.currentlistsection, selected, self.devtype, desiredversion)

                    self.open_maya_file(path)
                    print "Opened file: {0}".format(path)

                else:
                    mc.file(f=True, new=True)

                    publishname = self.activeasset.name + "_cached.abc"
                    publishpath = self.PROJECT.path.replace("\\", "/") + "/" + "shots" + "/" + self.activeasset.name + "/" + publishname

                    mel.eval('AbcImport -mode "import" "{0}";'.format(publishpath))
                    # list references
                    # import shaders based on references
                    # assign shaders

    def update_workingon_label(self, text):
        self.label_workingon.setText(str(text))

    def save_active_asset(self):
        """
        PATH: self.projectpath / asset or shot / name / devtype / file_v001.ma
        """
        if not self.devtype:
            raise RuntimeError("No list selected yet!")

        if self.devtype == "dev":
            self.activeasset.devversions += 1
            version = self.activeasset.devversions
        if self.devtype == "lookdev":
            self.activeasset.lookdevversions += 1
            version = self.activeasset.lookdevversions

        path = self.get_content_path(self.currentlistsection,
                                     self.activeasset.name,
                                     self.devtype,
                                     version)
        # print "contentpath: " + path
        self.save_maya_file(path)

        # print "newversion: ", version
        self.PROJECT.data[self.currentlistsection][self.activeasset.name][self.devtype] = version
        # print "newversion data: ", self.PROJECT.data[self.currentlistsection][self.activeasset.name][self.devtype]
        # print "saving . . .   *beep boop*"
        self.PROJECT.update()

    def publish_active_asset(self):
        if self.currentlistsection == "assets":
            if self.devtype == "dev":
                self.publish_asset_dev()
            if self.devtype == "lookdev":
                self.publish_asset_lookdev()
        if self.currentlistsection == "shots":
            if self.devtype == "dev":
                self.publish_shot_dev()
            if self.devtype == "lookdev":
                self.publish_shot_lookdev()

    def publish_asset_dev(self):
        publishname = self.activeasset.name + "_published.ma"
        publishpath = self.PROJECT.assetpath + "/" + self.activeasset.name + "/" + publishname
        # TODO set published to TRUE?
        self.PROJECT.data[self.currentlistsection][self.activeasset.name]["published"] = True
        self.PROJECT.update()
        self.save_maya_file(publishpath)
        self.view_assets()

    def publish_asset_lookdev(self):
        shaderrelations = self.list_relations()
        allshaderfiles = os.listdir(self.PROJECT.shaderpath)

        for file in allshaderfiles:
            if self.activeasset.name in file:
                filepath = self.PROJECT.shaderpath.replace("\\", "/") + "/" + file
                icFU.delete_file(filepath)

        self.save_shaders_to_path(self.PROJECT.shaderpath)


        self.PROJECT.data[self.currentlistsection][self.activeasset.name]["shaderrelations"] = shaderrelations
        self.PROJECT.update()
        mc.file(save=True, type="mayaAscii")
        self.view_assets_lookdev()

    def publish_shot_dev(self):
        publishname = self.activeasset.name + "_cached.abc"
        publishpath = self.PROJECT.path.replace("\\", "/") + "/" + "shots" + "/" + self.activeasset.name + "/" + publishname
        print "publishpath: ", publishpath
        command = "-frameRange {0} {1} -file '{2}'".format(0, 10, publishpath)
        mc.AbcExport(j=command)
        self.PROJECT.data[self.currentlistsection][self.activeasset.name]["published"] = True
        self.view_shots()

    def publish_shot_lookdev(self):
        print "There is nothing to publish buddy! You should render this!"

    def delete_item(self):
        selected = self.list_content.currentItem().text()
        if not selected:
            raise RuntimeError("No item selected!")

        if self.confirmation_dialog("Weet je zeker dat je dit item wil verwijderen?",
                                    title="Delete confirmation"):
            if self.currentlistsection == "assets":
                self.PROJECT.delete_asset(selected)

            if self.currentlistsection == "shots":
                self.PROJECT.delete_asset(selected)

            if self.currentlistsection == "other":
                self.PROJECT.delete_asset(selected)
        self.update_list_content(self.currentlistsection)

    def version_text(self, number):
        return "_ver" + self.make_three_digit_string(number)

    def has_version(self, string):
        print "string to check for version: "
        print string
        return string[-10:-7] == "_ver"

    def get_version_as_int(self, string):
        return int(string[-6:-3])

    def make_three_digit_string(self, number):
        numberstring = str(number)
        print "numberstring :" + numberstring
        if len(numberstring) > 3:
            raise RuntimeError("number too big!")

        while len(numberstring) < 3:
            numberstring = "0" + numberstring  # ZERO

        return numberstring

    def make_version_string(self, numberstring):
        return "_v{0}".format(numberstring)

    def get_published_version(self):
        pass

    def published_check(self):
        pass

    def updated_selection(self):
        # TODO: Traverse the structure properly
        """
        The selection in the contents list changed. Get the proper meta-information from the hierarchy.

        e.g.: data = {"assets":{"name":[data]}}
        :return:
        """
        self.combobox_versions.clear()
        self.textfield_information.clear()
        if self.list_content.selectedItems():
            if self.currentlistsection == "assets":
                selecteditem = self.list_content.currentItem().text()
                itemdata = self.PROJECT.data[self.currentlistsection][selecteditem]
                print "data: ", itemdata

                self.activeasset = EXOframe.Asset(self.PROJECT, selecteditem, **itemdata)

                self.textfield_information.setPlainText("{0}".format(self.activeasset.__repr__()))

                if self.devtype == "dev":
                    self.update_version_list(self.activeasset.devversions)
                elif self.devtype == "lookdev":
                    self.update_version_list(self.activeasset.lookdevversions)

            if self.currentlistsection == "shots":
                selecteditem = self.list_content.currentItem().text()
                itemdata = self.PROJECT.data[self.currentlistsection][selecteditem]
                print "data: ", itemdata

                self.activeasset = EXOframe.Shot(self.PROJECT, selecteditem, **itemdata)

                self.textfield_information.setPlainText("{0}".format(self.activeasset.__repr__()))

                if self.devtype == "dev":
                    self.update_version_list(self.activeasset.devversions)
                elif self.devtype == "lookdev":
                    self.update_version_list(self.activeasset.lookdevversions)

            if self.currentlistsection == "other":
                selecteditem = self.list_content.currentItem().text()
                itemdata = self.PROJECT.data[self.currentlistsection][selecteditem]
                print "data: ", itemdata

                self.activeasset = EXOframe.Other(self.PROJECT, selecteditem, **itemdata)

                self.textfield_information.setPlainText("{0}".format(self.activeasset.__repr__()))

                self.update_version_list(self.activeasset.devversions)

    def open_maya_file(self, path):
        mc.file(path, open=True)

    def save_maya_file(self, path):
        print "save_maya_file:", path
        mc.file(rename=path)
        mc.file(save=True, type="mayaAscii")

    ###############################################################

    ####                                              SHADING UTILS

    ###############################################################
    def list_shaders(self):
        shaderlist = []
        for i in self.list_shading_engines():
            if not i == "initialParticleSE" and not i == "initialShadingGroup":
                shaderlist.append(mc.listConnections("{0}.surfaceShader".format(i))[0])
        #print "shaderlist: ", shaderlist
        return shaderlist

    def list_shading_engines(self):
        shadingenginelist = []
        totalshadinglist = mc.ls(type="shadingEngine")
        for s in totalshadinglist:
            if not s == "initialParticleSE" and not s == "initialShadingGroup":
                shadingenginelist.append(s)
        #print "shadingengines: ", shadingenginelist

        return shadingenginelist

    def list_relations(self):
        if not self.list_shaders():
            raise RuntimeError("No shaders in scene!")

        relationdata = {}
        shaderlist = self.list_shaders()
        shadingenginelist = self.list_shading_engines()

        for s, se in zip(shaderlist, shadingenginelist):
            print "shader: ", s
            print "shadingengine: ", se
            objects = mc.listRelatives(se, parent=True, fullPath=True)
            print "objects: ", objects
            relationdata.update({s: objects})

        return relationdata

    def save_shaders_to_path(self, path):
        for s in self.list_shaders():
            exportname = "{0}_{1}".format(self.activeasset.name, s)
            mc.select(s)
            mc.file("{0}/{1}.ma".format(path, exportname),
                    force=True,
                    options="v=0",
                    type="mayaAscii",
                    es=True)


def show():
    """
    Checks if window is unique and if not, deletes and (re-)opens.
    """
    if mc.window(WINDOW_NAME, exists = True, q = True):
        mc.deleteUI(WINDOW_NAME)

    EXOpipeline()