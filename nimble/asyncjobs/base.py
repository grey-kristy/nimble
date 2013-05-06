from multiprocessing import Manager, Process, Value
from datetime import datetime
import hashlib, Queue, inspect, functools, os, os.path
import time, traceback, json

class Job(object):
    def __init__(self, command, args=None, kwargs=None, jid=None):
        self.jid = jid or '%s%s'%(time.time(), id(self))
        self.command = command
        self.args = args or []
        self.kwargs = kwargs or {}

    def __str__(self):
        return json.dumps([self.command, self.args, self.kwargs])

    @staticmethod
    def loads(name, text):
        command, args, kwargs = json.loads(text)
        return Job(jid=name, command=command, args=args, kwargs=kwargs)

class FunctionProxyProcessor(object):
    def __init__(self, proc):
        self.proc = proc
    
    def process(self, job):
        return getattr(self.proc, job.command)(*job.args, **job.kwargs)

class Dispatcher(object):
    worker_dir='workers/'

    def __init__(self, proc, log_dir, backlog=1024, daemonize=True):
        dtnow = datetime.now()
        wid = '%s_worker'%dtnow

        self.log_dir = log_dir
        self.worker_dir = '%s%s'%(self.log_dir, Dispatcher.worker_dir)
        self.dispatcher_log_file = '%s%s'%(self.log_dir, 'jobs.log')
        Dispatcher.worker_log_file = '%s%s.log'%(self.log_dir, wid)

        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

        if not os.path.exists(self.worker_dir):
            os.mkdir(self.worker_dir)

        with open(self.dispatcher_log_file, 'a+') as log:
            pass

        with open(self.worker_log_file, 'a+') as log:
            pass

        self.log('start', dtnow)

        self.active = Value('d', 1)

        self.worker = Process(target=Dispatcher._worker_proc, args=(wid, self.worker_dir, proc, self.active))
        #self.worker.daemon = daemonize

        self.worker.start()

        self.log('worker', data=[self.worker.pid, wid])

    def log(self, action, data=None):
        procs = {
            'drop': lambda job: '<dropped_job id="%s" command="%s" args="%s" time="%s" />\n'%(job.jid, job.command, job.args, datetime.now()),
            'dispatch': lambda job: '<dispatch_job id="%s" command="%s" args="%s" time="%s" />\n'%(job.jid, job.command, job.args, datetime.now()),
            'start': lambda dtnow: '<log start="%s">\n'%dtnow,
            'close': lambda x: '</log>\n',
            'terminate': lambda err: '<terminated>%s</terminated>\n</log>\n'%err,
            'worker': lambda job: '<worker pid="%s" wid="%s" time="%s" />\n'%(data[0], data[1], datetime.now()),
            'error': lambda ex: '<error time="%s">%s</error>\n'%(datetime.now(), ex),
        }
        with open(self.dispatcher_log_file, 'a+') as log:
            log.write(procs[action](data))

    @staticmethod
    def worker_log(worker, action, job=None):
        procs = {
            'start': lambda job: '<log wid="%s" start="%s">\n'%(worker, datetime.now()),
            'close': lambda job: '</log>\n',
            'drop': lambda job: '<drop_job id="%s" command="%s" args="%s" time="%s" />\n'%(job.jid, job.command, job.args, datetime.now()),
            'got': lambda job: '<get_job id="%s" command="%s" args="%s" time="%s" />\n'%(job.jid, job.command, job.args, datetime.now()),
            'done': lambda job: '<done_job id="%s" time="%s" />\n'%(job.jid, datetime.now()),
            'error': lambda ex: '<error time="%s">%s</error>\n'%(datetime.now(), ex),
        }
        with open(Dispatcher.worker_log_file, 'a+') as log:
            log.write(procs[action](job))
    
    @staticmethod
    def _worker_proc(wid, worker_dir, proc, active):
        Dispatcher.worker_log(wid, 'start', None)

        def process(jdir, jfile, proc):
            with open(os.path.join(jdir, jfile), 'r') as jf:
                job = Job.loads(jfile, jf.read())

                Dispatcher.worker_log(wid, 'got', job)
                try:
                    proc.process(job)
                    Dispatcher.worker_log(wid, 'done', job)
                except Exception as e:
                    Dispatcher.worker_log(wid, 'error', e)
                    return False
            os.remove(os.path.join(jdir, jfile))
            return True

        while True:
            try:
                fnames = os.listdir(worker_dir)
                for fn in fnames:
                    process(worker_dir, fn, proc)

                time.sleep(0.1)
                if not active.value:
                    break;
            except:
                Dispatcher.worker_log(wid, 'error', traceback.format_exc())
                break;

        Dispatcher.worker_log(wid, 'close', None)

    def dispatch(self, command, args):
        job = Job(command=command, args=args)
        try:
            with open('%s/%s'%(self.worker_dir, job.jid), 'w') as jf:
                jf.write(str(job))
            return True
        except:
            self.log('error', traceback.format_exc())
            return False

    def shutdown(self):
        self.active.value = 0
        self.log('close')

class AsyncJobManager(object):
    def __init__(self, proc, log_dir, max_tasks=1024, daemonize=True):
        self.proc = FunctionProxyProcessor(proc)
        self.dispatcher = Dispatcher(proc=self.proc,
                                     log_dir=log_dir,
                                     backlog=max_tasks, 
                                     daemonize=daemonize)

        for name, meth in inspect.getmembers(proc, inspect.ismethod):
            f = AsyncJobManager.wrapped_dispatch(meth, self.dispatcher)
            setattr(self, meth.__name__, f)

    def shutdown(self):
        self.dispatcher.shutdown()

    @staticmethod
    def wrapped_dispatch(func, dispatcher):
        @functools.wraps(func)
        def f(*args):
            return dispatcher.dispatch(command=func.__name__, args=args)
        return f
