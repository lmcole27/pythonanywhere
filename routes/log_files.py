# #LOG FILE PROCESSOR HOMEPAGE
# @app.route('/log', methods=['GET', 'POST'])
# def process_log():
#     return render_template("processlog.html")

# #LOG FILE PROCESSOR OUTPUT
# @app.route('/upload', methods=['POST'])
# def upload():
#     # Check if a file was uploaded
#     if 'file' not in request.files:
#         return render_template("processlog.html")
#     file = request.files['file']

#     # Check if the file has a valid name
#     if file.filename == '':
#         return render_template("processlog.html")

#     #Set variables
#     i_list = [] # list of Unique IDs
#     count = 0 # Number of Unique IDs
#     writeunid = 0 # Indicator of whether this is an error to capture

#     # Read file content directly / load to memory
#     file_content = file.read().decode('utf-8')  # Assuming the file is a text file
#     lines=file_content.splitlines()

#     for line in lines:
#         if 'severity' in line:
#             if 'severity="Critical"' in line:
#                 writeunid = 1
#             else:
#                 writeunid =0
#         if "<unid>" in line and writeunid==1:
#             unid= str(line).strip()
#             i_list.append(unid)
#             writeunid==0

#     for item in i_list:
#         count += 1

#     return render_template("processlog_output.html", DATA=i_list, count=count)

# #LOG FILE PROCESSOR HOMEPAGE
# @app.route('/compare', methods=['GET', 'POST'])
# def comparefiles():
#     return render_template("compare.html")

# #LOG FILE PROCESSOR OUTPUT
# @app.route('/uploadfiles', methods=['POST'])
# def uploadfiles():
#     # Check if a file was uploaded
#     if 'file1' not in request.files:
#         return render_template("compare.html")
#     elif 'file2' not in request.files:
#         return render_template("compare.html")

#     primaryfile = request.files['file1']
#     secondaryfile = request.files['file2']

#     # Check if the file has a valid name
#     if primaryfile.filename == '':
#         return render_template("compare.html")
#     elif secondaryfile.filename == '':
#         return render_template("compare.html")

#     # Read file content directly
#     primaryfile_content = primaryfile.read().decode('utf-8')  # Assuming the file is a text file
#     secondaryfile_content = secondaryfile.read().decode('utf-8')
#     primelines=primaryfile_content.splitlines()
#     secondlines=secondaryfile_content.splitlines()

#         # Initialize an empty set to store the rows
#     primeset = set()
#     secondset = set()
#     missingitemset = set()
#     extraitemset = set()

#     # Initialize count variables
#     primecount = 0
#     secondcount = 0
#     blanks = 0
#     missingcount = 0
#     blanks2 = 0
#     duplicates2 = 0
#     extracount = 0

#     # Append the row to the list
#     for row in primelines:
#         if row == "":
#             blanks += 1
#         else:
#             primeset.add(row)

#     primecount = len(primelines)
#     duplicates = int(primecount) - int(len(primeset)) - int(blanks)

#     for row in secondlines:
#         if row == "":
#             blanks2 += 1
#         else:
#             secondset.add(row)

#     secondcount = len(secondlines)
#     duplicates2 = int(secondcount) - int(len(secondset)) - int(blanks2)

#     for item in primeset:
#         if item not in secondset:
#             missingitemset.add(item)
#             missingcount+=1

#     for item in secondset:
#         if item not in primeset:
#             extraitemset.add(item)
#             extracount += 1

#     # Save to a CSV file
#     with open("output.csv", mode="w", newline="") as csvoutputfile:
#         writer = csv.writer(csvoutputfile)
#         writer.writerow(missingitemset)

#     with open('output.txt', 'w') as txtoutputfile:
#         for row in missingitemset:
#             txtoutputfile.write(row + '\n')

#     return render_template("compare_output.html", missingitemlist=missingitemset, primecount=primecount, secondcount=secondcount, blanks=blanks, duplicates=duplicates, missingcount=missingcount, blanks2=blanks2, extracount=extracount, extraitemlist=extraitemset, duplicates2=duplicates2)


# @app.route('/downloads')
# def download():
#     return render_template('downloads.html')

# @app.route('/download/<filename>')
# def download_file(filename):
#     file_path = filename

#     try:
#         # Serve the file for download
#         return send_file(file_path, as_attachment=True)
#     except Exception as e:
#         return f"Error: {str(e)}", 404
