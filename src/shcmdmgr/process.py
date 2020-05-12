''' Helping functions to handle sub-process creation '''
import subprocess
from shcmdmgr.cio import print_str

def run_script(command_with_arguments):
    try:
        process = subprocess.Popen(command_with_arguments)
        try:
            process.wait()
        except subprocess.TimeoutExpired as ex:
            process.kill()
            raise ex
    except PermissionError:
        print_str('Script: ' + str(command_with_arguments))
        print_str('could not be run, because the file is not executable')
    except KeyboardInterrupt:
        print_str()
