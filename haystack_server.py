# haystack_server.py

from util import get_log, bannerfy
from haystack_finder import get_finder
from es_config import ES_CONFIG # used as a base class

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from aiohttp.web import HTTPNotFound, HTTPClientError

from json import JSONDecodeError
from pprint import pformat

finder = get_finder()
routes = web.RouteTableDef()

@routes.get('/*')
async def get_api_description(request: Request) -> Response:
    api_desc = """
<!doctype html><html>
<head><meta charset="utf-8" /><title>Haystack Server API Description</title></head>
<body>
<h1>API Description</h1>
You should send a <em>POST</em> request to this server with the header
<em>content-type: application/json</em> and a json body with the following
structure: <code>{ "question": "..." }</code>.  You will receive a json back
with the answer to the question and some relevant metadata.
</body></html>"""
    return Response(text=api_desc)

@routes.post('/')
async def get_answers(request: Request) -> Response:
    if request.content_type != 'application/json':
        raise HTTPNotFound(reason='content_type != application/json')
    try:
        body = await request.json()
    except JSONDecodeError as e:
        reason = f"{e}\n{pformat(e.doc,indent=4)}"
        raise HTTPClientError(reason=reason)

    try:
        question = body['question']
    except KeyError as e:
        reason = f"json payload must have a 'question' field"
        raise HTTPClientError(reason=reason)

    if not isinstance(question,str):
        reason = f"question must be a string"
        raise HTTPClientError(reason=reason)

    return json_response(finder.get_answers(question, top_k_reader=3))
