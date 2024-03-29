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

import logging, datetime, uuid, time, json
from threading import Thread, Lock
import database.database as database
import interfaces.sbi as sbi
from logger import TangoLogger

# INFORMATION
# mutex used to ensure one single access to ddbb (repositories) for the nsi records creation/update/removal
mutex_slice2db_access = Lock()

#Log definition to make the slice logs idetified among the other possible 5GTango components.
LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
TangoLogger.getLogger("sonataAdapter:nsi_translator", logging.DEBUG, log_json=True)
LOG.setLevel(logging.DEBUG)

db = database.slice_database()


################################## THREADs to manage slice requests #################################
# SEND NETWORK SLICE (NS) INSTANTIATION REQUEST
## Objctive: send request 2 GTK to instantiate 
## Params: NSI - parameters given by the user.
class thread_ns_instantiate(Thread):
  def __init__(self, nsi_json):
    Thread.__init__(self)
    self.NSI = {}
    self.req = nsi_json
  
  # Creates the json structure to request a NS instantiation.
  def send_instantiation_request(self):
    LOG.info("Instantiating Slice: " + self.req['nsiId'])
    
    # NS requests information
    data = {}
    data['name'] = self.req['nsiId']
    data['nst_id'] = self.req['nstId']
    data['request_type'] = 'CREATE_SLICE'
    if self.req['instantiation_params']:
      data['instantiation_params'] = self.req['instantiation_params']
  
    # Calls the function towards the GTK
    LOG.info("NS Instantiation request JSON: " + str(data))
    instantiation_response = sbi.net_serv_instantiate(data)
    return instantiation_response

  def update_nsi_notify_instantiate(self):

    sbi.send_metrics(str(self.NSI['name']), 'stop', 'instantiation')

    """     mutex_slice2db_access.acquire()
    try:
      jsonNSI = self.NSI

      # updates the slice information before notifying the GTK
      if (jsonNSI['nsi-status'] == "INSTANTIATING"):
        jsonNSI['nsi-status'] = "INSTANTIATED"

        # validates if any service has error status to apply it to the slice status
        for service_item in jsonNSI['nsr-list']:
          if (service_item['working-status'] == "ERROR"):
            service_item['working-status'] = 'ERROR'
            jsonNSI['nsi-status'] = "ERROR"

        # updates NetSlice template usageState
        if (jsonNSI['nsi-status'] == "INSTANTIATED"):
          nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
          if (nst_descriptor['nstd'].get('usageState') == "NOT_IN_USE"):
            nstParameter2update = "usageState=IN_USE"
            updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])
      
      elif (jsonNSI['nsi-status'] == "TERMINATING"):
        jsonNSI['nsi-status'] = "TERMINATED"

        # updates NetSlice template usageState if no other nsi is instantiated/ready
        nsis_list = nsi_repo.get_all_saved_nsi()
        all_nsis_terminated = True
        for nsis_item in nsis_list:
          if (nsis_item['nst-ref'] == jsonNSI['nst-ref'] and nsis_item['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY"]):
              all_nsis_terminated = False
              break
        
        if (all_nsis_terminated):
          nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
          nst_json = nst_descriptor['nstd']
          if (nst_json['usageState'] == "IN_USE"):
            nstParameter2update = "usageState=NOT_IN_USE"
            updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])

      else:
        # errors are managed in the main thread function (run)
        jsonNSI['nsi-status'] = 'ERROR'
        #TODO: check if any nsr is being instantiated and wait until 
      
      # sends the updated NetSlice instance to the repositories
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.NSI['id'])

    finally:
      # release the mutex for other threads
      mutex_slice2db_access.release()
      
      # creates a thread with the callback URL to advise the GK this slice is READY
      slice_callback = jsonNSI['sliceCallback']
      json_slice_info = {}
      json_slice_info['status'] = jsonNSI['nsi-status']
      json_slice_info['updateTime'] = jsonNSI['updateTime']
      json_slice_info['name'] = jsonNSI['name']
      json_slice_info['instance_uuid'] = jsonNSI['id']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
      LOG.info("Network Slice INSTANTIATION with ID: "+str(self.NSI['id'])+" finished and tng-gtk notified about it.") """
  
  def run(self):

    # acquires mutex to have unique access to the nsi (repositories)
    mutex_slice2db_access.acquire()
    
    instantiation_resp = self.send_instantiation_request()
    if instantiation_resp[1] != 201:
      self.NSI['nsi-status'] = 'ERROR'
      self.NSI['errorLog'] = 'ERROR when instantiating '
    else:
      self.NSI['id'] = self.req['nsiId']
      self.NSI['nsi-status'] = 'INSTANTIATING'
      

    # releases mutex for any other thread to acquire it
    mutex_slice2db_access.release()
    
    if self.NSI['nsi-status'] != 'ERROR':
      # Waits until the NS is instantiated/ready or error
      deployment_timeout = 30 * 60   # 30 minutes

      nsi_instantiated = False
      while deployment_timeout > 0:

        if self.NSI['id'] == self.req['nsiId']:
          uuid = sbi.get_nsi_id_from_name(self.req['nsiId'])
          if (uuid):
            self.NSI['id'] = uuid
          
        if self.NSI['id'] != self.req['nsiId']:
          # Check ns instantiation status
          nsi = sbi.get_saved_nsi(self.NSI['id'])
          if "uuid" in nsi:
            self.NSI = nsi
            self.NSI["id"] = self.NSI["uuid"]
            del self.NSI["uuid"]
          
          if self.NSI['nsi-status'] in ["INSTANTIATED", "ERROR", "READY"]:
            nsi_instantiated = True
          
          # if all services are instantiated, ready or error, break the while loop to notify the GTK
          if nsi_instantiated:
            LOG.info("Network Slice Instantiation request processed for Network Slice with Name: "+str(self.NSI['name']))
            break
    
        time.sleep(1)
        deployment_timeout -= 1
    
      if not nsi_instantiated:
        self.NSI['nsi-status'] = 'ERROR'
        self.NSI['errorLog'] = 'ERROR when terminating with timeout'
    
    
    # Notifies the VS that the Network Slice instantiation process is done (either complete or error)
    #LOG.info("Instantiation Step: Informing VS about the correct end of Network Slice with ID: "+str(self.NSI['id']))
    self.update_nsi_notify_instantiate()


# SEND NETWORK SLICE (NS) TERMINATION REQUEST
## Objctive: send the ns termination request 2 GTK
## Params: nsiId (uuid within the incoming request URL)
class thread_ns_terminate(Thread):
  def __init__(self, NSI):
    Thread.__init__(self)
    self.NSI = NSI
  
  def send_termination_requests(self):
    LOG.info("Terminating Slice: ")

    data = {}
    data["instance_uuid"] = self.NSI['id']
    data["request_type"] = "TERMINATE_SLICE"

    # calls the function towards the GTK
    termination_response = sbi.net_serv_terminate(data)

    return termination_response[0], termination_response[1]
  
  def update_nsi_notify_terminate(self):

    sbi.send_metrics(str(self.NSI['name']), 'stop', 'termination')

    """  mutex_slice2db_access.acquire()
    try:
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # updates nsir fields
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      if jsonNSI['nsi-status'] == "TERMINATING":
        jsonNSI['nsi-status'] = "TERMINATED"
      
      # validates if any service has error status to apply it to the slice status
      for service_item in jsonNSI['nsr-list']:
        if (service_item['working-status'] == "ERROR"):
          jsonNSI['nsi-status'] = "ERROR"
          jsonNSI['errorLog'] = "Network Slice termination not done due to a service termination error."
          break

      # sends the updated nsi to the repositories
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.NSI['id'])

      # updates NetSlice template usageState if no other nsi is instantiated/ready
      nsis_list = nsi_repo.get_all_saved_nsi()
      all_nsis_terminated = True
      for nsis_item in nsis_list:
        if (nsis_item['nst-ref'] == self.NSI['nst-ref'] and nsis_item['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY"]):
            all_nsis_terminated = False
            break
      
      if (all_nsis_terminated):
        nst_descriptor = nst_catalogue.get_saved_nst(self.NSI['nst-ref'])
        nst_json = nst_descriptor['nstd']
        if (nst_json['usageState'] == "IN_USE"):
          nstParameter2update = "usageState=NOT_IN_USE"
          updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, self.NSI['nst-ref'])

    finally:
      # release the mutex for other threads
      mutex_slice2db_access.release()

      # sends the request to notify the GTK the slice is READY
      slice_callback = jsonNSI['sliceCallback']
      json_slice_info = {}
      json_slice_info['status'] = jsonNSI['nsi-status']
      json_slice_info['updateTime'] = jsonNSI['updateTime']
      json_slice_info['name'] = jsonNSI['name']
      json_slice_info['instance_uuid'] = jsonNSI['id']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
      LOG.info("Network Slice TERMINATION with ID: "+str(self.NSI['id'])+" finished and tng-gtk notified about it.") """

  def run(self):

    # acquires mutex to have unique access to the nsi (rpositories)
    mutex_slice2db_access.acquire()
    
    # sends each of the termination requests
    LOG.info("Termination Step: Terminating Network Slice Instantiation.")

    # requests to terminate a NSI
    termination_resp = self.send_termination_requests()
    if termination_resp[1] != 201:
      self.NSI['nsi-status'] = 'ERROR'
      self.NSI['errorLog'] = 'ERROR when terminating '

    
    # releases mutex for any other thread to acquire it
    mutex_slice2db_access.release()

    if self.NSI['nsi-status'] != 'ERROR':
      # Waits until the NS is terminated or error
      deployment_timeout = 30 * 60   # 30 minutes

      nsi_terminated = False
      while deployment_timeout > 0:
        # Check ns instantiation status
        self.NSI = sbi.get_saved_nsi(self.NSI['id'])
      
        self.NSI["id"] = self.NSI["uuid"]
        del self.NSI["uuid"]
        
        if self.NSI['nsi-status'] in ["TERMINATED", "ERROR"]:
          nsi_terminated = True
        
        # if slice is terminated or error, break the while loop to notify the GTK
        if nsi_terminated:
          LOG.info("Network Slice Termination request processed for Network Slice with Name: "+str(self.NSI['name']))
          break
    
        time.sleep(1)
        deployment_timeout -= 1
    
      if not nsi_terminated:
        self.NSI['nsi-status'] = 'ERROR'
        self.NSI['errorLog'] = 'ERROR when terminating with timeout'
    
    # Notifies the VS that the Network Slice termination process is done (either complete or error)
    #LOG.info("Termination Step: Informing about the correct end of Network Slice with ID: "+str(self.NSI['id']))
    self.update_nsi_notify_terminate()

# SEND NETWORK SLICE (NS) CONFIGURATION REQUEST
## Objctive: send the ns configuration request 2 ssm
## Params: nsiId (uuid within the incoming request URL) and parameters
class thread_ns_configure(Thread):
  def __init__(self, NSI):
    Thread.__init__(self)
    self.NSI = NSI
  
  def send_configuration_requests(self):
    LOG.info("Configurating Slice: ")

    # calls the function towards the GTK
    configuration_response = sbi.ws_configure(self.NSI['parameters'], self.NSI['fsm_name'])

    return configuration_response[0], configuration_response[1]
  
  def update_nsi_notify_configure(self):
    sbi.send_metrics(self.NSI['name'], 'stop', self.NSI['parameters']['ruleName'])
  

  def run(self):

    # acquires mutex to have unique access to the nsi (repositories)
    #mutex_slice2db_access.acquire()
    
    # sends each of the termination requests
    LOG.info("Configuration Step: Configuring Network Slice Instantiation.")

    # requests to configure a NSI
    configuration_resp = self.send_configuration_requests()
    if configuration_resp[1] != 202:
      self.NSI['nsi-status'] = 'ERROR'
      self.NSI['errorLog'] = 'ERROR when configuring '

    
    # releases mutex for any other thread to acquire it
    #mutex_slice2db_access.release()

    if self.NSI['nsi-status'] != 'ERROR':
        
      self.NSI['nsi-status'] = "CONFIGURATED"
      nsi_configurated = True
      
      # if slice is configurated or error, break the while loop to notify the GTK
      LOG.info("Network Slice Configuration request processed for Network Slice with Name: "+str(self.NSI['name']))
    
      if not nsi_configurated:
        self.NSI['nsi-status'] = 'ERROR'
        self.NSI['errorLog'] = 'ERROR when configurating with timeout'
    
    # Notifies the VS that the Network Slice configuartion process is done (either complete or error)
    #LOG.info("Configuration Step: Informing about the correct end of Network Slice with Name: "+str(self.NSI['name']))
    self.update_nsi_notify_configure()


################################ NSI CREATION SECTION ##################################
# 1 step: create_nsi (with its internal functions)
# Create the NSIId and store in internal db.
def create_nsi(nsi_json):
  LOG.info("Creating a new Network Slice record before instantiating it.")

   
  # creates NSI ID with the received information
  # This ID will be used as the name in the next interactions
  newNsiId = nsi_json['name'] + "-" + str(uuid.uuid4())
   
  # sending back the response

  return (newNsiId, 201)

 
  
################################ NSI INSTANTIATION SECTION ##################################
# 1 step: instantiate_nsi
# Does all the process to instantiate the NSI
def instantiate_nsi(nsi_json):
  LOG.info("Check for NstID before instantiating it.")
  nstId = nsi_json['nstId']
  catalogue_response = sbi.get_saved_nst(nstId)
  if catalogue_response.get('nstd'):
    nst_json = catalogue_response['nstd']
  else:
    return catalogue_response, catalogue_response['http_code']

  # validate if there is any NSTD
  if not catalogue_response:
    return_msg = {}
    return_msg['error'] = "There is NO NSTd with this uuid in the DDBB."
    return return_msg, 400

  # check if exists another nsir with the same name (nsiId)
  nsirepo_jsonresponse = sbi.get_all_saved_nsi()
  if nsirepo_jsonresponse:
    for nsir_item in nsirepo_jsonresponse:
      if (nsir_item["name"] == nsi_json['nsiId']):
        return_msg = {}
        return_msg['error'] = "There is already an slice with this nsiId."
        return (return_msg, 400)
     
    # Network Slice Placement
  LOG.info("Placement of the Network Service Instantiations.")
  new_nsi_json = nsi_placement(nsi_json, nst_json)

  if new_nsi_json[1] != 200:
    LOG.info("Error returning saved nsir.")
    return (new_nsi_json[0], new_nsi_json[1])
  
  # starts the thread to instantiate while sending back the response
  LOG.info("Network Slice Instance Record created. Starting the instantiation procedure.")
  thread_ns_instantiation = thread_ns_instantiate(new_nsi_json[0])
  thread_ns_instantiation.start()


  return ({},202)
  
# does the NS placement based on the available VIMs resources & the required of each NS.
def nsi_placement(nsi_json, nst_json):

  # get the VIMs information registered to the SP
  vims_list = sbi.get_vims_info()

  # validates if the incoming vim_list is empty (return 500) or not (follow)
  if not 'vim_list' in vims_list:
    return_msg = {}
    return_msg['error'] = "Not found any VIM information, register one to the SP."
    return return_msg, 500

  # NSR PLACEMENT: placement based on the instantiation parameters...
  # TODO Choose vim per service based in instantiation parameters

  city = "IT"
  vimId = ""
  for vim_item in vims_list['vim_list']:
    if (vim_item['type'] == "vm" and vim_item['vim_city'] == city):
      vimId = vim_item['vim_uuid']
      break

  if vimId != "":
    instantiation_params_list = []
    for subnet_item in nst_json["slice_ns_subnets"]:
      service_dict = {}
      service_dict["vim_id"] = vimId
      service_dict["subnet_id"] = subnet_item["id"]
      instantiation_params_list.append(service_dict)
    nsi_json['instantiation_params'] = json.dumps(instantiation_params_list)
  
  return nsi_json, 200


########################################## NSI TERMINATE SECTION #######################################
# 1 step: terminate_nsi
# Does all the process to terminate the NSI
def terminate_nsi(nsiName, TerminOrder):
  #LOG.info("Updating the Network Slice Record for the termination procedure.")
  mutex_slice2db_access.acquire()
  try:
    # Get the uuid from the name provided
    uuid = sbi.get_nsi_id_from_name(nsiName)
    if (uuid):
      terminate_nsi = sbi.get_saved_nsi(uuid)
      if terminate_nsi:
        # if nsi is not in TERMINATING/TERMINATED
        if terminate_nsi['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY", "ERROR"]:
          terminate_nsi['id'] = terminate_nsi['uuid']
          del terminate_nsi['uuid']
        
          terminate_nsi['terminateTime'] = str(datetime.datetime.now().isoformat())
          #terminate_nsi['sliceCallback'] = TerminOrder['callback']
          terminate_nsi['nsi-status'] = "TERMINATING"

          # starts the thread to terminate while sending back the response
          LOG.info("Starting the termination procedure.")
          thread_ns_termination = thread_ns_terminate(terminate_nsi)
          thread_ns_termination.start()

          if db.get_slice(nsiName) is not None:
            db.del_slice(nsiName)


          terminate_value = 202
            
        else:
          terminate_nsi['errorLog'] = "This NSI is either terminated or being terminated."
          terminate_value = 404
      else:
        terminate_nsi['errorLog'] = "There is no NSIR in the db."
        terminate_value = 404
    else:
      terminate_nsi = {}
      terminate_nsi['errorLog'] = "There is no NSIR in the db."
      terminate_value = 404
  finally:
    mutex_slice2db_access.release()
    return (terminate_nsi, terminate_value)

############################################ NSI GET SECTION ############################################
# Gets one single NSI item information
def get_nsi(nsiName, timestamp):
  # Get the uuid from the name provided
  name = 'query'
  uuid = sbi.get_nsi_id_from_name(nsiName)
  if (uuid):
    LOG.info("Retrieving Network Slice Instance with ID: " +str(uuid))
    nsirepo_jsonresponse = sbi.get_saved_nsi(uuid)
    if (nsirepo_jsonresponse): 

      fsm_name = db.get_fsm_name_slice(nsiName)
      if fsm_name is not None:
        if (fsm_name != ""):
          if (fsm_name == "tunnel"):
            name="getvnfinfo"
          elif (fsm_name == "MTD"):
            name="getmtdinfo"
          nsirepo_jsonresponse['parameters'] = sbi.ws_get_info(uuid,fsm_name)

      sbi.send_metrics(nsiName, 'start', name, timestamp)
      # Translate the response
      new_nsirepo_jsonresponse = translate_nsi_from_sonata_to_vs(nsiName, nsirepo_jsonresponse)
      return (new_nsirepo_jsonresponse, 200, name)
    else:
      sbi.send_metrics(nsiName, 'start', name, timestamp)
      return_msg = {}
      return_msg['msg'] = "There are no NSIR with this uuid in the db."
      return (return_msg, 404, name)
  else:
      sbi.send_metrics(nsiName, 'start', name, timestamp)
      return_msg = {}
      return_msg['msg'] = "There are no NSIR with this uuid in the db."
      return (return_msg, 404, name)

# Gets all the existing NSI items
def get_all_nsi():
  LOG.info("Retrieve all existing Network Slice Instance records.")
  nsirepo_jsonresponse = sbi.get_all_saved_nsi()
  if (nsirepo_jsonresponse):
    new_nsirepo_jsonresponse = []
    # Translate the response
    for nsi in nsirepo_jsonresponse:
      new_nsi = translate_nsi_from_sonata_to_vs(None,nsi)
      new_nsirepo_jsonresponse.append(new_nsi)
    return (new_nsirepo_jsonresponse, 200)
  else:
    return_msg = {}
    return_msg['msg'] = "There are no NSIR in the db."
    return (return_msg, 404)

# Translate nsi from sonata format to vs format

""" public class NetworkSliceInstance {

  @Id
  @GeneratedValue
  @JsonIgnore
  private Long id;

  private String name;

  private String description;

  private String nsiId; //ID of the network slice

  private String nstId; //ID of the network slice template

  private String nsdId; //ID of the descriptor of the NFV network service that implements the network slice

  private String nsdVersion; //version of the descriptor of the NFV network service that implements the network slice

  private String dfId; //ID of the deployment flavour in the NFV network service

  private String instantiationLevelId; //ID of the instantiation level in the NFV network service

  @JsonIgnore
  private String oldInstantiationLevelId; //ID of the previous instantiation level when the NFV network service is scaled

  private String nfvNsId; //ID of the NFV network service that implements the network slice

  private boolean soManaged;

  @JsonInclude(JsonInclude.Include.NON_EMPTY)
  @ElementCollection(fetch=FetchType.EAGER)
  @Fetch(FetchMode.SELECT)
  @Cascade(org.hibernate.annotations.CascadeType.ALL)
  private List<String> networkSliceSubnetInstances = new ArrayList<>(); //in case of composite network slice, the ID of its network slice subnets 
  private String tenantId; //owner of the slice

  private NetworkSliceStatus status;

  private String errorMessage; //this field gets a value only in case of failure

  @JsonInclude(JsonInclude.Include.NON_NULL)
  private String nfvNsUrl;

} """

def translate_nsi_from_sonata_to_vs(nsiName, nsi_sonata):
  nsi_vs = {}

  nsi_vs['name'] = nsi_sonata['name']
  nsi_vs['description'] = nsi_sonata['description']
  nsi_vs['nsiId'] = nsi_sonata['name']
  nsi_vs['nstId'] = nsi_sonata['nst-ref']
  nsi_vs['nsdId'] = ""
  nsi_vs['nsdVersion'] = ""
  nsi_vs['dfId'] = ""
  nsi_vs['instantiationLevelId'] = ""
  nsi_vs['nfvNsId'] = ""
  nsi_vs['soManaged'] = False
  nsi_vs['networkSliceSubnetInstances'] = None
  nsi_vs['tenantId'] = ""

  status = db.get_status_slice(nsiName)
  if status is not None:
    nsi_vs['status'] = status
  else:
    nsi_vs['status'] = translate_status_from_sonata_to_vs(nsi_sonata['nsi-status'])

  nsi_vs['errorMessage'] = nsi_sonata['errorLog']
  nsi_vs['nfvNsUrl'] = ""
  if 'parameters' in nsi_sonata:
    nsi_vs['parameters'] = nsi_sonata['parameters']
  else:
    nsi_vs['parameters'] = "{}"

  """ nsi_vs = nsi_sonata """

  return nsi_vs

# Translate status from sonata format to vs format
""" public enum NetworkSliceStatus {

	NOT_INSTANTIATED,
	INSTANTIATING,
	INSTANTIATED,
	UNDER_MODIFICATION,
	TERMINATING,
	TERMINATED,
	FAILED
	
} """
def translate_status_from_sonata_to_vs(status_sonata):
  if status_sonata == "READY":
    status_vs = "INSTANTIATED"
  elif status_sonata == "ERROR":
    status_vs = "FAILED"
  else:
    status_vs = status_sonata

  return status_vs


  ########################################## NSI CONFIGURE SECTION #######################################
# configure_nsi
# Does all the process to configure the NSI
def configure_nsi(nsiName, nsi_json):
  #LOG.info("Updating the Network Slice Record for the configuration procedure.")
  #mutex_slice2db_access.acquire()
  try:
    # Get the uuid from the name provided
    uuid = sbi.get_nsi_id_from_name(nsiName)
    if (uuid):
      configure_nsi = sbi.get_saved_nsi(uuid)
      if configure_nsi:
        # if nsi is in INSTANTIATED
        if configure_nsi['nsi-status'] in ["INSTANTIATED"]:

          #If the config is for receive information, only update the db
          fsm_name=""
          if (nsi_json['parameters']['ruleName'] == "getvnfinfo"):
            fsm_name="tunnel"
            db.update_status_slice("CONFIGURING", nsiName)
            db.update_fsm_name_slice(fsm_name,nsiName)
            configure_value = 201
          elif (nsi_json['parameters']['ruleName'] == "getmtdinfo"):
            fsm_name="MTD"
            db.update_status_slice("CONFIGURING", nsiName)
            db.update_fsm_name_slice(fsm_name,nsiName)
            configure_value = 201

            #If the config is for configure the fsm start the thread
          else:
            if (nsi_json['parameters']['ruleName'] == "addpeer"):
              fsm_name="tunnel"
            elif (nsi_json['parameters']['ruleName'] == "routemgmt"):
              fsm_name="tunnel"
            elif (nsi_json['parameters']['ruleName'] == "activatemtd"):
              fsm_name="MTD"
            elif (nsi_json['parameters']['ruleName'] == "modifymtd"):
              fsm_name="MTD"
            configure_nsi['fsm_name'] = fsm_name
            
            configure_nsi['id'] = configure_nsi['uuid']
            del configure_nsi['uuid']
          
            configure_nsi['configureTime'] = str(datetime.datetime.now().isoformat())
            #configure_nsi['sliceCallback'] = nsiName['callback']
            configure_nsi['nsi-status'] = "CONFIGURING"

            # Add parameters information from json request
            configure_nsi['parameters'] = nsi_json['parameters']

            # starts the thread to configure while sending back the response
            LOG.info("Starting the configuration procedure.")
            thread_ns_configuration = thread_ns_configure(configure_nsi)
            thread_ns_configuration.start()
            thread_ns_configuration.join()
            configure_value = 202

            db.update_status_slice("CONFIGURED", nsiName)
            db.update_fsm_name_slice("",nsiName)  
        else:
          configure_nsi['errorLog'] = "This NSI is not in instantiated or configurated status."
          configure_value = 404
      else:
        configure_nsi['errorLog'] = "There is no NSIR in the db."
        configure_value = 404
    else:
      configure_nsi = {}
      configure_nsi['errorLog'] = "There is no NSIR in the db."
      configure_value = 404
  finally:
    #mutex_slice2db_access.release()
    return ({}, configure_value)
