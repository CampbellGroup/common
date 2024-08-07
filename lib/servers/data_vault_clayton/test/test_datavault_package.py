import mock
import numpy as np
import os
import pytest
import tempfile
import unittest

from labrad import types

from twisted.internet import task

from datavault import Session, Dataset, SessionStore


def _unique_dir():
    return tempfile.mkdtemp(prefix='dvtest_')


def _unique_dir_name():
    newdir = _unique_dir()
    # Remove the newly created directory as this wil be recreated by the
    # Session.
    _empty_and_remove_dir(newdir)
    return newdir


def _empty_and_remove_dir(*names):
    for name in names:
        if not os.path.exists(name):
            continue
        for listedname in os.listdir(name):
            path = os.path.join(name, listedname)
            if os.path.isdir(path):
                _empty_and_remove_dir(name + '/' + listedname)
            else:
                os.remove(path)
        os.rmdir(name)


class TestSessionStore(unittest.TestCase):
    def setUp(self):
        self.datadir = _unique_dir_name()
        self.hub = mock.MagicMock()

    def tearDown(self):
        _empty_and_remove_dir(self.datadir)

    def test_get_new_session(self):
        store = SessionStore(self.datadir, self.hub)
        self.assertFalse(store.exists('foo'))
        store.get('foo')
        self.assertTrue(store.exists('foo'))

    def test_get_existing_session(self):
        store = SessionStore(self.datadir, self.hub)
        # Create a new session.
        new_session = store.get('foo')
        # Get the same existing session again.
        got_session = store.get('foo')
        self.assertEqual(new_session, got_session)

    def test_get_all_sessions(self):
        store = SessionStore(self.datadir, self.hub)
        # Create a new session.
        foo_session = store.get('foo')
        bar_session = store.get('bar')
        self.assertEqual([foo_session, bar_session], store.get_all())


class _DatavaultTestCase(unittest.TestCase):
    _TITLE = 'Foo'
    _INDEPENDENTS = [('Current', 'mA'), ('Freq', 'Ghz')]
    _DEPENDENTS = [('Dep 1', 'Voltage', 'V')]

    def assertArrayEqual(self, expected, actual):
        self.assertTrue(np.array_equal(expected, actual),
                        msg='Arrays not equal\nfirst:\n{}\nsecond:\n{}'
                        .format(expected, actual))

    def assertListOfVariablesEqual(self, expected, actual):
        self.assertEqual(len(expected), len(actual))
        msg_template = (
            'Mismatch in varianles list at position {}:'
            '\nexpected:\n{}\nactual:\n{}')

        items = enumerate(zip(expected, actual))
        for i, (expected_var, actual_var) in items:
            msg = msg_template.format(i, expected_var, actual_var)
            self.assertEqual(expected_var.label, actual_var.label, msg=msg)
            self.assertEqual(
                expected_var.datatype, actual_var.datatype, msg=msg)
            self.assertEqual(expected_var.unit, actual_var.unit, msg=msg)
            self.assertEqual(expected_var.shape, actual_var.shape, msg=msg)
            if hasattr(expected_var, 'legend'):
                self.assertTrue(hasattr(actual_var, 'legend'), msg=msg)
                self.assertEqual(
                    expected_var.legend, actual_var.legend, msg=msg)

    def assertDatasetsEqual(self, expected, actual):
        expected_entries, expected_num = expected.get_data(None, 0)
        actual_entries, actual_num = actual.get_data(None, 0)
        self.assertEqual(expected_num, actual_num)
        self.assertArrayEqual(expected_entries, actual_entries)
        expected_independents = expected.get_independents()
        actual_independents = actual.get_independents()
        self.assertListOfVariablesEqual(
            expected_independents, actual_independents)
        expected_dependents = expected.get_dependents()
        actual_dependents = actual.get_dependents()
        self.assertListOfVariablesEqual(
            expected_dependents, actual_dependents)


class SessionTest(_DatavaultTestCase):

    def setUp(self):
        self.datadir = _unique_dir_name()
        self.hub = mock.MagicMock()
        self.store = mock.MagicMock()

    def tearDown(self):
        _empty_and_remove_dir(self.datadir)

    def _get_session(self, path=['foo']):
        return Session(self.datadir, path, self.hub, self.store)

    def test_init_no_parent(self):
        s = self._get_session()
        dirs, datasets = s.list_contents([])
        self.assertEqual(len(dirs), 0)
        self.assertEqual(len(datasets), 0)

    def test_add_new_dataset(self):
        session = self._get_session()
        dataset = session.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)
        datasets = session.list_datasets()
        self.assertEqual(len(datasets), 1)
        self.assertEqual(['00001 - Foo'], datasets)

        # Check the dataset is returned from open.
        opened_dataset = session.open_dataset('00001 - Foo')
        self.assertDatasetsEqual(dataset, opened_dataset)

    def test_add_child_session(self):
        parent_session = self._get_session(path=['parent'])
        # Add a listener
        parent_session.listeners.add('foo_listener')
        # Set the session store mock to return the parent
        self.store.get.return_value = parent_session
        child_session = self._get_session(path=['parent', 'child'])
        self.hub.onNewDir.assert_called_with('child', set(['foo_listener']))

    def test_save_reload_dataset(self):
        s1 = self._get_session()
        d1 = s1.new_dataset(self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)
        d1.add_data(np.array([0]))
        d1.add_data(np.array([1]))
        s1.save()
        self.assertEqual(['00001 - Foo'], s1.list_datasets())

        s2 = self._get_session()
        s2.load()
        datasets = s2.list_datasets()
        self.assertEqual(len(datasets), 1)
        self.assertEqual(['00001 - Foo'], datasets)
        d2 = s2.open_dataset(datasets[0])
        self.assertDatasetsEqual(d1, d2)

    def test_add_new_tags(self):
        session1 = self._get_session()
        dataset1 = session1.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)
        session2 = self._get_session()
        dataset2 = session2.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)

        session = self._get_session()
        session.update_tags(['foo'], [session1, session2], [dataset1, dataset2])

        expected_session_tags = [(session1, ['foo']), (session2, ['foo'])]
        expected_dataset_tags = [(dataset1, ['foo']), (dataset2, ['foo'])]
        self.hub.onTagsUpdated.assert_called_with(
            (expected_session_tags, expected_dataset_tags), set([]))

    def test_get_tags(self):
        # Create some sessions and add some datasets.
        session1 = self._get_session()
        dataset1 = session1.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)
        session2 = self._get_session()
        dataset2 = session2.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)

        # Create another session to store tags for the other sessions and
        # datasets in.
        session = self._get_session()
        session.update_tags(['foo'], [session1, session2], [dataset1, dataset2])
        session.update_tags(['bar'], [session1], [])

        # Check the session has the right tags for the other sessions and
        # datasets.
        tags = session.get_tags([session1, session2], [dataset1, dataset2])
        self.assertEqual(2, len(tags))

        session_tags = tags[0]
        expected_session_tags = [
            (session1, ['bar', 'foo']), (session2, ['foo'])]
        self.assertEqual(expected_session_tags, session_tags)

        dataset_tags = tags[1]
        expected_dataset_tags = [(dataset1, ['foo']), (dataset2, ['foo'])]
        self.assertEqual(expected_dataset_tags, dataset_tags)

        # Check the sessions themselves don't have any of the tags.
        tags1 = session1.get_tags([session1], [])
        self.assertEqual(([(session1, [])], []), tags1)
        tags2 = session2.get_tags([session2], [])
        self.assertEqual(([(session2, [])], []), tags2)

    def test_remove_tags(self):
        # Create a session and add a datasets.
        session = self._get_session()
        dataset = session.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)

        # Use the session to store tags for itself.
        session.update_tags(['session_tag'], [session], [])
        session.update_tags(['dataset_tag'], [], [dataset])

        # Remove the tags.
        session.update_tags(['-session_tag'], [session], [])
        session.update_tags(['-dataset_tag'], [], [dataset])

        session_tags, dataset_tags = session.get_tags([session], [dataset])
        self.assertEqual([(session, [])], session_tags)
        self.assertEqual([(dataset, [])], dataset_tags)

    def test_toggle_tags(self):
        # Create a session and add a datasets.
        session = self._get_session()
        dataset = session.new_dataset(
            self._TITLE, self._INDEPENDENTS, self._DEPENDENTS)

        # Use the session to store tag for itself.
        session.update_tags(['tag'], [session], [dataset])

        # Toggle the tag off.
        session.update_tags(['^tag'], [session], [dataset])

        session_tags, dataset_tags = session.get_tags([session], [dataset])
        self.assertEqual([(session, [])], session_tags)
        self.assertEqual([(dataset, [])], dataset_tags)

        # Toggle the tag back on.
        session.update_tags(['^tag'], [session], [dataset])

        session_tags, dataset_tags = session.get_tags([session], [dataset])
        self.assertEqual([(session, ['tag'])], session_tags)
        self.assertEqual([(dataset, ['tag'])], dataset_tags)


class DatasetTest(_DatavaultTestCase):
    _EXT_INDEPENDENTS = [('t', [1], 'v', 'ns'), ('x', [2, 2], 'c', 'V')]
    _EXT_DEPENDENTS = [('cnt', 'foo', [3, 2], 'i', '')]

    def setUp(self):
        self.hub = mock.MagicMock()
        self.session = mock.MagicMock()
        self.session.hub = self.hub
        self.session.dir = _unique_dir()

    def tearDown(self):
        _empty_and_remove_dir(self.session.dir)

    def _get_records_simple(self, rows, dtype):
        data_array = np.array(rows)
        data_array = np.atleast_2d(data_array)
        data_record = np.core.records.fromarrays(data_array.T, dtype=dtype)
        return data_record

    def _get_records_extended(self, rows, dtype):
        data_record = np.recarray((len(rows),), dtype=dtype)
        for i, row in enumerate(rows):
            data_record[i] = row
        return data_record

    def test_init_create_simple(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._INDEPENDENTS,
            dependents=self._DEPENDENTS)

        self.assertEqual('2.0.0', dataset.version())

        self.assertEqual('*(v[mA],v[Ghz],v[V])', dataset.get_row_type())
        self.assertEqual('(*v[mA],*v[Ghz],*v[V])', dataset.get_transpose_type())

        # Check dependents added correctly
        dependents = dataset.get_dependents()
        self.assertEqual(len(self._DEPENDENTS), len(dependents))
        self.assertEqual(self._DEPENDENTS[0][0], dependents[0].label)
        self.assertEqual(self._DEPENDENTS[0][1], dependents[0].legend)
        self.assertEqual(self._DEPENDENTS[0][2], dependents[0].unit)

        # Check independents added correctly
        independents = dataset.get_independents()
        self.assertEqual(len(self._INDEPENDENTS), len(independents))
        self.assertEqual(self._INDEPENDENTS[0][0], independents[0].label)
        self.assertEqual(self._INDEPENDENTS[0][1], independents[0].unit)
        self.assertEqual(self._INDEPENDENTS[1][0], independents[1].label)
        self.assertEqual(self._INDEPENDENTS[1][1], independents[1].unit)

    def test_init_create_extended(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._EXT_INDEPENDENTS,
            dependents=self._EXT_DEPENDENTS,
            extended=True)

        self.assertEqual('3.0.0', dataset.version())

        self.assertEqual('*(v[ns],*2c[V]{2,2},*2i{3,2})', dataset.get_row_type())
        self.assertEqual('(*v[ns],*3c[V]{N,2,2},*3i{N,3,2})', dataset.get_transpose_type())

        # Check dependents added correctly
        dependents = dataset.get_dependents()
        self.assertEqual(len(self._DEPENDENTS), len(dependents))
        self.assertEqual(self._EXT_DEPENDENTS[0][0], dependents[0].label)
        self.assertEqual(self._EXT_DEPENDENTS[0][1], dependents[0].legend)
        self.assertArrayEqual(self._EXT_DEPENDENTS[0][2], dependents[0].shape)
        self.assertEqual(self._EXT_DEPENDENTS[0][3], dependents[0].datatype)
        self.assertEqual(self._EXT_DEPENDENTS[0][4], dependents[0].unit)

        # Check independents added correctly
        independents = dataset.get_independents()
        self.assertEqual(len(self._INDEPENDENTS), len(independents))
        self.assertEqual(self._EXT_INDEPENDENTS[0][0], independents[0].label)
        self.assertArrayEqual(self._EXT_INDEPENDENTS[0][1], independents[0].shape)
        self.assertEqual(self._EXT_INDEPENDENTS[0][2], independents[0].datatype)
        self.assertEqual(self._EXT_INDEPENDENTS[0][3], independents[0].unit)

        self.assertEqual(self._EXT_INDEPENDENTS[1][0], independents[1].label)
        self.assertArrayEqual(self._EXT_INDEPENDENTS[1][1], independents[1].shape)
        self.assertEqual(self._EXT_INDEPENDENTS[1][2], independents[1].datatype)
        self.assertEqual(self._EXT_INDEPENDENTS[1][3], independents[1].unit)

    def test_add_data_simple(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._INDEPENDENTS,
            dependents=self._DEPENDENTS)

        dataset.listeners.add('foo listener')

        data = self._get_records_simple(
            [(1, 2, 3), (2, 3, 4)], dataset.data.dtype)

        # Add the data.
        dataset.add_data(data)

        self.hub.onDataAvailable.assert_called_with(None, set(['foo listener']))
        data_in_dataset, count = dataset.get_data(None, 0, simple_only=True)
        self.assertEqual(count, 2)
        self.assertArrayEqual([1, 2, 3], data_in_dataset[0])
        self.assertArrayEqual([2, 3, 4], data_in_dataset[1])

    def test_add_data_extended(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._EXT_INDEPENDENTS,
            dependents=self._EXT_DEPENDENTS,
            extended=True)

        dataset.listeners.add('foo listener')
        row_1 = (1, [[0, 1], [1, 0]], [[0, 1], [2, 3], [4, 5]])
        row_2 = (2, [[1, 0], [1, 0]], [[6, 7], [8, 3], [2, 1]])
        data = self._get_records_extended([row_1, row_2], dataset.data.dtype)

        # Add the data.
        dataset.add_data(data)

        self.hub.onDataAvailable.assert_called_with(None, set(['foo listener']))

        data_in_dataset, count = dataset.get_data(None, 0, simple_only=False)
        self.assertEqual(count, 2)
        self.assertArrayEqual(row_1[0], data_in_dataset[0][0])
        self.assertArrayEqual(row_1[1], data_in_dataset[0][1])
        self.assertArrayEqual(row_1[2], data_in_dataset[0][2])
        self.assertArrayEqual(row_2[0], data_in_dataset[1][0])
        self.assertArrayEqual(row_2[1], data_in_dataset[1][1])
        self.assertArrayEqual(row_2[2], data_in_dataset[1][2])

    def test_save_reload_data_extended(self):
        # Set up the dataset
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._EXT_INDEPENDENTS,
            dependents=self._EXT_DEPENDENTS,
            extended=True)

        dataset.listeners.add('foo listener')
        row_1 = (1, [[0, 1], [1, 0]], [[0, 1], [2, 3], [4, 5]])
        row_2 = (2, [[1, 0], [1, 0]], [[6, 7], [8, 3], [2, 1]])
        data = self._get_records_extended([row_1, row_2], dataset.data.dtype)
        # Add the data.
        dataset.add_data(data)

        # Save the dataset
        dataset.save()

        # Create a new dataset that loads the data.
        new_dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            extended=True)

        data_in_dataset, count = new_dataset.get_data(None, 0, simple_only=False)
        self.assertEqual(count, 2)
        self.assertArrayEqual(row_1[0], data_in_dataset[0][0])
        self.assertArrayEqual(row_1[1], data_in_dataset[0][1])
        self.assertArrayEqual(row_1[2], data_in_dataset[0][2])
        self.assertArrayEqual(row_2[0], data_in_dataset[1][0])
        self.assertArrayEqual(row_2[1], data_in_dataset[1][1])
        self.assertArrayEqual(row_2[2], data_in_dataset[1][2])

    def test_add_one_parameter(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._INDEPENDENTS,
            dependents=self._DEPENDENTS)

        dataset.param_listeners.add('listener')
        dataset.add_parameter('param 1', 'data for param')

        self.hub.onNewParameter.assert_called_with(None, set(['listener']))

        self.assertEqual(['param 1'], dataset.get_param_names())
        self.assertEqual('data for param', dataset.get_parameter('param 1'))

    def test_add_two_parameters(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._INDEPENDENTS,
            dependents=self._DEPENDENTS)

        dataset.param_listeners.add('listener')
        dataset.add_parameters([('param 2', 'data 2'), ('param 3', 'data 3')])
        self.hub.onNewParameter.assert_called_with(None, set(['listener']))
        self.assertEqual(['param 2', 'param 3'], dataset.get_param_names())
        self.assertEqual('data 2', dataset.get_parameter('param 2'))
        self.assertEqual('data 3', dataset.get_parameter('param 3'))

    def test_add_comment(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._INDEPENDENTS,
            dependents=self._DEPENDENTS)

        dataset.comment_listeners.add('listener')
        dataset.add_comment('user 1', 'comment 1')

        self.hub.onCommentsAvailable.assert_called_with(None, set(['listener']))

        retreived_comment, count = dataset.get_comments(None, 0)
        self.assertEqual(1, count)
        self.assertEqual('user 1', retreived_comment[0][1])
        self.assertEqual('comment 1', retreived_comment[0][2])

    def test_keep_streaming(self):
        dataset = Dataset(
            self.session,
            "Foo Name",
            title=self._TITLE,
            create=True,
            independents=self._INDEPENDENTS,
            dependents=self._DEPENDENTS)

        data = self._get_records_simple([(1, 2, 3)], dataset.data.dtype)

        dataset.add_data(data)

        listener = 'listener'
        # Start streaming the listener
        dataset.keep_streaming(listener, 0)
        # Check the listener is notified of the data already available
        self.hub.onDataAvailable.assert_called_with(None, [listener])
        self.hub.reset_mock()
        # Keep streaming for more data added
        dataset.keep_streaming(listener, 1)
        # Add more data.
        dataset.add_data(data)
        # Trigger the listener again.
        self.hub.onDataAvailable.assert_called_with(None, set([listener]))


if __name__ == '__main__':
    pytest.main(['-v', '-s', __file__])
