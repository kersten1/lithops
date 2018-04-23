#
# (C) Copyright IBM Corp. 2018
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import requests
import base64
import os
import json
import ssl
from urllib.parse import urlparse
import http.client
import logging

logger = logging.getLogger(__name__)


class CloudFunctions(object):

    def __init__(self, config):
        '''
        Constructor
        '''
        self.api_key = str.encode(config['api_key'])
        self.endpoint = config['endpoint'].replace('http:', 'https:')
        self.namespace = config['namespace']
        self.runtime = config['action_name']

        auth = base64.encodestring(self.api_key).replace(b'\n', b'')
        self.headers = {
                'content-type': 'application/json',
                'Authorization': 'Basic %s' % auth.decode('UTF-8')
                }
        
        self.session = requests.session()
        self.session.headers.update(self.headers)
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=256, max_retries=3)
        self.session.mount('https://', adapter)
        
        logger.info('IBM Cloud Functions init for namespace: {}'.format(self.namespace))
        logger.info('IBM Cloud Functions init for host: {}'.format(self.endpoint))
        logger.info('IBM Cloud Functions init for runtime: {}'.format(self.runtime))
        if(logger.getEffectiveLevel() == logging.WARNING):
            print("IBM Cloud Functions init for namespace: {} and host: {}".format(self.namespace,self.endpoint))
            print("IBM Cloud Functions init for runtime: {}".format(self.runtime))
        
    def create_action(self, action_name,  memory=None, timeout=None,
                      code=None, is_binary=True, overwrite=True):
        """
        Create an IBM Cloud Function
        """

        logger.info('I am about to create new cloud function action')
        url = os.path.join(self.endpoint, 'api', 'v1', 'namespaces', self.namespace, 'actions', action_name + "?overwrite=" + overwrite)
        
        data = {}
        limits = {}
        cfexec = {}
        
        if timeout: limits['timeout'] = timeout
        if memory: limits['memory'] = memory
        if limits: data['limits'] = limits

        cfexec['kind'] = 'python'
        cfexec['code'] = base64.b64encode(code) if is_binary else code
        data['exec'] = cfexec

        res = self.session.put(url, json=data, headers=self.headers)
        data = res.json()
        print(data)
        
    def get_action(self, action_name):
        """
        Get an IBM Cloud Function
        """
        print ("I am about to get a cloud function action")
        url = os.path.join(self.endpoint, 'api', 'v1', 'namespaces', self.namespace, 'actions', action_name)
        res = self.session.get(url, headers=self.headers)
        return res.json()
    
    def invoke(self, action_name, payload, invocation_type):
        """
        Invoke an IBM Cloud Function
        """
        executor_id = payload['executor_id']
        call_id = payload['call_id']
        url = os.path.join(self.endpoint, 'api', 'v1', 'namespaces', self.namespace, 'actions', action_name)
        res = self.session.post(url, json=payload)
        data = res.json()
        
        if 'activationId' in data:
            log_msg='Executor ID {} Function {} - Activation ID: {}'.format(executor_id,
                                                                            call_id,
                                                                            data["activationId"])
            logger.info(log_msg)
            if(logger.getEffectiveLevel() == logging.WARNING):
                print(log_msg)
            return data["activationId"]
        else:
            print(data)
            return None
        
    def invoke_(self, action_name, payload, invocation_type):
        """
        Invoke an IBM Cloud Function (alternative)
        """
        executor_id = payload['executor_id']
        call_id = payload['call_id']
        
        url = urlparse(os.path.join(self.endpoint, 'api', 'v1', 'namespaces', self.namespace, 'actions', action_name))
        conn = http.client.HTTPSConnection(url.netloc, context=ssl._create_unverified_context())
        conn.request("POST", url.geturl(), body = json.dumps(payload), headers=self.headers)
        
        activation = {}
        try:
            res = conn.getresponse()
            res = res.read()
            data = json.loads(res.decode("utf-8"))
        except:
            pass
        
        conn.close()
        
        if 'activationId' in data:
            log_msg='Executor ID {} Function {} - Activation ID: {}'.format(executor_id,
                                                                            call_id,
                                                                            data["activationId"])
            logger.info(log_msg)
            if(logger.getEffectiveLevel() == logging.WARNING):
                print(log_msg)
            return data["activationId"]
        else:
            print(activation)