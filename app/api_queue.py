"""
API请求队列处理模块
提供高并发支持和请求队列管理
"""

import queue
import threading
import time
import traceback
from functools import wraps
from app.unified_logger import logger

# 全局请求队列
request_queue = queue.Queue()

# 请求计数器
request_counter = 0
error_counter = 0

# 队列处理线程数量
WORKER_THREADS = 5

# 队列处理线程列表
worker_threads = []

# 队列状态
queue_running = False

# 锁，用于线程安全的计数器更新
counter_lock = threading.Lock()

def enqueue_request(func, *args, **kwargs):
    """
    将请求加入队列
    
    Args:
        func: 要执行的函数
        args: 位置参数
        kwargs: 关键字参数
        
    Returns:
        任务ID
    """
    global request_counter
    
    with counter_lock:
        request_counter += 1
        task_id = request_counter
        
    # 创建任务
    task = {
        'id': task_id,
        'func': func,
        'args': args,
        'kwargs': kwargs,
        'result_queue': queue.Queue(),
        'timestamp': time.time()
    }
    
    # 加入队列
    request_queue.put(task)
    logger.debug(f"任务 {task_id} 已加入队列")
    
    return task

def queue_processor():
    """队列处理线程函数"""
    global error_counter
    
    logger.info("队列处理线程已启动")
    
    while queue_running:
        try:
            # 从队列获取任务，超时1秒
            try:
                task = request_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            # 处理任务
            try:
                logger.debug(f"处理任务 {task['id']}")
                result = task['func'](*task['args'], **task['kwargs'])
                task['result_queue'].put(('success', result))
            except Exception as e:
                with counter_lock:
                    error_counter += 1
                logger.error(f"任务 {task['id']} 处理失败: {str(e)}")
                logger.debug(traceback.format_exc())
                task['result_queue'].put(('error', str(e)))
            finally:
                request_queue.task_done()
                
        except Exception as e:
            with counter_lock:
                error_counter += 1
            logger.error(f"队列处理线程异常: {str(e)}")
            logger.debug(traceback.format_exc())
            
    logger.info("队列处理线程已停止")

def start_queue_processors():
    """启动队列处理线程"""
    global queue_running, worker_threads
    
    if queue_running:
        return
        
    queue_running = True
    worker_threads = []
    
    # 创建并启动工作线程
    for i in range(WORKER_THREADS):
        thread = threading.Thread(target=queue_processor, daemon=True, name=f"QueueProcessor-{i}")
        thread.start()
        worker_threads.append(thread)
        
    logger.info(f"已启动 {WORKER_THREADS} 个队列处理线程")

def stop_queue_processors():
    """停止队列处理线程"""
    global queue_running
    
    if not queue_running:
        return
        
    queue_running = False
    
    # 等待所有线程结束
    for thread in worker_threads:
        thread.join(timeout=2)
        
    logger.info("所有队列处理线程已停止")

def queue_task(timeout=30):
    """
    将API请求加入队列的装饰器
    
    Args:
        timeout: 超时时间（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 将请求加入队列
            task = enqueue_request(func, *args, **kwargs)
            
            # 等待结果
            try:
                result_type, result = task['result_queue'].get(timeout=timeout)
                if result_type == 'error':
                    raise Exception(result)
                return result
            except queue.Empty:
                raise TimeoutError(f"任务 {task['id']} 处理超时")
                
        return wrapper
    return decorator

def get_queue_stats():
    """获取队列统计信息"""
    return {
        'queue_size': request_queue.qsize(),
        'request_count': request_counter,
        'error_count': error_counter,
        'worker_threads': len(worker_threads),
        'queue_running': queue_running
    }

# 启动队列处理器
start_queue_processors()
