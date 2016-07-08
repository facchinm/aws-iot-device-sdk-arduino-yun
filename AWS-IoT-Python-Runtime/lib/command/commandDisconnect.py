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
from core.exception.AWSIoTExceptions import disconnectError
from core.exception.AWSIoTExceptions import disconnectTimeoutException


class commandDisconnect(AWSIoTCommand.AWSIoTCommand):
    # Target API: AWSIoTMQTTShadowClient.disconnect()

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcShadowClient):
        self._commandProtocolName = "d"
        self._parameterList = srcParameterList
        self._serialCommServerHandler = srcSerialCommuteServer
        self._shadowClientHandler = srcShadowClient
        self._desiredNumberOfParameters = 0

    def _validateCommand(self):
        ret = self._shadowClientHandler is not None and self._serialCommServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def execute(self):
        returnMessage = "D T"
        if not self._validateCommand():
            returnMessage = "D1F: " + "No setup."
        else:
            try:
                self._shadowClientHandler.disconnect()
            except disconnectError as e:
                returnMessage = "D2F: " + str(e.message)
            except disconnectTimeoutException as e:
                returnMessage = "D3F: " + str(e.message)
            except Exception as e:
                returnMessage = "DFF: " + "Unknown error."
        self._serialCommServerHandler.writeToInternalProtocol(returnMessage)
