import threading
import time

import schedule

from checkin import checkin


def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(3)


def update_schedule(time: str, number: str, password: str):
    """
    :param time: 时间 HH:mm 字符串格式
    :param number: 学号
    :param password: 密码
    """
    schedule.clear(number)
    schedule.every().day.at(time).do(checkin, (number, password)).tag(number)


def delete_schedule(number: str):
    schedule.clear(number)


if __name__ == '__main__':
    # update schedule: update_schedule( ... )
    scheduler()