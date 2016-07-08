'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

import AWSIoTCommand
from core.exception.AWSIoTExceptions import publishError
from core.exception.AWSIoTExceptions import publishTimeoutException
from core.exception.AWSIoTExceptions import publishQueueFullException
from core.exception.AWSIoTExceptions import publishQueueDisabledException


class commandPublish(AWSIoTCommand.AWSIoTCommand):
    # Target API: AWSIoTMQTTClient.publish(topic, payload, qos)

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore):
        self._commandProtocolName = "p"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._desiredNumberOfParameters = 4

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "P T"
        if not self._validateCommand():
            returnMessage = "P1F: " + "No setup."
        else:
            try:
                # Retain flag is ignored
                self._mqttCoreHandler.publish(self._parameterList[0], self._parameterList[1], int(self._parameterList[2]))
            except TypeError as e:
                returnMessage = "P2F: " + str(e.message)
            except publishError as e:
                returnMessage = "P3F: " + str(e.message)
            except publishTimeoutException as e:
                returnMessage = "P4F: " + str(e.message)
            except publishQueueFullException as e:
                returnMessage = "P5F: " + str(e.message)
            except publishQueueDisabledException as e:
                returnMessage = "P6F: " + str(e.message)
            except Exception as e:
                returnMessage = "PFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
