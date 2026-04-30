
import glob
import os
import pathlib
import sys
from pandas import read_xml
from collections import defaultdict
import csv
import xml.etree.ElementTree as ET



class Datalog(): # agilent 34970A format xml agost/2024

    def __init__(self,directory):

        self.directory = directory

    def get_folders_in_directories_recursively( self, index=0):

        folder_list = list()
        parent_directory = self.directory

        for path, subdirs, _ in os.walk(self.directory):

            if not index:

                for sdirs in subdirs:

                    folder_path = "{}/{}".format(path, sdirs)
                    folder_list.append(folder_path)

            elif path[len(parent_directory):].count('/') + 1 == index:

                for sdirs in subdirs:

                    folder_path = "{}/{}".format(path, sdirs)
                    folder_list.append(folder_path)

        return folder_list


    def list_file (self):

        self.listdirect = Datalog.get_folders_in_directories_recursively(self.directory,0)

        print(self.listdirect[-1])

        self.list_of_files = glob.glob(self.listdirect[-1]+'/*') # * means all if need specific format then *.csv
        self.latest_file = max(self.list_of_files, key=os.path.getmtime)
        print(self.latest_file)


# Passing the path of the
# xml document to enable the
# parsing process
        tree = ET.parse(self.latest_file)

# getting the parent tag of
# the xml document
        root = tree.getroot()

# printing the root (parent) tag
# of the xml document, along with
# its memory location
        print(root.attrib)

        for child in root:

            print(child.tag, child.attrib)


        x = [elem.tag for elem in root.iter('timestamp')]

#print (x)

# printing the attributes of the
# first tag from the parent 
#print(root[-1].attrib)

# printing the text contained within
# first subtag of the 5th tag from
# the parent
        print(root[-1][1].text)

        rha = root[-1][0].text
        tca = root[-1][1].text
        rhb = root[-1][2].text
        tcb = root[-1][3].text

# structuring into Dataframe format

        #variables_df = read_xml(latest_file)
        #variabontime = variables_df.iloc[-1].RHA


        print (rha,tca,rhb,tcb)

