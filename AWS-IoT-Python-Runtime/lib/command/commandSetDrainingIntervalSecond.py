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


class commandSetDrainingIntervalSecond(AWSIoTCommand.AWSIoTCommand):
    # Target API: AWSIoTMQTTClient.configureDrainingFrequency(1/srcDrainingIntervalSecond)

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcMQTTCore):
        self._commandProtocolName = "di"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._mqttCoreHandler = srcMQTTCore
        self._desiredNumberOfParameters = 1

    def _validateCommand(self):
        ret = self._mqttCoreHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "DI T"
        if not self._validateCommand():
            returnMessage = "DI1F: " + "No setup."
        else:
            try:
                self._mqttCoreHandler.configureDrainingFrequency(1/float(self._parameterList[0]))
            except TypeError as e:
                returnMessage = "DI2F: " + str(e.message)
            except ValueError as e:
                returnMessage = "DI3F: " + str(e.message)
            except Exception as e:
                returnMessage = "DIFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
