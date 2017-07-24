#!/usr/bin/env python

from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')
