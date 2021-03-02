from flask import Flask, jsonify, request

from tagger import Tagger

app = Flask(__name__)
tagger = Tagger()


@app.route('/tag_string')
def tag_string():
    original_text = request.args.get('txt', '', type=str)
    text, entities = tagger.tag(original_text)
    return jsonify(text=text, entities=entities)

@app.route('/link_entity')
def link_entity():
    original_text = request.args.get('txt', '', type=str)
    snomed_name, snomed_id = tagger.normalize(original_text)
    return jsonify(text=original_text, entities=[f"{snomed_name} ({snomed_id})"])


@app.route('/')
def hello_world():
    return 'Demo: <a href="./tag_string?txt=\'Today I woke up with migraine and I took an aspirine.\'">click here</a>'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
