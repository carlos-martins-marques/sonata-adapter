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

from flask import Flask, request, jsonify
import logging, json, datetime


import translator.nsi_translator as nsi_translator
import interfaces.validate_incoming_json as json_validator
from logger import TangoLogger

#Log definition to make the slice logs idetified among the other possible 5GTango components.
LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
TangoLogger.getLogger("sonataAdapter:nbi", logging.DEBUG, log_json=True)
LOG.setLevel(logging.DEBUG)

app = Flask(__name__)

#Variables with the API path sections
API_ROOT="/api"
API_VERSION="/v1"
API_NS="/ns"

############################################# NETWORK SLICE PING ############################################
# PING function to validate if the onata-adaptor-docker is active
@app.route('/pings', methods=['GET'])
def getPings():
  ping_response  = {'alive_since': '2018-07-18 10:00:00 UTC', 'current_time': str(datetime.datetime.now().isoformat())}

  return jsonify(ping_response), 200



""" ######################################### NETSLICE TEMPLATE Actions #########################################
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['OPTIONS'])
def optionsAllNST():
  return "Allow: OPTIONS, GET, HEAD, POST", 200

@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['OPTIONS']) 
def optionsOneNST(nstId):
  return "Allow: OPTIONS, GET, HEAD, POST", 200

# CREATES a NetSlice template(NST)
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['POST']) 
def create_slice_template():
  LOG.info("Request to upload a Network Slice Template: " + str(request.json))
  new_nst = nst_manager.create_nst(request.json)
  return jsonify(new_nst[0]), new_nst[1]

# GETS for all the NetSlice Templates (NST) information
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['GET'])
def get_all_slice_templates():
  LOG.info("Request to get ALL Network Slice Templates.")
  args = request.args.to_dict()
  if 'count' in args.keys():
    listNST = nst_manager.get_all_nst_counter()
  else:
    listNST = nst_manager.get_all_nst()

  return jsonify(listNST[0]), listNST[1]

#GETS for a specific NetSlice Template (NST) information
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['GET'])
def get_slice_template(nstId):
  LOG.info("Request to get the Network Slice Template with ID: " + str(nstId))
  returnedNST = nst_manager.get_nst(nstId)

  return jsonify(returnedNST[0]), returnedNST[1]

# DELETES a NetSlice Template
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['DELETE'])
def delete_slice_template(nstId):
  deleted_NSTid = nst_manager.remove_nst(nstId)
  LOG.info("Request to remove Network Slice Template with ID: " + str(nstId))
  
  if deleted_NSTid == 403:
    returnMessage = "Not possible to delete, there are NSInstances using this NSTemplate"
  else:
    returnMessage = "NST with ID:" + str(nstId) + "deleted from catalogues."
  return jsonify(returnMessage) """


######################################### NETSLICE INSTANCE Actions #########################################
# CREATES a NetSlice Identifier (NSI)
@app.route(API_ROOT+API_VERSION+API_NS, methods=['POST'])
def create_slice_identifier():
  LOG.info("Request to create a Network Slice Identifier with the following information: " + str(request.json))
  
  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
  creating_nsiId = json_validator.validate_create_instantiation(request.json)
  
  if (creating_nsiId[1] == 200):
    creating_nsiId = nsi_translator.create_nsi(request.json)
  
  return jsonify(creating_nsiId[0]), creating_nsiId[1]


# INSTANTIATE a NetSlice instance (NSI)
@app.route(API_ROOT+API_VERSION+API_NS+'/<name>/action/instantiate', methods=['PUT'])
def instantiate_slice_instance(name):
  LOG.info("Request to create a Network Slice Instantiation with the following information: " + str(request.json))
  
  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
  instantiating_nsi = json_validator.validate_instantiate_instantiation(request.json)
  
  if (instantiating_nsi[1] == 200):
    instantiating_nsi = nsi_translator.instantiate_nsi(request.json)
  
  return jsonify(instantiating_nsi[0]), instantiating_nsi[1]

# TERMINATES a NetSlice instance (NSI)
@app.route(API_ROOT+API_VERSION+API_NS+'/<name>/action/terminate', methods=['PUT'])
def terminate_slice_instance(name):
  LOG.info("Request to terminate the Network Slice Instantiation according to the following: " + str(request.json))
  
  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 200 ok
  terminating_nsi = json_validator.validate_terminate_instantiation(request.json)
  
  if (terminating_nsi[1] == 200):
    terminating_nsi = nsi_translator.terminate_nsi(name, request.json)  
  
  return jsonify(terminating_nsi[0]), terminating_nsi[1]


# GETS ALL the NetSlice instances (NSI) information
@app.route(API_ROOT+API_VERSION+API_NS, methods=['GET'])
def get_all_slice_instances():
  LOG.info("Request to retreive all the Network Slice Instantiations.")
  allNSI = nsi_translator.get_all_nsi()

  return jsonify(allNSI[0]), allNSI[1]

# GETS a SPECIFIC NetSlice instances (NSI) information
@app.route(API_ROOT+API_VERSION+API_NS+'/<name>', methods=['GET'])
def get_slice_instance(name):
  LOG.info("Request to retrieve the Network Slice Instantiation with Name: " + str(name))
  returnedNSI = nsi_translator.get_nsi(str(name))

  return jsonify(returnedNSI[0]), returnedNSI[1]




