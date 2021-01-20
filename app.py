from flask import Flask, jsonify, render_template, request
from tagger import Tagger

app = Flask(__name__)
tagger = Tagger()

@app.route('/tag_string')
def tag_string():
    original_text = request.args.get('txt', '', type=str)
    text, entities = tagger.tag(original_text)
    return jsonify(text=text, entities=entities)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
