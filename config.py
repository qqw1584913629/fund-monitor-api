"""
API 服务配置文件
集中管理所有可配置项，方便维护和调整
"""

# ==================== 网络配置 ====================

# 请求超时时间（秒）
REQUEST_TIMEOUT = 10

# 并发请求数
MAX_WORKERS = 5

# ==================== 日志配置 ====================

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# 日志格式
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# ==================== 版本信息 ====================

VERSION = "1.0.0"
