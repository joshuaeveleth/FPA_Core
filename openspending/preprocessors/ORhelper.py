# -*- coding: utf-8 -*-

from google.refine import refine
import tempfile
import os
import requests
import codecs
import time
import csv
import urllib
from openspending.preprocessors import processing_funcs
from flask import current_app
#from settings import OPENREFINE_SERVER

from os.path import splitext

#from csvkit import convert as xlsconvert

import StringIO

import openpyxl
import xlrd
import csv



def convert_to_utf(item):
    try:
        return str(item)
    except:
        try:
            return item.decode('utf-8', 'ignore')
        except:
            return item

def convert_files_to_csv(rawfilepath):
    """
    static raw files and convert them to csv strings
    """

    # JSON, xlsx, xls, csv

    extension = splitext(rawfilepath)[1]
    print rawfilepath

    if extension in [".xls"]:
        wb = xlrd.open_workbook(rawfilepath)
        sh = wb.sheet_by_index(0)

        your_csv_file = StringIO.StringIO()
        #wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

        for rownum in xrange(sh.nrows):
            temparray = []
            for colnum in xrange(sh.ncols):
                item = convert_to_utf(sh.cell_value(rowx=rownum, colx=colnum))
                temparray.append(item)
            your_csv_file.write(",".join(temparray) + '\n')

        your_csv_file.seek(0)
        return your_csv_file.getvalue()
    elif extension in [".xlsx"]:
        wb = openpyxl.load_workbook(rawfilepath, use_iterators=True)
        ws = wb.worksheets[0]


        your_csv_file = StringIO.StringIO()
        #wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

        for row in ws.iter_rows(row_offset=0):
            temparray = []
            for c in row:
                item = convert_to_utf(c.value)
                temparray.append(item)
            your_csv_file.write(",".join(temparray) + '\n')
            #wr.writerow(temparray)

        your_csv_file.seek(0)
        print "returing the value here, we can fix this"
        return your_csv_file.getvalue()

    elif extension in ['.csv']:
        with open(rawfilepath, 'rb') as fl:
            return fl.read()
    else:
        print "ERROR Could not read"
        return None



class RefineProj:


    def __init__(self, source=None):
        OPENREFINE_SERVER = current_app.config.get("OPENREFINE_SERVER")
        self.refine_server = refine.Refine(server=OPENREFINE_SERVER)
        #the source object will have the project_id of OR
        #if project_id does not exist then createOR

        #check that source exists and is good
        #bad URLS and bad files are not possible

        
        self.source = source

        if not source.ORid:
            self.refineproj = self.createOR(source)
        else:
            self.refineproj = refine.RefineProject(server=OPENREFINE_SERVER, project_id=str(int(self.source.ORid)))



    def getProjectID(self):
        return self.source.ORid




    #depending on how long this takes, it could be a celery call
    def createOR(self, source):

        #download source data and save to temp file
        #add checks for a valid URL or file path

        if source.url:
            try:
                resp = requests.get(source.url)
                responsetext = resp.text
            except Exception, e:
                #let's try another method
                fp = urllib.urlopen(source.url)
                responsetext = fp.read()
        elif source.rawfile:
            responsetext = convert_files_to_csv(source.rawfile.get_path())
            # fp = source.rawfile.get_path()
            # s = fp.read()
            try:
                responsetext = str(responsetext)
            except:
                try:
                    responsetext = str(responsetext.decode('utf-8', 'ignore'))
                except:
                    pass
        else:
            return None

        if not responsetext:
            return None



        #preprocessing functions
        if (len(source.dataset.prefuncs.keys()) > 0):
            #apply preprocessors
            for func in source.dataset.prefuncs.keys():
                tempmethod = getattr(processing_funcs, func, None)
                if tempmethod:
                    responsetext = tempmethod(responsetext)


        filepath = os.path.join(tempfile.gettempdir(), str(int(time.time())) + ".csv").replace("\\","/")
        try:
            with codecs.open(filepath, 'wb', 'utf-8') as f:
                f.write(responsetext)
        except Exception, e:
            #codec issue trying default
            with codecs.open(filepath, 'wb') as f:
                f.write(responsetext)         

        #store raw file here with barn


        refineproj = self.refine_server.new_project(project_file=filepath,project_name=self.source.dataset.name, separator=',',
                #store_blank_rows=True,
                #store_blank_cells_as_nulls=True
                )

        os.remove(filepath)


        #and save the edited sourcew
        if refineproj.project_id:

            return refineproj
        else:
            return None

    def list_ops_to_json(self, rawops):
        tempjsonobj = {}
        counter = 0
        for rawop in rawops:
            tempjsonobj[str(counter)] = rawop
            counter +=1
        print tempjsonobj
        return tempjsonobj


    def list_ops_to_list(self,jsonops):
        temparray = []
        for jsonindex in jsonops.keys():
            temparray.append(jsonops[jsonindex])
        return temparray





    def get_operations(self):
        return self.list_ops_to_json(self.refineproj.get_operations())


    def get_file(self):
        #apply the operations tot he project and get result
        return self.refineproj.export(export_format='csv')






    def applyOR(self, refineproj):
        if self.openrefine_transformation and self.openrefine_transformation != "":
            import json
            entryobject = json.loads(self.openrefine_transformation)
            operations = []
            print entryobject
            for entry in entryobject['entries']:
                if 'operation' in entry.keys():
                    operations.append(entry['operation'])
            data = {'operations': json.dumps(operations)}
            r = refineproj.do_json("apply-operations", data=data)
            return True
        else:
            return None

    def deleteOR(refineproj=None):
        OPENREFINE_SERVER = current_app.config.get("OPENREFINE_SERVER")
        if not refineproj:
            refiner = refine.RefineProject(server=OPENREFINE_SERVER, project_id=int(self.openrefine_projectnumber))
        else:
            refiner = refineproj
        refiner.delete()
        self.openrefine_projectnumber = ""
        self.save()
        return True

    def getUpdatedCSV(asText=True):
        #we may just need to do an explore on the refineproj?
        refineproj = self.createOR()
        self.applyOR(refineproj)
        f = refineproj.export(export_format='csv')
        self.deleteOR(refineproj)
        return f.read()

import json

def cleanOperations(JSONObj):
    operations = []

    for entry in JSONObj.values():
        print entry
        if 'operation' in entry.keys():
            operations.append(entry['operation'])
    return json.dumps(operations)



def testORLoad(sourceurl=None, fileobj=None):
    #download source data and save to temp file
    #add checks for a valid URL or file path

    if not sourceurl and not fileobj:
        print "You're missing the sourceurl or the fileobj"

    
    if sourceurl:
        res = requests.get(sourceurl)
        datatext = res.text
    elif fileobj:
        with codecs.open(fileobj, 'rb') as datafile:
            datatext = datafile.read()
    else:
        print "something went wrong with finding sourceurl or fileobj"


    filepath = os.path.join(tempfile.gettempdir(), str(int(time.time())) + ".csv").replace("\\","/")


    
    with codecs.open(filepath, 'wb', 'utf-8') as f:
        f.write(datatext)

    OPENREFINE_SERVER = current_app.config.get("OPENREFINE_SERVER")

    #store raw file here with barn

    try:
        refine_server = refine.Refine(server=OPENREFINE_SERVER)
        refineproj = refine_server.new_project(project_file=filepath,project_name="testerhere", separator=',',
                #store_blank_rows=True,
                #store_blank_cells_as_nulls=True
                )
    except Exception, e:
        print "hit error on project creation"
        print e
        os.remove(filepath)
        return False

    os.remove(filepath)

    try:
        numrows = refineproj.get_rows()
        if numrows == 0:
            print "failed to get data, there was an error, or something else"
            refineproj.delete()
            return False
        else:
            print "Data load success"
            refineproj.delete()
            return True
    except:
        print "something went wrong with calling the proj"
        print e
        refineproj.delete()
