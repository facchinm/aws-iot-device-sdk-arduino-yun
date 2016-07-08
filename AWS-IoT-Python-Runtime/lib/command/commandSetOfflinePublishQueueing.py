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


class commandSetOfflinePublishQueueing(AWSIoTCommand.AWSIoTCommand):
    # Target API: AWSIoTMQTTClient.configureOfflinePublishQueueing(srcQueueSize, srcDropBehavior)

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore):
        self._commandProtocolName = "pq"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._desiredNumberOfParameters = 2

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "PQ T"
        if not self._validateCommand():
            returnMessage = "PQ1F: " + "No setup."
        else:
            try:
                # In AWS IoT Python SDK:
                # queueSize == 0 -> queue feature is turned off
                # queueSize == -1 -> queue is infinite
                # In IoT Yun SDK:
                # queueSize == 0 -> queue is infinite
                # queueSize == -1 is not checked
                queueSizeSentToCore = int(self._parameterList[0])
                if int(self._parameterList[0]) == 0:  # Infinite queue
                    queueSizeSentToCore = -1
                if int(self._parameterList[0]) < 0:  # Disable queue
                    queueSizeSentToCore = 0
                self._mqttCoreHandler.configureOfflinePublishQueueing(queueSizeSentToCore, int(self._parameterList[1]))
            except TypeError as e:
                returnMessage = "PQ2F: " + str(e.message)
            except ValueError as e:
                returnMessage = "PQ3F: " + str(e.message)
            except Exception as e:
                returnMessage = "PQFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
