
import hashlib
import functools
import shutil
import logging

import pygeoprocessing

from natcap.testing import data_storage

LOGGER = logging.getLogger('natcap.testing.utils')

def get_hash(uri):
    """Get the MD5 hash for a single file.  The file is read in a
        memory-efficient fashion.

        Args:
            uri (string): a string uri to the file to be tested.

        Returns:
            An md5sum of the input file"""

    block_size = 2**20
    file_handler = open(uri, 'rb')
    md5 = hashlib.md5()
    while True:
        data = file_handler.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def save_workspace(new_workspace):
    """Decorator to save a workspace to a new location.

        If `new_workspace` already exists on disk, it will be recursively
        removed.

        Example usage with a test case::

            import natcap.invest.testing

            @natcap.invest.testing.save_workspace('/path/to/workspace')
            def test_workspaces(self):
                model.execute(self.args)

        Note:
            + Target workspace folder must be saved to ``self.workspace_dir``
                This decorator is only designed to work with test functions
                from subclasses of ``unittest.TestCase`` such as
                ``natcap.invest.testing.GISTest``.

            + If ``new_workspace`` exists, it will be removed.
                So be careful where you save things.

        Args:
            new_workspace (string): a URI to the where the workspace should be
                copied.

        Returns:
            A composed test case function which will execute and then save your
            workspace to the specified location."""

    # item is the function being decorated
    def test_inner_func(item):

        # this decorator indicates that this innermost function is wrapping up
        # the function passed in as item.
        @functools.wraps(item)
        def test_and_remove_workspace(self, *args, **kwargs):
            # This inner function actually executes the test function and then
            # moves the workspace to the folder passed in by the user.
            item(self)

            # remove the contents of the old folder
            try:
                shutil.rmtree(new_workspace)
            except OSError:
                pass

            # copy the workspace to the target folder
            old_workspace = self.workspace_dir
            shutil.copytree(old_workspace, new_workspace)
        return test_and_remove_workspace
    return test_inner_func


def regression(input_archive, workspace_archive):
    """Decorator to unzip input data, run the regression test and compare the
        outputs against the outputs on file.

        Example usage with a test case::

            import natcap.invest.testing

            @natcap.invest.testing.regression('/data/input.tar.gz', /data/output.tar.gz')
            def test_workspaces(self):
                model.execute(self.args)

        Args:
            input_archive (string): The path to a .tar.gz archive with the input data.
            workspace_archive (string): The path to a .tar.gz archive with the workspace to
                assert.

        Returns:
            Composed function with regression testing.
         """

    # item is the function being decorated
    def test_inner_function(item):

        @functools.wraps(item)
        def test_and_assert_workspace(self, *args, **kwargs):
            workspace = pygeoprocessing.geoprocessing.temporary_folder()
            self.args = data_storage.extract_parameters_archive(workspace, input_archive)

            # Actually run the test.  Assumes that self.args is used as the
            # input arguments.
            item(self)

            # Extract the archived workspace to a new temporary folder and
            # compare the two workspaces.
            archived_workspace = pygeoprocessing.geoprocessing.temporary_folder()
            data_storage.extract_archive(archived_workspace, workspace_archive)
            self.assertWorkspace(workspace, archived_workspace)
        return test_and_assert_workspace
    return test_inner_function


def build_regression_archives(file_uri, input_archive_uri, output_archive_uri):
    """Build regression archives for a target model run.

        With a properly formatted JSON configuration file at `file_uri`, all
        input files and parameters are collected and compressed into a single
        gzip.  Then, the target model is executed and the output workspace is
        zipped up into another gzip.  These could then be used for regression
        testing, such as with the ``natcap.invest.testing.regression`` decorator.

        Example configuration file contents (serialized to JSON)::

            {
                    "model": "natcap.invest.pollination.pollination",
                    "arguments": {
                        # the full set of model arguments here
                    }
            }

        Example function usage::

            import natcap.invest.testing

            file_uri = "/path/to/config.json"
            input_archive_uri = "/path/to/archived_inputs.tar.gz"
            output_archive_uri = "/path/to/archived_outputs.tar.gz"
            natcap.invest.testing.build_regression_archives(file_uri,
                input_archive_uri, output_archive_uri)

        Args:
            file_uri (string): a URI to a json file on disk containing the
            above configuration options.

            input_archive_uri (string): the URI to where the gzip archive
            of inputs should be saved once it is created.

            output_archive_uri (string): the URI to where the gzip output
            archive of output should be saved once it is created.

        Returns:
            Nothing.
        """
    file_handler = fileio.JSONHandler(file_uri)

    saved_data = file_handler.get_attributes()

    arguments = saved_data['arguments']
    model_id = saved_data['model']

    model_list = model_id.split('.')
    model = executor.locate_module(model_list)

    # guarantee that we're running this in a new workspace
    arguments['workspace_dir'] = pygeoprocessing.geoprocessing.temporary_folder()
    workspace = arguments['workspace_dir']

    # collect the parameters into a single folder
    input_archive = input_archive_uri
    if input_archive[-7:] == '.tar.gz':
        input_archive = input_archive[:-7]
    data_storage.collect_parameters(arguments, input_archive)
    input_archive += '.tar.gz'

    model_args = data_storage.extract_parameters_archive(workspace, input_archive)

    model.execute(model_args)

    archive_uri = output_archive_uri
    if archive_uri[-7:] == '.tar.gz':
        archive_uri = archive_uri[:-7]
    LOGGER.debug('Archiving the output workspace')
    shutil.make_archive(archive_uri, 'gztar', root_dir=workspace, logger=LOGGER)

