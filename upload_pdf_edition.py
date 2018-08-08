#!/usr/bin/env python3
"""Morning Star PDF edition uploader

Usage:
    upload_pdf_edition.py DATE

DATE should be in %Y-%m-%d format (2017-12-31).
"""
from datetime import datetime
import logging
from pathlib import Path
import sys

import boto3
from docopt import docopt

logger = logging.getLogger(name='upload_pdf_edition')
library_log_handler = logging.FileHandler(
        filename=Path('~/Library/Logs/pdf_edition.log').expanduser())
desktop_log_handler = logging.FileHandler(
        filename=Path('~/Desktop/e-edition-problems.txt').expanduser())
formatter = logging.Formatter(
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{',
    fmt='{asctime}  {levelname}  {name}  {message}')
library_log_handler.setFormatter(formatter)
desktop_log_handler.setFormatter(formatter)
library_log_handler.setLevel(logging.INFO)
desktop_log_handler.setLevel(logging.ERROR)
logger.addHandler(library_log_handler)
logger.addHandler(desktop_log_handler)


def main():
    _server_remote_path = Path('/Volumes/Server/')
    _server_local_path = Path('~/Server/').expanduser()
    if _server_remote_path.exists():
        SERVER_PATH = _server_remote_path
    elif _server_local_path.exists():
        SERVER_PATH = _server_local_path
    else:
        logger.critical("Can't find server location.")
        sys.exit(1)

    date = datetime.strptime(docopt(__doc__)['DATE'], '%Y-%m-%d').date()
    pdf_path = SERVER_PATH.joinpath(
        'Web PDFs', date.strftime('MS_%Y_%m_%d.pdf'))
    jpg_path = pdf_path.with_suffix('.jpg')

    if not (pdf_path.exists() and jpg_path.exists()):
        logger.critical('Missing PDF or JPG for %s', date)
        sys.exit(1)

    s3 = boto3.client('s3')
    s3.upload_file(str(pdf_path), 'rjw-ppps', pdf_path.name)
    logger.info('Uploaded PDF for %s', date)
    s3.upload_file(str(jpg_path), 'rjw-ppps', jpg_path.name)
    logger.info('Uploaded JPG for %s', date)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception('Uncaught exception in main program')
