set export_script to "PATH=/usr/local/bin:$PATH LC_ALL=en_GB.UTF-8 /usr/bin/env python3 /Volumes/Server/Production\\ Resources/Scripts/ms-pdf-edition/pdf_edition.py"
set upload_script to "PATH=/usr/local/bin:$PATH LC_ALL=en_GB.UTF-8 /usr/bin/env python3 -x /Volumes/Server/Production\\ Resources/Scripts/ms-pdf-edition/upload_pdf_edition.py"

set date_options to {"Tomorrow", "Another date"}
set default_date to {"Tomorrow"}
set choice_message to "Which edition do you want to export?"
set dialog_title to "Star PDF edition"

set choice to (choose from list date_options default items default_date with prompt choice_message with title dialog_title) as string
if result is "false" then error number -128


if choice is "Another date" then
	set edition_date to text returned of (display dialog "Please enter the edition date in the format 2000-12-31:" default answer "")
else
	set edition_date to do shell script "date -jv+1d +%Y-%m-%d"
end if

do shell script (export_script & " " & edition_date)
do shell script (upload_script & " " & edition_date)
