#!/usr/bin/env python

from flask import Flask, render_template, request
app = Flask(__name__)


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    print(request.form)
    return render_template('index.html')
