from celery import Celery

# Default Broker for RabbitMQ
app = Celery('tasks', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y
