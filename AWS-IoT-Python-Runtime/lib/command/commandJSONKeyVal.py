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


class commandJSONKeyVal(AWSIoTCommand.AWSIoTCommand):
    # Target API: getDesired/ReportedValueByKey(JSONIdentifier, key, externalJSONBuf, bufSize)
    # Parameter list: <JSONIdentifier> <key> <isFirstLoad>

    def __init__(self, srcParameterList, srcSerialCommuteServer, srcJSONManager):
        self._commandProtocolName = "j"
        self._parameterList = srcParameterList
        self._serialCommuteServerHandler = srcSerialCommuteServer
        self._jsonManagerHandler = srcJSONManager
        self._desiredNumberOfParameters = 3

    def _validateCommand(self):
        ret = self._serialCommuteServerHandler is not None
        return ret and AWSIoTCommand.AWSIoTCommand._validateCommand(self)

    def _formatValueIntoChunks(self, srcValue):
        # J <JSON Payload>
        # Generate the meta data
        metaData = "J "
        # Get configured chunk size
        configuredChunkSize = self._serialCommuteServerHandler.getChunkSize()
        # Divide the payload into smaller chunks plus  meta data
        messageChunkSize = configuredChunkSize - len(metaData)
        chunks = [metaData + srcValue[i:i + messageChunkSize] for i in range(0, len(srcValue), messageChunkSize)]
        # Concat them together
        return "".join(chunks)

    def execute(self):
        returnMessage = "J T"  # Placeholder for a successful RPC
        if not self._validateCommand():
            returnMessage = "J1F: No setup."
        else:
            try:
                # Check to see if this is the first get JSON command
                if self._parameterList[2] == '1':
                    # If it is, load in a new JSON payload using the provided identifier/key information
                    JSONWanted = self._jsonManagerHandler.retrieveJSONByKey(self._parameterList[0])
                    if JSONWanted is not None:
                        ValueWanted = self._jsonManagerHandler.getValueByKeyInJSON(JSONWanted, self._parameterList[1])
                        if ValueWanted is not None:
                            # Format the ValueWanted into chunks
                            ValueWantedFormatted = self._formatValueIntoChunks(ValueWanted)
                            returnMessage = ValueWantedFormatted
                        else:
                            returnMessage = "J3F: " + "No such key."
                        # If not, this is a chunk-wise communication from the previous JSON payload
                        # Do nothing
                    else:
                        returnMessage = "J2F: " + "No such JSON identifier."
            except Exception:
                returnMessage = "JFF: " + "Unknown error."
        if self._parameterList[2] == '1':
            self._serialCommuteServerHandler.writeToInternalJSON(returnMessage)
