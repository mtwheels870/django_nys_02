from celery import Celery
from celery.schedules import crontab
# import MySQLdb
import psycopg2
import random
import string
import time

# settins are not configured
# from django.conf import settings

# This shold match settings.py
default_config = {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'compassblue01',
        'USER': 'cb_admin',
        'PASSWORD': 'Ch0c0late!',
        'HOST': 'localhost',
        'PORT': '5432',
    }

CELERY_TASK_NAME = 'db_update'
RABBITMQ_BROKER = "pyamqp://guest@localhost//"
app = Celery(CELERY_TASK_NAME,
    broker=RABBITMQ_BROKER,
    broker_connection_retry=True,
    broker_connection_retry_on_startup=False
)
# disable UTC to use local time
app.conf.enable_utc = False


# Command line:
# celery -A db_update beat --loglevel=info
@app.task
def generate_data():
    start = time.time()
    try:
        print('generate_data(), check db to track updates.')
        # db = MySQLdb.connect(user='root', passwd="qweqwe", db="celery_test")
        # debug = settings.DEBUG
        # print(f"generate_data(), debug = {debug}")
        # default_config = DATABASES['default']
        db = psycopg2.connect(host=default_config['HOST'],
                database=default_config['NAME'],
                user=default_config['USER'],
                password=default_config['PASSWORD'])

        cursor = db.cursor()
        # c.execute("""SELECT * FROM `student_old`""")
        # print(c.fetchall())
        insert_query = """INSERT INTO `mycalendar_studentold` (`name`, `email`, `address`, `class1`) VALUES (%s, %s, %s, %s)"""

        addr_list = ['Dhaka', 'Rajshahi', 'Gazipur', 'Rangpur']
        letters = string.ascii_lowercase
        for i in range(200000):
            print('id: ', i + 1)
            rand_name = ''.join(random.choice(letters) for _ in range(10))
            query_data = (rand_name, rand_name + '@venturenxt.com', random.choice(addr_list), random.randint(1, 10))
            cursor.execute(insert_query, query_data)
            db.commit()
        db.close()

    except Exception as e:
        print(str(e))
    print('Execution time taken: ', time.time() - start)


@app.task
def update_data():
    start = time.time()
    try:
        print('update_data(), check db to track updates.')
        # debug = settings.DEBUG
        # print(f"generate_data(), debug = {debug}")
        # default_config = DATABASES['default']
        # db = MySQLdb.connect(user='root', passwd="qweqwe", db="celery_test")
        db = psycopg2.connect(host=default_config['HOST'],
                database=default_config['NAME'],
                user=default_config['USER'],
                password=default_config['PASSWORD'])
        cursor = db.cursor()
        offset, limit = 0, 30000
        # MTW truncate_query = """`TRUNCATE TABLE mycalendar_studentnew`"""
        truncate_query = "TRUNCATE TABLE mycalendar_studentnew"
        # query_str = """SELECT * from `mycalendar_studentold` LIMIT %s , %s"""
        query_str = f"SELECT * from mycalendar_studentold LIMIT {limit}"
        insert_query = """INSERT INTO `mycalendar_studentnew` (`id`, `name`, `email`, `address`, `class1`) VALUES (%s, %s, %s, %s, %s)"""
        try:
            # Truncate the table first
            cursor.execute(truncate_query)
            db.commit()
            while True:
                # get data from old table

                # results = c.execute(query_str, (offset, limit))
                results = cursor.execute(query_str)
                print('Total retrieved data: ', results)
                offset += limit

                # rollback test
                # if offset == 30000:
                #     raise Exception('Roll back test')

                if not results:
                    print('Retrieved all data, exiting the function')
                    break

                # insert into new table (should insert rows from old into new)
                data = cursor.fetchall()
                cursor.executemany(insert_query, data)
                db.commit()

        except Exception as err:
            print(str(err))
            db.rollback()

        db.close()

    except Exception as e:
        print(str(e))
    print('Execution time taken: ', time.time() - start)


# add "update_data" task to the beat schedule
app.conf.beat_schedule = {
    # Does this mean, run a crontab job every minute?
    "sync-db": {
        "task": "db_update.update_data",
        "schedule": crontab(minute='*'),
    }
}
