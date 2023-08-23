import os
import shutil
from os import path
from os.path import *

def _decoder(string_path: str) -> str:
    """Decodes encoded strings from CLI"""
    if string_path.startswith('~'):
        expanded = path.expanduser('~')
        out = string_path.split('~', 1)[1]
        if out.startswith('/'):
            out = out[1:]

        string_path = path.join(expanded, out)



    if not string_path.__contains__('\\'):
        pass
    else:
        string_path = string_path.replace('\\', '')
    if os.path.exists(string_path):
        if not string_path.startswith('/'):
            string_path = path.join(os.getcwd(), string_path)
        elif string_path.startswith('.'):
            string_path = path.join(os.getcwd(), string_path.split('.', 1)[1])

        if string_path.endswith('.'):
            string_path = string_path[:-1]

        return string_path

    return string_path


class Path:
    """A class that represents a path. Supports relative and absolute paths. OSX support only."""
    def __init__(self, pth, validate=True):
        """
        :param pth: The path to represent as a Path object
        :param validate: Validate any path returned by this object via __getitem__
        """
        self._path = _decoder(pth)
        self._validate = validate



    def exists(self):
        """Check if path exists."""
        return path.exists(self.path)

    def isFile(self):
        """Check if path is a file."""
        return path.isfile(self.path)

    def isDir(self):
        """Check if path is a directory."""
        return path.isdir(self.path)

    @property
    def path(self):
        """Get path."""
        return self._path

    def _assertDir(self):
        assert self.exists(), '{} does not exist'.format(self.path)
        assert self.isDir(), 'Path must be a directory'

    def copyFile(self, src):
        """Copy a file to this path"""
        self._assertDir()
        src = Path(src)
        assert src.exists(), 'Source path does not exist'
        if src.isDir():
            shutil.copytree(src.path, self.path)
        else:
            shutil.copy(src.path, self.path)


    def removeFile(self, filename):
        """Remove a file from this path. File name will be relative to this path."""
        self._assertDir()
        expected_location = join(self.path, filename)
        assert path.exists(expected_location), 'File does not exist'
        if path.isdir(expected_location):
            shutil.rmtree(expected_location)
        else:
            os.remove(expected_location)

    def join(self, *args, modify=True):
        """Join paths. Supports relative and absolute paths. OSX support only.
        :param modify: Modify this path object to the new path
        """
        final = join(self.path, *args)
        new = Path(final, validate=self._validate)

        if modify:
            for attr in dir(new):
                if attr.__contains__('__'):
                    continue
                try:
                    setattr(self, attr, getattr(new, attr))
                except AttributeError:
                    pass

            return self
        else:
            return new

    def __repr__(self):
        return f'<Path: {self.path}>'

    def __str__(self):
        return self.path

    def __eq__(self, other):
        if isinstance(other, Path):
            return self.path == other.path
        elif isinstance(other, str):
            return self.path == other
        else:
            raise TypeError(f'Cannot compare Path and {type(other)}')


    def __enter__(self):
        self._assertDir()
        self.cwd = os.getcwd()
        os.chdir(self.path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.cwd)


    def __getitem__(self, item):
        self._assertDir()
        out = self.join(item)
        if self._validate:
            assert out.exists(), 'Path does not exist'
        return out


    def __delitem__(self, key):
        self._assertDir()
        self.removeFile(key)

    def files(self, absolute=True):
        """Get all files in this path. Returns a list of Path objects."""
        self._assertDir()
        files = []
        if absolute:
            f = os.listdir(self.path)
            for f in f:
                files.append(Path(join(self.path, f)).path)
        else:
            for f in os.listdir(self.path):
                files.append(f)

        return files
