import urllib, urlparse

from openspending.core import db
from openspending.model.dataset import Dataset
from openspending.model.source import Source
from openspending.lib import json
from openspending.preprocessors.ORhelper import cleanOperations

from openspending.importer import ORImporter

from openspending.tests.base import DatabaseTestCase
from openspending.tests.helpers import fixture_path, make_account


def csvimport_fixture_path(name, path):
    return urlparse.urljoin('file:', urllib.pathname2url(fixture_path('or_import/%s/%s' % (name, path))))


def csvimport_fixture_file(name, path):
    try:
        fp = urllib.urlopen(csvimport_fixture_path(name, path))
    except IOError:
        if name == 'default':
            fp = None
        else:
            fp = csvimport_fixture_file('default', path)

    return fp


def csvimport_fixture(name):
    #load the dataset model
    dataset_fp = csvimport_fixture_file("default_dataset", "model.json")
    dataset_model = json.load(dataset_fp)
    dataset = Dataset(dataset_model)
    db.session.add(dataset)

    source_fp = csvimport_fixture_file(name, 'model.json')
    source_mapping_fp = csvimport_fixture_file(name, 'mapping.json')
    source_model = json.load(source_fp)
    user = make_account()
    data_path = csvimport_fixture_path(name, 'data.csv')
    print source_model.keys()
    source = Source(dataset=dataset, creator=user, url=source_model['url'], name=source_model['name'])
    db.session.add(source)
    db.session.commit()

    ORoperations_fp = csvimport_fixture_file(name, 'ORoperations.json')
    if ORoperations_fp:
        #expecting file to open
        refineproj = source.get_or_create_ORProject()
        #ORoperationsJSON = json.load(ORoperations_fp)
        #opsstring = cleanOperations(ORoperationsJSON)
        data = {'operations': ORoperations_fp.read()}
        refineproj.refineproj.do_json("apply-operations", data=data)
        #refineproj.refineproj.apply_operations_json(cleanOperations(ORoperationsJSON), wait=True)

    if source_mapping_fp:
        source_mapping = json.load(source_mapping_fp)
        source.addData(source_mapping)
    source.model.generate()

    return source


def clean_OR(source):
    print "cleaning source"
    refineproj = source.get_or_create_ORProject()
    refineproj.refineproj.delete()




class TestORImporter(DatabaseTestCase):

    def test_successful_import(self):
        source = csvimport_fixture('sci_study')
        importer = ORImporter(source)
        importer.run()
        source = db.session.query(Source).first()
        clean_OR(source)

        assert source is not None, "Dataset should not be None"
        assert source.name == "sci_study"

        entries = list(source.model.entries())
        assert len(entries) == 1

        # TODO: provenance
        entry = entries.pop()
        assert entry is not None, "Entry with name could not be found"
        assert entry['amount'] == 37.12441
        

    # def test_no_dimensions_for_measures(self):
    #     source = csvimport_fixture('simple')
    #     importer = CSVImporter(source)
    #     importer.run()
    #     dataset = db.session.query(Dataset).first()

    #     dimensions = [str(d.name) for d in dataset.model.dimensions]
    #     assert sorted(dimensions) == ['entry_id', 'from', 'time', 'to']

    # def test_successful_import_with_simple_testdata(self):
    #     source = csvimport_fixture('simple')
    #     importer = CSVImporter(source)
    #     importer.run()
    #     assert importer.errors == 0, importer.errors

    #     dataset = db.session.query(Dataset).first()
    #     assert dataset is not None, "Dataset should not be None"

    #     entries = list(dataset.model.entries())
    #     assert len(entries) == 5

    #     entry = entries[0]
    #     assert entry['from']['label'] == 'Test From'
    #     assert entry['to']['label'] == 'Test To'
    #     assert entry['time']['name'] == '2010-01-01'
    #     assert entry['amount'] == 100.00

    # def test_import_errors(self):
    #     source = csvimport_fixture('import_errors')

    #     importer = CSVImporter(source)
    #     importer.run(dry_run=True)
    #     assert importer.errors > 1, "Should have errors"

    #     records = list(importer._run.records)
    #     assert records[0].row == 1, \
    #         "Should detect missing date colum in line 1"

    # def test_empty_csv(self):
    #     source = csvimport_fixture('default')
    #     source.url = 'file:///dev/null'
    #     importer = CSVImporter(source)
    #     importer.run(dry_run=True)

    #     assert importer.errors == 2

    #     records = list(importer._run.records)
    #     assert records[0].row == 0
    #     assert records[1].row == 0
    #     assert "Didn't read any lines of data" in str(records[1].message)

    # def test_malformed_csv(self):
    #     source = csvimport_fixture('malformed')
    #     importer = CSVImporter(source)
    #     importer.run(dry_run=True)
    #     assert importer.errors == 1

    # def test_erroneous_values(self):
    #     source = csvimport_fixture('erroneous_values')
    #     importer = CSVImporter(source)
    #     importer.run(dry_run=True)

    #     # Expected failures:
    #     # * unique key constraint not met (2x)
    #     # * amount cannot be parsed
    #     # * time cannot be parse
    #     assert importer.errors == 4

    #     records = list(importer._run.records)
    #     # The fourth record should be about badly formed date
    #     assert "time" in records[3].attribute, \
    #         "Should find badly formatted date"

    #     # The row number of the badly formed date should be 5
    #     assert records[3].row == 5

    # def test_error_with_empty_additional_date(self):
    #     source = csvimport_fixture('empty_additional_date')
    #     importer = CSVImporter(source)
    #     importer.run()
    #     assert importer.errors == 1

    # def test_quoting(self):
    #     source = csvimport_fixture('quoting')
    #     importer = CSVImporter(source)
    #     importer.run()
    #     assert importer.errors == 0


# class TestCSVImportDatasets(DatabaseTestCase):

#     def count_lines_in_stream(self, f):
#         try:
#             return len(f.read().splitlines())
#         finally:
#             f.seek(0)

#     def _test_import(self, name):
#         source = csvimport_fixture(name)
#         data = open(source.url)
#         lines = self.count_lines_in_stream(data) - 1  # -1 for header row

#         importer = CSVImporter(source)
#         importer.run()

#         assert importer.errors == 0

#         # check correct number of entries
#         dataset = db.session.query(Dataset).first()
#         entries = list(dataset.entries())
#         assert len(entries) == lines

#     def test_all_imports(self):
#         for dir in ('lbhf', 'mexico', 'sample', 'uganda'):
#             yield self._test_import, dir