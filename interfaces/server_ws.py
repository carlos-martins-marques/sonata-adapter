#!/usr/local/bin/python3.4

"""
## Copyright (c) 2015 SONATA-NFV, 2017 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).
"""

import os, requests, json, logging

import asyncio

import time

from tornado import websocket, web, ioloop, httpserver

from logger import TangoLogger

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#Log definition to make the slice logs idetified among the other possible 5GTango components.
LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
TangoLogger.getLogger("sonataAdapter:server_ws", logging.DEBUG, log_json=True)
LOG.setLevel(logging.DEBUG)

################################# SERVER WEB SOCKET #####################################

names = [ 'tunnel', 'MTD', 'sonata_adaptor' ]
actions = [ 'registry', 'config', 'get_config', 'deregistry']
ssmId = {}
tunnelLiveWebSockets = {}
mtdLiveWebSockets = {}
sonataAdaptorLiveWebSockets = {}


class WSHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def open(self):
        LOG.info('New connection')


    def on_close(self):
        LOG.info('Connection closed')
        for key, value in tunnelLiveWebSockets.items():
            if self == value:
                tunnelLiveWebSockets.pop(key)
                break
        for key, value in mtdLiveWebSockets.items():
            if self == value:
                mtdLiveWebSockets.pop(key)
                break
        for key, value in sonataAdaptorLiveWebSockets.items():
            if self == value:
                sonataAdaptorLiveWebSockets.pop(key)
                break
    def check_origin(self, origin):
        return True

    
    async def on_message(self, message):
        global ssmId
        LOG.info('message received:  %s' % message)

        messageDict = json.loads(message)
        name = messageDict['name']
        id = messageDict['id']
        action = messageDict['action']

        # registry
        if action == actions[0]:
            if name == names[0]:
                sfuuid = messageDict['sfuuid']
                ssmId[id]=sfuuid
                tunnelLiveWebSockets[sfuuid] = self
            elif name == names[1]:
                sfuuid = messageDict['sfuuid']
                ssmId[id]=sfuuid
                mtdLiveWebSockets[sfuuid] = self
            elif name == names[2]:
                sonataAdaptorLiveWebSockets[id] = self

        # configuration
        elif action == actions[1]:

            #TODO 
            # If the sender is the FSM Tunnel
            if name == names[0]:
                for id in sonataAdaptorLiveWebSockets:
                    
                   toSend = { "name": names[2], "id": id, "action": action, "message": "Configuration OK"}
                   toSendJson = json.dumps(toSend)
                   LOG.info(name + ": send reply message to Sonata Adaptor " + toSendJson)

                   sonataAdaptorLiveWebSockets[id].write_message(toSendJson)
                #LOG.info(name + ": don't send reply message to Sonata Adaptor ")

            # If the sender is the FSM MTD
            elif name == names[1]:
                for id in sonataAdaptorLiveWebSockets:
                    
                   toSend = { "name": names[2], "id": id, "action": action, "message": "Configuration OK"}
                   toSendJson = json.dumps(toSend)
                   LOG.info(name + ": send reply message to Sonata Adaptor " + toSendJson)

                   sonataAdaptorLiveWebSockets[id].write_message(toSendJson)
                #LOG.info(name + ": don't send reply message to Sonata Adaptor ")

            # If the sender is the Sonata Adaptor
            elif name == names[2]:
                if (messageDict['fsm'] == names[0]): 
                    for sfuuid in tunnelLiveWebSockets:
                        
                        toSend = { "name": names[0], "id": sfuuid, "action": action, "parameters": messageDict['parameters']}
                        toSendJson = json.dumps(toSend)
                        LOG.info(name + ": send new message to FSM " + names[0] + " " + toSendJson)

                        tunnelLiveWebSockets[sfuuid].write_message(toSendJson)
                elif (messageDict['fsm'] == names[1]): 
                    for sfuuid in mtdLiveWebSockets:
                        
                        toSend = { "name": names[1], "id": sfuuid, "action": action, "parameters": messageDict['parameters']}
                        toSendJson = json.dumps(toSend)
                        LOG.info(name + ": send new message to FSM " + names[1] + " " + toSendJson)

                        mtdLiveWebSockets[sfuuid].write_message(toSendJson)

                # toSend = { "name": name, "id": id, "action": action, 
                #         "message": "Configuration OK"}
                # toSendJson = json.dumps(toSend)
                # LOG.info(name + ": send reply message to Sonata Adaptor " + toSendJson)
                # self.write_message(toSendJson)

        # get configuration
        elif action == actions[2]:
            #TODO 
            # If the sender is the FSM
            if name == names[0]:
                for id in sonataAdaptorLiveWebSockets:
                    
                    toSend = { "name": names[2], "id": id, "action": actions[2], "parameters": messageDict['parameters']}
                    toSendJson = json.dumps(toSend)
                    LOG.info(name + ": send reply message to Sonata Adaptor" + toSendJson)

                    sonataAdaptorLiveWebSockets[id].write_message(toSendJson)
            elif name == names[1]:
                for id in sonataAdaptorLiveWebSockets:
                    
                    toSend = { "name": names[2], "id": id, "action": actions[2], "parameters": messageDict['parameters']}
                    toSendJson = json.dumps(toSend)
                    LOG.info(name + ": send reply message to Sonata Adaptor" + toSendJson)

                    sonataAdaptorLiveWebSockets[id].write_message(toSendJson)
            # If the sender is the Sonata Adaptor
            elif name == names[2]:
                if (messageDict['fsm'] == names[0]): 
                    for sfuuid in tunnelLiveWebSockets:
                        
                        toSend = { "name": names[0], "id": sfuuid, "action": action}
                        toSendJson = json.dumps(toSend)
                        LOG.info(name + ": send new message to FSM " + names[0] + " " + toSendJson)

                        tunnelLiveWebSockets[sfuuid].write_message(toSendJson)
                elif (messageDict['fsm'] == names[1]): 
                    for sfuuid in mtdLiveWebSockets:
                        
                        toSend = { "name": names[1], "id": sfuuid, "action": action}
                        toSendJson = json.dumps(toSend)
                        LOG.info(name + ": send new message to FSM " + names[1] + " " + toSendJson)

                        mtdLiveWebSockets[sfuuid].write_message(toSendJson)
        # deregistry
        elif action == actions[3]:
            for key, value in sonataAdaptorLiveWebSockets.items():
                if self == value:
                    sonataAdaptorLiveWebSockets.pop(key)
                    break

        else:
            LOG.warning("Action not recognized: " + action)

server_ws = web.Application([
    (r'/ssm', WSHandler),
])