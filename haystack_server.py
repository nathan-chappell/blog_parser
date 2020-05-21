# haystack_server.py

from util import get_log, bannerfy
from haystack_finder import get_finder, Finder
from es_config import ES_CONFIG
from make_index import BlogIndexConfig

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from aiohttp.web import HTTPNotFound, HTTPClientError

from json import JSONDecodeError
from pprint import pformat
from typing import Optional

routes = web.RouteTableDef()
server_log = get_log(__file__, stderr=True)

finder: Optional[Finder] = None

def make_finder(config: ES_CONFIG):
    global finder
    finder = get_finder(config)

@routes.get('/')
async def get_api_description(request: Request) -> Response:
    api_desc = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Haystack Server API Description</title>
</head>
<body>
    <h1>API Description</h1>
    You should send a <em>POST</em> request to this server with the header
    <em>content-type: application/json</em> and a json body with the following
    structure:
    <code>
        <p>{<p>&emsp;"question": "..."</p>}</p>
    </code>
    You will receive a json back with the answer to the question and some
    relevant metadata.
</body>
</html>
"""
    return Response(body=api_desc, content_type='text/html')


@routes.post('/')
async def get_answers(request: Request) -> Response:
    if request.content_type != 'application/json':
        raise HTTPNotFound(reason='content_type != application/json')
    try:
        body = await request.json()
    except JSONDecodeError as e:
        reason = f"(400) {e}\n{pformat(e.doc,indent=4)}"
        #raise HTTPClientError(reason=reason)
        return Response(status=400, text=reason)

    try:
        question = body['question']
    except KeyError as e:
        reason = f"(400) json payload must have a 'question' field"
        #raise HTTPClientError(reason=reason)
        return Response(status=400, text=reason)

    if not isinstance(question, str):
        reason = f"(400) question must be a string"
        #raise HTTPClientError(reason=reason)
        return Response(status=400, text=reason)

    if isinstance(finder,Finder):
        return json_response(finder.get_answers(question, top_k_reader=3))
    else:
        return json_response({'answer': 'I have no brain!'})

def run_server() -> None:
    app = web.Application(logger=server_log)
    app.add_routes(routes)
    web.run_app(app, host='localhost', port=8000)

if __name__ == '__main__':
    run_server()
