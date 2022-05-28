import os
import resource
import subprocess
import sys

def getMem():
    X = resource.getrusage(resource.RUSAGE_CHILDREN)
    res =  X.ru_maxrss
    return res/1024
def pp(allocatedTime, allocatedMemory, INPUT_FILE, CODE_FILE):
    os.chdir('/tmp')
    cmd= f"ulimit -s unlimited; ./{CODE_FILE} < {INPUT_FILE} > comparison_file" # run cpp file 
    def setLimit():
        resource.setrlimit(resource.RLIMIT_CPU, (allocatedTime, allocatedTime))
        resource.setrlimit(resource.RLIMIT_CORE, (allocatedMemory,allocatedMemory))
        #resource.setrlimit(resource.RLIMIT_NPROC, (20,20))
        resource.setrlimit(resource.RLIMIT_FSIZE, (128000000,128000000))
        pass
    info = resource.getrusage(resource.RUSAGE_CHILDREN)
    initUsage = info.ru_stime+ info.ru_utime
    try:
        process = subprocess.run(cmd,shell=True, preexec_fn=setLimit, capture_output=True, timeout=allocatedTime)
    except subprocess.TimeoutExpired as tle:
        print(0)
        print(allocatedTime)
        print(getMem())
        return
    except Exception as e:
        raise(e)
        
    info = resource.getrusage(resource.RUSAGE_CHILDREN)
    userTime = info.ru_stime+ info.ru_utime - initUsage
    returnCode = process.returncode
    stdout = process.stdout
    stderr = process.stderr
    print(returnCode)
    print(userTime)
    print(getMem())