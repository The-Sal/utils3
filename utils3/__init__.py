"""Utility Functions Version 3"""
import os
import io
import sys
import time
import base64
import random
import shutil
import inspect
import traceback
import threading
import subprocess
import playerFramework
from utils3.system import paths

# Store reference to any subprocesses, so they can all be terminated when an error is thrown
_processes: [subprocess.Popen] = []


# Terminate Wrapper
def _terminate_on_error(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            for process in _processes:
                process.kill()
                process.terminate()

    return wrapper


# Functions
@_terminate_on_error
def playAudio(file, type_=0):
    """
    Play an audio file
    :param file: The path to the audio file
    :param type_: 0 = use PyObjC, 1 = use playerFramework
    :return:
    """
    # check if pyobjc is available
    try:
        if type_ == 1:
            raise ImportError
        from AppKit import NSSound
        s = NSSound.alloc().initWithContentsOfFile_byReference_(file, True)
        s.play()
        time.sleep(s.duration())
    except ImportError:
        playerFramework.player(warning=False).play_track(file, True)

def whoCalledMe() -> (str, str):
    """The file the called this function and the name of the function"""
    return inspect.stack()[1][1], inspect.stack()[1][3]

def probe(result_callback: callable):
    """Probe a function to see it's args, kwargs, errors, return value, traceback and execution time.

    :param result_callback: The function to call with the results of the probe, the result will be a dict
        like this:
            {
                "args": [0, 1, 3],
                "kwargs": {
                    "a": 1,
                    "b": 2
                },
                "error": None,
                "return": 5,
                "traceback": "",
                "time": 1.0
            }

    """
    probe_results = {
        'args': [],
        'kwargs': {},
        'error': Exception('No Error'),
        'return': None,
        'time_taken': None,
        'traceback': str()
    }

    def _time_taken(t):
        probe_results['time_taken'] = t

    def probe_decorator(func):
        def probe_wrapper(*args, **kwargs):
            probe_results['args'] = list(args)
            probe_results['kwargs'] = kwargs
            with Timer(_time_taken):
                try:
                    probe_results['return'] = func(*args, **kwargs)
                except Exception as e:
                    probe_results['error'] = e
                    probe_results['traceback'] = traceback.format_exc()
            result_callback(probe_results)

        return probe_wrapper

    return probe_decorator

def redundancy(redundancy_function: callable):
    """
    Redundancy decorator, if the function fails, it will call the redundancy function.

    :param redundancy_function: The function to call if the wrapped function fails
    :return: A decorator that will call the redundancy function if the wrapped function fails
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                e.__str__()
                return redundancy_function(*args, **kwargs)

        return wrapper

    return decorator

def base64File(file_path):
    """Return the base64 encoded contents of a file"""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read())

def base64DecodeFile(file_path, data):
    """Decode base64 data and write it to a file"""
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(data))

def assertTypes(types: [type], auto_convert=True, class_method=False):
    """
    Guarantee that the types of the arguments of a function are correct
    :param class_method: If the decorator is being used on a class method, the first argument will be the class instance
    :param types: A list of types, the length of the list must match the number of arguments
    :param auto_convert: If the types don't match, try to convert them
    :return:
    """
    def assertDecorator(function):
        def assertWrapper(*args, **kwargs):
            args = list(args)
            ref = None
            if class_method:
                ref = args[0]
                args = args[1:]

            for i, arg in enumerate(args):
                if not isinstance(arg, types[i]):
                    if auto_convert:
                        try:
                            args[i] = types[i](arg)
                        except ValueError:
                            raise TypeError(f'Argument {i} must be of type {types[i]}')
                    else:
                        raise TypeError(f'Argument {i} must be of type {types[i]}')

            if ref is not None:
                args.insert(0, ref)

            return function(*args, **kwargs)

        return assertWrapper

    return assertDecorator

def runAsThread(func):
    """Run a function as a thread"""
    def thread_wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    return thread_wrapper


# Classes
class ProxyModule:
    """ProxyModule is a class that allows you to only import the module when it's needed."""

    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None

    def __getattr__(self, name):
        if self.module is None:
            self.module = __import__(self.module_name)
            self._add_attributes()

        return getattr(self.module, name)

    def _add_attributes(self):
        # check the module directory for other python files
        # import them and add them to the module
        # this is used to emulate the 'from' statement (for modules not classes)
        try:
            module_dir = self.module.__path__[0]
        except AttributeError:
            return
        for file in os.listdir(module_dir):
            if file.startswith('.') or file.startswith('__'):
                continue
            if not file.endswith('.py'):
                continue

            try:
                getattr(self.module, file.split('.')[0])
            except AttributeError:
                # the file is not already imported
                try:
                    attrib = __import__(self.module_name + '.' + file.split('.')[0])
                    setattr(self.module, file.split('.')[0], attrib)
                except KeyError:
                    pass
                except ModuleNotFoundError:
                    raise ModuleNotFoundError("Could not import {}".format(file.split('.')[0]))


class Timer:
    """Time how long it takes for a code block to execute"""

    def __init__(self, callback):
        """
        :param callback: A function that takes a single argument, the time elapsed
        """
        self.callback = callback

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        self.end = time.time()
        self.callback(self.end - self.start)


class Coffee:
    """Prevent macOS from sleeping. Call __del__ when the class is no longer needed."""

    def __init__(self):
        self._process = None
        self._kill = False
        self._thread_pool = []
        self._deleted = False

    @_terminate_on_error
    def caffeinate(self):
        """When calling caffeinate the Mac will not sleep until decaffeinate is called.
        Note: A thread will be launched to make sure the caffeinate process is still running,
        THIS THREAD IS NOT A DAEMON THREAD, SO IT WILL NOT TERMINATE WHEN THE PROGRAM ENDS. THIS IS TO ENCOURAGE
        CALLING del ON THE COFFEE OBJECT WHEN IT IS NO LONGER NEEDED."""
        assert self._deleted is False, "This coffee has been deleted"
        self._process = subprocess.Popen(['caffeinate'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _processes.append(self._process)

        def watchProcess():
            while not self._kill:
                if self._process.poll() is not None:
                    self._process = subprocess.Popen(['caffeinate'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    _processes.append(self._process)
                time.sleep(0.1)

            self._process.kill()
            self._process.terminate()

        thread = threading.Thread(target=watchProcess)
        for t in self._thread_pool:
            assert not t.is_alive(), "A coffee thread is still running"
        self._thread_pool.append(thread)
        thread.start()

    @_terminate_on_error
    def decaffeinate(self):
        """Stop the caffeinate process"""
        # Asserting is not really warented only makes an issue when the object is deleted without
        # calling caffeinate

        # assert self._process is not None, "Caffeinate has not been started"
        # assert self._kill is False, "Caffeinate has already been stopped"
        self._kill = True
        time.sleep(0.3)

    def __del__(self):
        self.decaffeinate()
        time.sleep(0.3)
        for t in self._thread_pool:
            assert not t.is_alive(), "A coffee thread is still running"

        for p in _processes:
            p.kill()
            p.terminate()

        _processes.clear()
        self._deleted = True

    def __enter__(self):
        self.caffeinate()
        return self

    def __exit__(self, *args):
        self.decaffeinate()


class Container:
    """A container is a temporary directory that gets created when using the 'with' statement.
    The directory is deleted when the 'with' statement ends. Within the 'with' statement, the
    current working directory is set to the container directory.
    The __enter__ method returns the path in a Path object"""

    def __init__(self):
        self._container = "." + random.randint(0, 9999999).__str__()

    def __enter__(self) -> paths.Path:
        os.mkdir(self._container)
        pth = paths.Path(self._container)
        self._cwd = os.getcwd()
        os.chdir(self._container)
        return pth

    def __exit__(self, *args):
        os.chdir(self._cwd)
        shutil.rmtree(self._container)


class CaptureSTDOUT:
    """Redirect the stdout and stderr to a stringIO object to capture the output"""

    def __init__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr

        self.new_stdout = io.StringIO()
        self.new_stderr = io.StringIO()

    def startCapture(self):
        sys.stdout = self.new_stdout
        sys.stderr = self.new_stderr

    def stopCapture(self):
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr

    def __enter__(self):
        self.startCapture()
        return self

    def __exit__(self, *args):
        self.stopCapture()

    def getStdout(self):
        return self.new_stdout.getvalue()

    def getStderr(self):
        return self.new_stderr.getvalue()


class Suppressor:
    """Supress stdout and stderr. The following methods are available for use:\n
        startSuppression() – Start suppressing stdout and stderr\n
        stopSuppression() – Stop suppressing stdout and stderr\n
        __enter__/__exit__ – Start suppressing stdout and stderr within a code block\n
        @Suppressor – Decorator to suppress stdout and stderr for a function
    """

    def __init__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        self._property = None

    def start_supress(self):
        assert self._property is None  # Avoid @staticmethod
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    def stopSupress(self):
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr

    def __enter__(self):
        self.start_supress()
        return self

    def __exit__(self, *args):
        self.stopSupress()

    @staticmethod
    def __call__(func):
        assert callable(func), "Supress can only be used as a decorator"

        def wrapper(*args, **kwargs):
            with Suppressor():
                return func(*args, **kwargs)

        return wrapper



