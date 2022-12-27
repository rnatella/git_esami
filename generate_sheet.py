from docxtpl import DocxTemplate
import xlwings as xw
import argparse
import sys
import os
import urllib.parse
from students import Students


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

    try:
        students = Students(xlsx_path)
    except Exception as e:
        print(e)
        sys.exit(1)


    num_students = students.get_num_students()
    print("Total students: " + str(num_students))


    for student in students:

        username = student["username"]
        password = student["password"]
        repository_url = student["repository_url"]
        fullname = student["surname"] + " " + student["firstname"]

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
    


template = DocxTemplate(template_file)
template.render(context)
template.save(target_file)

