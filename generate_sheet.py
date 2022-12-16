from docxtpl import DocxTemplate
import xlwings as xw
import argparse
import sys
import os
import urllib.parse


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', nargs='+', help="Path to XLSX with list of students", required=True)
parser.add_argument('-o', '--output', help="Path to generated DOCX", required=True)
parser.add_argument('-t', '--template', help="Path to template DOCX", required=True)
parser.add_argument('-r', '--replace_domain', help="Replace domain in Git repo URL")

args = parser.parse_args()

xlsx_files = args.input
target_file = args.output
template_file = args.template
domain = args.replace_domain


for xlsx_path in xlsx_files:

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



context = {
            "row_contents": []
        }


for xlsx_path in xlsx_files:

    print(f"Parsing '{xlsx_path}'")

    wb = xw.Book(xlsx_path)
    sheet = wb.sheets[0]

    empty_column = sheet.used_range[-1].offset(column_offset=1).column

    username_column = None
    password_column = None
    url_column = None
    name_column = None
    surname_column = None

    for col in range(1,empty_column):

        if sheet.range((1,col)).value == "username":
            username_column = col

        if sheet.range((1,col)).value == "password":
            password_column = col

        if sheet.range((1,col)).value == "repository_url":
            url_column = col
        
        if sheet.range((1,col)).value.casefold() == "cognome":
            surname_column = col

        if sheet.range((1,col)).value.casefold() == "nome":
            name_column = col

    if username_column is None or password_column is None or url_column is None:
        print(f"Error: Missing columns in '{xlsx_path}'")
        sys.exit(1)

    num_students = sheet.range('A1').end('down').row
    print("Total students: " + str(num_students))


    for row in range(2,num_students+1):

        username = sheet.range((row,username_column)).value
        password = sheet.range((row,password_column)).value
        repository_url = sheet.range((row,url_column)).value
        fullname = sheet.range((row,surname_column)).value + " " + sheet.range((row,name_column)).value

        if username is None or password is None or repository_url is None:
            print(f"Empty field(s) for user '{username}', skipping...")
            continue

        item = {}
        item["username"] = username
        item["password"] = password
        item["fullname"] = fullname

        if domain is not None:

            parsed = urllib.parse.urlparse(repository_url)

            replaced_info = []

            if parsed.username is not None:
                replaced_info.append(parsed.username)

                if parsed.password is not None:
                    replaced_info.append(f":{parsed.password}")

                replaced_info.append("@")
            
            replaced_info.append(domain)

            if parsed.port is not None:
                replaced_info.append(f":{parsed.port}")

            replaced = parsed._replace(netloc=''.join(replaced_info))

            item["repository_url"] = urllib.parse.urlunparse(replaced)

        else:
            item["repository_url"] = repository_url


        context["row_contents"].append(item)
    
    wb.close()


template = DocxTemplate(template_file)
template.render(context)
template.save(target_file)

