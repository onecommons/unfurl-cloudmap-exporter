import json
from urllib.parse import unquote

from flask import Flask, jsonify, request
from flask.json import JSONEncoder
import uvicorn

from .cloudmap import handle

app = Flask(__name__)

@app.route('/cloud')
def cloud():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'url is required'}), 400
    
    url = unquote(url)
    root = handle(url)

    def default(o):
        if hasattr(o, 'to_json'):
            return o.to_json()
        raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')
    response = app.response_class(
        response=json.dumps(root, default=default),
        status=200,
        mimetype='application/json'
    )
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8082, interface="wsgi", log_level="info")
