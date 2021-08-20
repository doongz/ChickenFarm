import os
import sys
import logging
import requests
import argparse
import threading
import getpass
import time
from termcolor import colored
from argparse import RawTextHelpFormatter

from chicken_farm.src.employees import Statistician

KEY = os.getenv('OPERATION_KEY', None)

# def progbar(curr, total, full_progbar):
#     frac = float(curr) / float(total)
#     filled_progbar = int(round(frac * full_progbar))
#     if curr != total:
#         print('|',
#             '#' * filled_progbar + '-' * (full_progbar - filled_progbar),
#             end='\r', file=sys.stderr)
#     else:
#         print(' ', ' ' * full_progbar, end='\r', file=sys.stderr)
#     sys.stderr.flush()


# progbar_event = threading.Event()

# def progbar_thread():
#     for i in range(0, 59):
#         if progbar_event.is_set():
#             progbar(60, 60, 60)
#             break
#         progbar(i, 60, 60)
#         time.sleep(0.5)

def netvalue():
    successes, fails = Statistician(KEY).transport_netvalue()
    print(colored(f"上传基金历史净值成功 {len(successes)} 条。", "green"))
    if len(fails) != 0:
        print(colored(f"上传基金历史净值失败 {len(fails)} 条。", "red"))


def main():
    parser = argparse.ArgumentParser(description=f"",
        formatter_class=RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', '--netvalue', action='store_true',  help='上传最新净值')

    args = parser.parse_args()

    if args.netvalue:
        netvalue()


    return 0


if __name__ == '__main__':
    sys.exit(main())

