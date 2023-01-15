import requests
import html
from bs4 import BeautifulSoup
import json
import esprima
import collections

from getCredentials import getCredentials

EMAIL = "bingexploiter10@gmail.com"
PASSWORD = "Meta2358!"

cookies = getCredentials(email=EMAIL, password=PASSWORD)

inbox_html_resp = requests.get(
    "https://www.messenger.com",
    cookies=cookies
)
inbox_html_resp.raise_for_status()
inbox_html_page = inbox_html_resp.text

try:
    # Find these other values that come with authed calls
    dtsg_ind = inbox_html_page.index('DTSGInitialData') + len('DTSGInitialData",[],{"token":"')
    DTSG = inbox_html_page[dtsg_ind:dtsg_ind + inbox_html_page[dtsg_ind:].index('"')]
    dev_id_ind = inbox_html_page.index('"deviceId":"') + len('"deviceId":"')
    DEVICE_ID = inbox_html_page[dev_id_ind:dev_id_ind + inbox_html_page[dev_id_ind:].index('"')]
    # Version comes escaped in the HTML. The raw strings fix that.
    version_ind = inbox_html_page.index(r'\"version\":', dev_id_ind) + len(r'\"version\":')
    VERSION = inbox_html_page[version_ind:version_ind + inbox_html_page[version_ind:].index('}')]
    doc_id_ind = inbox_html_page.index('"queryID":"', dev_id_ind) + len('"queryID":"')
    DOC_ID = inbox_html_page[doc_id_ind:doc_id_ind + inbox_html_page[doc_id_ind:].index('"')]
    user_id_ind = inbox_html_page.index('"actorID":"') + len('"actorID":"')
    USER_ID = inbox_html_page[user_id_ind:user_id_ind + inbox_html_page[user_id_ind:].index('"')]
except ValueError as e:
    with open('log.html', 'wb') as f:
        f.write(bytes(inbox_html_page, 'utf-8'))
    raise e

with open('log.html', 'wb') as f:
    f.write(bytes(inbox_html_page, 'utf-8'))

print(DTSG)
print(DEVICE_ID)
print(VERSION)
print(DOC_ID)
print(USER_ID)

inbox_resp = requests.post(
    "https://www.messenger.com/api/graphql/",
    cookies=cookies,
    data={
        "fb_dtsg": DTSG,
        "doc_id": DOC_ID,
        "variables": json.dumps({
            "deviceId": DEVICE_ID,
            "requestId": 0,
            "requestPayload": json.dumps({
                "database": 1,
                "version": VERSION,
                "sync_params": json.dumps({})
            }),
            "requestType": 1
        })
    }
)
inbox_resp.raise_for_status()

def is_lightspeed_call(node):
    return (
        node.type == "CallExpression"
        and node.callee.type == "MemberExpression"
        and node.callee.object.type == "Identifier"
        and node.callee.object.name == "LS"
        and node.callee.property.type == "Identifier"
        and node.callee.property.name == "sp"
    )

def parse_argument(node):
    if node.type == "Literal":
        return node.value
    if node.type == "ArrayExpression":
        assert len(node.elements) == 2
        high_bits, low_bits = map(parse_argument, node.elements)
        return (high_bits << 32) + low_bits
    if (
        node.type == "UnaryExpression" and
        node.prefix and
        node.operator == "-"
    ):
        return -parse_argument(node.argument)

inbox_json = inbox_resp.json()
inbox_js = inbox_json["data"]["viewer"]["lightspeed_web_request"]["payload"]

fn_calls = collections.defaultdict(list)

def handle_node(node, meta):
    if not is_lightspeed_call(node):
        return

    args = [parse_argument(arg) for arg in node.arguments]
    (fn_name, *fn_args) = args

    fn_calls[fn_name].append(fn_args)

esprima.parseScript(inbox_js, delegate=handle_node)

conversations = collections.defaultdict(dict)

for args in fn_calls["deleteThenInsertThread"]:
    last_sent_ts, last_read_ts, last_msg, *rest = args
    user_id, last_msg_author = [
        arg for arg in rest if isinstance(arg, int) and arg > 1e14
    ]
    conversations[user_id]["unread"] = last_sent_ts != last_read_ts
    conversations[user_id]["last_message"] = last_msg
    conversations[user_id]["last_message_author"] = last_msg_author

for args in fn_calls["verifyContactRowExists"]:
    user_id, _, _, name, *rest = args
    conversations[user_id]["name"] = name

print(json.dumps(conversations, indent=2))



# print(inbox_html_page)