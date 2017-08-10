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

logging.basicConfig(
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{',
    format='{asctime}  {levelname}  {name}  {message}',
    filename=str(Path('~/Library/Logs/pdf_edition.log').expanduser()))
logger = logging.getLogger(name='upload_pdf_edition')

if __name__ == '__main__':
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
