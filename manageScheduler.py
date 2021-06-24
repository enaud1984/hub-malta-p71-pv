from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor,ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ADDED,EVENT_JOB_ERROR
from config import conf
import logging
import logging.handlers

logger = logging.getLogger( __name__ )
class NoRunningFilter(logging.Filter):
    def filter(self, record):
        return record.levelname!='INFO'

my_filter = NoRunningFilter()
logging.getLogger("apscheduler").addFilter(my_filter)
logging.getLogger('apscheduler').propagate = False
logging.getLogger("apscheduler.scheduler").addFilter(my_filter)
logging.getLogger("apscheduler.executors").addFilter(my_filter)
executors = {
'default': ThreadPoolExecutor(conf.max_thread_scheduler),
'processpool': ProcessPoolExecutor(conf.max_instances_scheduler)
}
sched = BackgroundScheduler( daemon=True,executors=executors)

def my_listener(event):
    if hasattr(event,"exception") and event.exception:
        e = event.exception 
        logger.error(f"The job crashed :({event.msg}",e)
    else:
        logger.info('The job {event.job_id} started :)')

def initScheduler():
    sched.add_listener(my_listener, EVENT_JOB_ADDED | EVENT_JOB_ERROR)
    sched.start()  # notice that the "start to watch" process happen here
    
def add_job(send,class_name,timeloop):
    if sched.get_job(class_name) is None:
        sched.add_job( send,'interval',
                                id=class_name,
                                name=class_name,
                                seconds = timeloop,
                                max_instances = conf.max_instances_scheduler )

