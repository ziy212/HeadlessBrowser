from multiprocessing import Process
import threading,argparse,subprocess,logging,queue,os,time,sys
import psutil

logger = logging.getLogger('phantom-manager')

# each Task object specifies the `url` to be browsed
# for `times` 
class Task:
	def __init__(self, url, times):
        self.url = url
        self.times = times

class Manager(threading.Thread):
    def __init__(self, task_queue, worker_count,
        timeout, user_agent, log_dir, worker_script_path):
        self.__task_queue = queue.Queue()
        self.__worker_count = worker_count
        self.__timeout = timeout
        self.__user_agent = user_agent
        self.__workers = []
        self.__log_dir = []
        self.__total_worker_instances = 1
        self.__worker_script_path = worker_script_path

    def __launch_worker(task):
        try:
            # prepare log path
            o = urlparse(task.url)
            host = o.netloc
            path_name = host + '_' + str(self.__total_worker_instances)
            full_path_name = os.path.join(self.__log_dir,path_name)
            os.makedirs(full_path_name)

            # prepar args
            args = ['phantomjs']
            args[1:1] = [self.__worker_script_path, task.url, str(task.times)]
            
            # start worker process 
            worker = subprocess.Popen(
                args, 
                stdout=open(os.path.join(full_path_name, 'stdout.txt'), 'w'),
                stderr=open(os.path.join(self.directory, 'stderr.txt'), 'w'))
            worker_info = (int(time.time()),task.url, task.times, worker)
            time.sleep(1)

            # update worker info
            self.__total_worker_instances += 1
            self.__workers.append(worker_info)
            logger.info("succeeded to run " + worker_info +
                ", full_path:" + full_path_name)
        except Exception as e:
            logger.error("failed to launch worker "+str(e))
