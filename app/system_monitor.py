import psutil

def get_system_resources():
    """
    获取系统CPU和内存使用情况
    
    Returns:
        dict: 包含CPU和内存使用情况的字典
    """
    # 获取CPU信息
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # 获取内存信息
    memory = psutil.virtual_memory()
    
    return {
        'cpu': {
            'usage_percent': cpu_percent,
            'core_count': cpu_count
        },
        'memory': {
            'total': int(memory.total / (1024 * 1024)),  # 转换为MB
            'used': int(memory.used / (1024 * 1024)),    # 转换为MB
            'free': int(memory.available / (1024 * 1024)),  # 转换为MB
            'usage_percent': memory.percent
        }
    } 