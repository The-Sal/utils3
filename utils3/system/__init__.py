"""Utility Functions for operating system"""
import os
import time
import random
import subprocess
from utils3._classes import Process


_access_id = random.random()

# Store reference to any subprocesses, so they can all be terminated when an error is thrown
_processes: [subprocess.Popen] = []


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


def _require_access_id(function):
    def wrapper(*args, **kwargs):
        global _access_id
        if len(args) == 0:
            return None
        elif args[0] != _access_id:
            return None

        _access_id = random.random()

        new_args = list(args)
        new_args.pop(0)
        return function(*new_args, **kwargs)


    return wrapper


@_terminate_on_error
def command(cmd, read: bool = False, wait: bool = True, supress: bool = True, *args, **kwargs):
    """Run a command"""
    pipe = None

    if supress:
        pipe = subprocess.DEVNULL

    if read:
        pipe = subprocess.PIPE

    process = subprocess.Popen(cmd, stdout=pipe, stderr=pipe, *args, **kwargs)
    _processes.append(process)
    if wait:
        process.wait()

    if read:
        process.wait()
        return process.stdout.read().decode()


def ipAddress(interface='en0'):
    """Get the IP Address of a network interface"""
    assert subprocess.check_call(['which', 'ifconfig'], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE) == 0, "ifconfig not found"
    return command(['ifconfig', interface], read=True).split('inet ')[1].split(' netmask')[0].strip()


def foregroundApplication() -> str:
    """Return the foreground application"""
    foreground = command(['osascript', '-e',
                          'tell application "System Events" to name of first application process whose frontmost is '
                          'true'],
                         read=True)

    return foreground.split('\n')[0]


def allProcesses() -> [Process]:
    """Read all processes running on Mac"""
    allProcs = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE).stdout.read().decode().split('\n')
    allProcs.pop(0)

    procs = []

    for proc in allProcs:
        components = proc.split(' ')
        index = 0
        for component in components:
            if not component != '':
                components.pop(index)

            index += 1

        for component in components:
            if component == '' or component == ' ' or component == '':
                components.remove(component)

            index += 1

        clean_list = list(dict.fromkeys(components))

        try:
            clean_list.remove('')
        except ValueError:
            pass

        if len(clean_list) == 0:
            continue

        owner = clean_list[0]
        pid = clean_list[1]
        cpu_percent = clean_list[2]
        memory_percent = clean_list[3]
        clean_list.pop(0)
        clean_list.pop(1)
        clean_list.pop(2)
        clean_list.pop(3)
        cmd = ' '.join(clean_list)

        try:
            procs.append(Process(owner, pid, cpu_percent, memory_percent, '/' + cmd.split('/', 1)[1]))
        except IndexError:
            procs.append(Process(owner, pid, cpu_percent, memory_percent, cmd))

    return procs


@_terminate_on_error
def killProcess(pid: int, signal: int = 9):
    """Kill a process"""
    assert isinstance(pid, int), "pid must be an int"
    os.kill(pid, signal)


@_terminate_on_error
def killProcessByName(name: str):
    """Kill a process by name. This will scan all processes and kill the first one that matches the name. Note the name
    of the process is the name of the executable, not the name of the process"""
    for proc in allProcesses():
        complete_name = ''
        for part in proc.cmd.split('/'):
            new_path = complete_name + '/' + part
            if os.path.exists(new_path):
                complete_name = new_path

        complete_name = complete_name[1:]
        name_of_proc = complete_name.split('/')[-1]
        if name_of_proc == name:
            killProcess(proc.pid)
            break




# Experimental Functions / "Dangerous" Functions
@_require_access_id
def crashOS():
    """Crash the operating system. This will restart the computer due to a kernel panic"""
    proc = subprocess.Popen([
        '/usr/sbin/bluetoothd',
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.4)
    proc.kill()
    proc.terminate()

