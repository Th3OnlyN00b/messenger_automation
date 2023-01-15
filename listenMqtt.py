import paho.mqtt.client as mqtt
import math
import random
from utils import getGUID
from getCredentials import getCredentials
import json

CHAT_ON = True
FOREGROUND = False

topics = [
    "/t_ms",
    "/thread_typing",
    "/orca_typing_notifications",
    "/orca_presence",
    "/legacy_web",
    "/br_sr",
    "/sr_res",
    "/webrtc",
    "/onevc",
    "/notify_disconnect",
    "/inbox",
    "/mercury",
    "/messaging_events",
    "/orca_message_notifications",
    "/pp",
    "/webrtc_response",
]

def listenMqtt(email: str, password: str, user_id: str, state: dict[str:"Any"]):
    SESSION_ID = math.floor(random.random() * 9007199254740991) + 1
    username = {
        "u": user_id,
        "s": SESSION_ID,
        "chat_on": CHAT_ON,
        "fg": FOREGROUND,
        "d": getGUID(),
        "ct": "websocket",
        #App id from facebook
        "aid": "219994525426954",
        "mqtt_sid": "",
        "cp": 3,
        "ecp": 10,
        "st": topics,
        "pm": [],
        "dc": "",
        "no_auto_fg": True,
        "gas": None
    }
    cookies: dict[str:str] = getCredentials(email, password)

    # TODO: Find out which regions are valid and automatically change them, or remove region (seems to work without it)
    host = f"wss://edge-chat.messenger.com/chat?region=prn&sid={SESSION_ID}"

    options = {
        "clientId": "mqttwsclient", # What type of client we're using. This is the only valid value I know of
        "protocolId": 'MQIsdp', # No clue what this is, extracted from the API request
        "protocolVersion": 3, # Likely to future proof different api changes, changing it breaks things.
        "username": json.dumps(username), # Yes the username really is that complicated. No I don't know why.
        "clean": True, # Unclear. Might not be needed
        "wsOptions": {
            "headers": {
                'Cookie': cookies,
                'Origin': 'https://www.messenger.com',
                'User-Agent': None, # TODO: Should probably allow this to be added at some point
                'Referer': 'https://www.messenger.com',
                'Host': 'edge-chat.messenger.com'
            },
            "origin": 'https://www.messenger.com',
            "protocolVersion": 13
        }
    }

    # Define some inner helper functions that will be used to handle specific querries from mqtt
    def mqtt_on_log(client, userdata, level, buff):
        print("client", client)
        print("userdata", userdata)
        print("level", level)
        print("buff", buff)

    def mqtt_on_connect(client, userdata, flags, rc):
        queue = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": user_id,
        }
        # TODO: Something with paging here maybe?
        if(state['page_id']):
            topic = "/messenger_sync_get_diffs"
            queue.last_seq_id = state["last_seq_id"]
            queue.sync_token = state["sync_token"]
        else:
            topic = "/messenger_sync_create_queue"
            queue.initial_titan_sequence_id = state["last_seq_id"]
            queue.device_params = None
            
        if(state["sync_token"]):
            topic = "/messenger_sync_get_diffs"
            queue.last_seq_id = state["last_seq_id"]
            queue.sync_token = state["sync_token"]
        else:
            topic = "/messenger_sync_create_queue"
            queue.initial_titan_sequence_id = state["last_seq_id"]
            queue.device_params = None
        

    # Make the actual client
    mqtt_client = mqtt.Client()

    # Set the appropriate "on" actions
    mqtt_client.on_log = mqtt_on_log




