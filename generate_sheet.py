from docxtpl import DocxTemplate
import xlwings as xw
import argparse
import sys
import os


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-o', '--output', help="Path to generated DOCX", required=True)
parser.add_argument('-t', '--template', help="Path to template DOCX", required=True)

args = parser.parse_args()

xlsx_path = args.input
target_file = args.output
template_file = args.template

if not os.path.exists(xlsx_path):
    print(f"Error: '{xlsx_path}' not found")
    sys.exit(1)

if not xlsx_path.endswith('.xlsx'):
    print(f"Error: '{xlsx_path}' does not seem an XLSX file")
    sys.exit(1)


if os.path.exists(target_file):
    print(f"Warning: '{target_file}' already existing, overwriting")

if not target_file.endswith('.docx'):
    print(f"Error: '{target_file}' has to be a DOCX file")
    sys.exit(1)


if not os.path.exists(template_file):
    print(f"Error: '{template_file}' not found")
    sys.exit(1)

if not template_file.endswith('.docx'):
    print(f"Error: '{template_file}' has to be a DOCX file")
    sys.exit(1)


wb = xw.Book(xlsx_path)
sheet = wb.sheets[0]


empty_column = sheet.used_range[-1].offset(column_offset=1).column

username_column = None
password_column = None
url_column = None

for col in range(1,empty_column):

    if sheet.range((1,col)).value == "username":
        username_column = col

    if sheet.range((1,col)).value == "password":
        password_column = col

    if sheet.range((1,col)).value == "repository_url":
        url_column = col

if username_column is None or password_column is None or url_column is None:
    print(f"Error: Missing columns in '{xlsx_path}'")
    sys.exit(1)

num_students = sheet.range('A1').end('down').row
print("Total students: " + str(num_students))


context = {
            "row_contents": []
        }

for row in range(2,num_students+1):

    item = {}
    item["username"] = sheet.range((row,username_column)).value
    item["password"] = sheet.range((row,password_column)).value
    item["repository_url"] = sheet.range((row,url_column)).value

    context["row_contents"].append(item)


template = DocxTemplate(template_file)
template.render(context)
template.save(target_file)