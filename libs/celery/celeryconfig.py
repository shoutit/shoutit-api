BROKER_HOST = "localhost"
BROKER_PORT = 5672
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("celery_tasks", )
