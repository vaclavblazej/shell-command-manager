''' Helping functions to handle sub-process creation '''
import subprocess

def run_script(command_with_arguments, formatter):
    try:
        process = subprocess.Popen(command_with_arguments)
        try:
            process.wait()
        except subprocess.TimeoutExpired as ex:
            process.kill()
            raise ex
    except PermissionError:
        formatter.print_str('Script: ' + str(command_with_arguments))
        formatter.print_str('could not be run, because the file is not executable')
    except KeyboardInterrupt:
        formatter.print_str()
