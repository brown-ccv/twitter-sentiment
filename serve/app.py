from flask import Flask, render_template, send_from_directory
import os
import json
import csv

app = Flask(__name__, static_url_path='')

#CSV_DIR = '/data/'
CSV_DIR = 'data/'

data = []
# this assumes that all files within /data/ are of the CSV format we expect
# that's a bit fragile, but as long as the volume isn't used improperly, it'll work
for subdir, dirs, files in os.walk(CSV_DIR):
    print(subdir)
    for file in files:
        print(file)
        with open(os.path.join(subdir, file)) as f:
            r = csv.reader(f)
            for row in r:
                data.append([float(row[2]), row[5], float(row[6])])

@app.route('/')
def hello_world():
    return render_template('visualization.html', data=data)
