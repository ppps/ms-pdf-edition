#!/usr/bin/env python3
"""Morning Star PDF edition

Usage:
    pdf_edition.py DATE

DATE should be in %Y-%m-%d format (2017-12-31).
"""

from datetime import datetime
import logging
from pathlib import Path
import subprocess
import sys

from docopt import docopt
import msutils
import msutils.edition

logger = logging.getLogger(name='pdf_edition')
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


_server_remote_path = Path('/Volumes/Server/')
_server_local_path = Path('~/Server/').expanduser()
if _server_remote_path.exists():
    SERVER_PATH = _server_remote_path
elif _server_local_path.exists():
    SERVER_PATH = _server_local_path
else:
    logger.critical("Can't find server location.")
    sys.exit(1)

COMBINED_PDF_TEMPLATE = '{page.date:MS_%Y_%m_%d.pdf}'


as_export_pdf = '''\
on export_pdf(posix_path, pdf_export_file, page_to_export)
	tell application id "com.adobe.InDesign"
		-- Suppress dialogs
		set user interaction level of script preferences to never interact

		set smallestSize to PDF export preset "MS E-Edition"

		open (POSIX file posix_path as alias)

		tell PDF export preferences to set page range to page_to_export
		export the active document format PDF type to POSIX file pdf_export_file using smallestSize

		close the active document

		-- Restore dialogs
		set user interaction level of script preferences to interact with all
	end tell
end export_pdf

on run {{}}
	export_pdf("{indesign_file}", "{pdf_file}", "{page_to_export}")
end run
'''


as_export_jpg = '''\
on export_jpg(posix_path, jpg_export_file)
	tell application id "com.adobe.InDesign"
		-- Suppress dialogs
		set user interaction level of script preferences to never interact

		open (POSIX file posix_path as alias)

		tell JPEG export preferences
			set JPEG Quality to medium
			set JPEG Rendering style to progressive encoding
			set resolution to 72
			set Page String to "1"
		end tell
		export the active document format JPG to POSIX file jpg_export_file

		close the active document

		-- Restore dialogs
		set user interaction level of script preferences to interact with all
	end tell
end export_jpg

on run {{}}
	export_jpg("{indesign_file}", "{jpg_file}")
end run
'''


def run_applescript(script: str):
    """Run an AppleScript using subprocess and osascript"""
    result = subprocess.run(
        args=['osascript', '-'],
        input=script,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8')
    if result.stderr:
        logger.error('AppleScript stderr: %s', result.stderr.rstrip())
    return result.stdout.rstrip()


def export_indesign_page(page, date):
    """Export an InDesign page using the as_export_pdf AppleScript"""
    pdfs_dir = msutils.edition._edition_subdirectory(
        date, msutils.edition.WEB_PDFS_TEMPLATE)
    pdfs_dir.mkdir(exist_ok=True)

    if len(page.pages) == 1:
        export_nums = [1]
        export_names = [page.path.with_suffix('.pdf').name]
    else:
        export_nums = [2, 3]
        export_names = []
        nums_str = '-'.join(map(str, page.pages))
        for pn in page.pages:
            new_name = page.path.with_suffix('.pdf').name
            new_name = new_name.replace(nums_str, str(pn), 1)
            export_names.append(new_name)

    for indd_page_num, pdf_name in zip(export_nums, export_names):
        logger.info('%s %s', export_nums, export_names)
        run_applescript(as_export_pdf.format(
            indesign_file=page.path,
            pdf_file=pdfs_dir.joinpath(pdf_name),
            page_to_export=indd_page_num
            ))
        logger.info('Exported PDF file: %24s', pdf_name)


def export_front_jpg(page):
    jpg_name = SERVER_PATH.joinpath(
        'Web PDFs', 'MS_{0:%Y_%m_%d}.jpg'.format(page.date))
    run_applescript(as_export_jpg.format(
        indesign_file=page.path,
        jpg_file=jpg_name
        ))
    logger.info('Exported front JPG: %24s', jpg_name.name)


def export_with_ghostscript(export_file, *pdf_paths):
    args = [
        'gs',
        '-sDEVICE=pdfwrite',
        '-dPDFSETTINGS=/screen',
        '-dCompatibilityLevel=1.5',
        '-dNOPAUSE', '-dQUIET', '-dBATCH',
        '-sOutputFile=' + str(export_file)]

    args.extend([str(p) for p in pdf_paths])
    subprocess.run(args)


def save_combined_pdf(date):
    """Combine the web PDF files for date's edition using ghostscript"""
    files = msutils.edition_web_pdfs(date)
    if not files:
        logger.error('No web PDF files found for ghostscript step')
        sys.exit(1)
    combined_file = SERVER_PATH.joinpath(
        'Web PDFs',
        COMBINED_PDF_TEMPLATE.format(page=files[0]))

    export_with_ghostscript(combined_file, *[f.path for f in files])
    logger.info('Saved combined PDF to file: %24s', combined_file.name)


def in_place_reduce_size(pdf_path):
    """Replace a PDF file with a reduced-size version"""
    tmp_name = pdf_path.with_name(pdf_path.name + '.tmp')
    export_with_ghostscript(tmp_name, pdf_path)
    tmp_name.replace(pdf_path)
    logger.info('Reduced size of PDF: %24s', pdf_path.name)


def main():
    edition_date = datetime.strptime(docopt(__doc__)['DATE'], '%Y-%m-%d')
    try:
        files = msutils.edition_indd_files(edition_date)
    except msutils.NoEditionError as e:
        logger.critical(e)
        sys.exit(1)

    for f in files:
        export_indesign_page(f, edition_date)
        if f.pages[0] == 1 and not f.prefix:
            # Require no prefix so supplement fronts
            # don't overwrite the 'real' front
            export_front_jpg(f)
    for p in msutils.edition_web_pdfs(edition_date):
        in_place_reduce_size(p.path)
    save_combined_pdf(edition_date)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception('Uncaught exception in main program')
