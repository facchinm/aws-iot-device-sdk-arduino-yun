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

import sys
sys.path.insert(0, "../lib/util/")
sys.path.insert(0, "../lib/exception/")
import communicationServer
import AWSIoTExceptions
import Queue
import signal
import logging


class serialCommunicationServer(communicationServer.communicationServer):

    def __init__(self):
        self._log = logging.getLogger(__name__)
        self._protocolMessageQueue = Queue.Queue(0)
        self._yieldMessageQueue = Queue.Queue(0)
        self._jsonBuf = ""
        self._txBuf = ""
        self._acceptTimeout = 0  # Never timeout
        self._chunkSize = 50  # Biggest chunk of data that can be sent over serial1
        self._returnList = []
        self._currentElementOut = ""  # Retained message that needs to be sent out in chunks
        self._lockedQueueSize = 0  # Number of messages to be transmitted in this yield
        # Register timeout signal handler
        signal.signal(signal.SIGALRM, self._timeoutHandler)
        signal.alarm(0)  # disable SIGALRM
        self._log.debug("Register timeout signal handler.")
        self._log.debug("serialCommunicationServer init.")

    def _timeoutHandler(self, signal, frame):
        self._log.debug("Raise a custom exception for accept timeout.")
        raise AWSIoTExceptions.acceptTimeoutException()

    def _basicInput(self):
        return raw_input()

    def _basicOutput(self, srcContent):
        print(srcContent)

    def setAcceptTimeout(self, srcTimeout):
        self._acceptTimeout = srcTimeout
        self._log.debug("serialCommunicationServer set accept timeout to " + str(self._acceptTimeout))

    def getChunkSize(self):
        return self._chunkSize

    def setChunkSize(self, srcChunkSize):
        self._chunkSize = srcChunkSize
        self._log.debug("serialCommunicationServer set chunk size to " + str(self._chunkSize))

    def updateLockedQueueSize(self):
        self._lockedQueueSize = self._yieldMessageQueue.qsize()

    def getLockedQueueSize(self):
        return self._lockedQueueSize

    def accept(self):
        # Messages are passed from remote client to server line by line
        # A number representing the number of lines to receive will be passed first
        # Then serialCommunicationServer should loop the exact time to receive the following lines
        # All these reads add up tp ONE timeout: acceptTimeout. Once exceeded, this timeout will trigger a callback raising an exception
        # Throw acceptTimeoutException, ValueError
        # Store the incoming parameters into an internal data structure
        self._returnList = []
        self._log.debug("Clear internal list. Size: " + str(len(self._returnList)))
        signal.alarm(self._acceptTimeout)  # Enable SIGALRM
        self._log.debug("Accept-timer starts, with acceptTimeout: " + str(self._acceptTimeout) + " second(s).")
        numLines = int(self._basicInput())  # Get number of lines to receive
        self._log.debug(str(numLines) + " lines to be received. Loop begins.")
        loopCount = 1
        while(loopCount <= numLines):
            currElementIn = self._basicInput()
            self._returnList.append(currElementIn)
            self._log.debug("Received: " + str(loopCount) + "/" + str(numLines) + " Message is: " + currElementIn)
            loopCount += 1
        signal.alarm(0)  # Finish reading from remote client, disable SIGALRM
        self._log.debug("Finish reading from remote client. Accept-timer ends.")
        return self._returnList

    def writeToInternalProtocol(self, srcContent):
        self._protocolMessageQueue.put(srcContent)
        self._log.debug("Updated serialCommunicationServer internal protocolMessageQueue by inserting a new message. Size: " + str(self._protocolMessageQueue.qsize()))

    def writeToInternalYield(self, srcContent):
        self._yieldMessageQueue.put(srcContent)
        self._log.debug("Updated serialCommunicationServer internal yieldMessageQueue by inserting a new message. Size: " + str(self._yieldMessageQueue.qsize()))

    def writeToInternalJSON(self, srcContent):
        self._jsonBuf = srcContent
        self._log.debug("Updated serialCommunicationServer internal json buffer with a new JSON payload of size: " + str(len(self._jsonBuf)))

    def writeToExternalYield(self):
        # Write ONE chunk to the remote client
        # If no retained chunks, pick ONE new message from the given messageQueue and start again
        # Messages in the internal messageQueue should be well-formated for yield messages, serialCommunicationServer will do nothing to format it
        if self._lockedQueueSize > 0 or self._currentElementOut != "":
            if self._currentElementOut == "":  # No more chunks left for current retained?
                self._currentElementOut = self._yieldMessageQueue.get()
                self._lockedQueueSize -= 1
                self._log.debug("Start sending a new message to remote client: " + self._currentElementOut)
            self._txBuf = self._currentElementOut[0:self._chunkSize]
            self._basicOutput(self._txBuf)
            self._log.debug("Send through serial to remote client. Chunk: " + self._txBuf + " Size: " + str(len(self._txBuf)))
            self._currentElementOut = self._currentElementOut[self._chunkSize:]
        else:
            self._basicOutput("Y F: No messages.")
            self._log.debug("No more messages for yield. Exiting writeToExternalYield.")

    def writeToExternalProtocol(self):
        # Wrapper for protocol serial communitation
        if not self._protocolMessageQueue.empty():
            thisProtocolMessage = self._protocolMessageQueue.get()
            self._basicOutput(thisProtocolMessage)
            self._log.debug("Send through serial to remote client: " + thisProtocolMessage + " Size: " + str(len(thisProtocolMessage)))
        else:
            self._log.debug("No protocol messages available. Exiting writeToExternalProtocol.")

    def writeToExternalJSON(self):
        # Wrapper for JSON serial communication
        # Only ONE JSON payload will be tracked, this method will be called in a loop util there is not more chunks for THIS payload
        if self._jsonBuf != "":
            self._txBuf = self._jsonBuf[0:self._chunkSize]
            self._basicOutput(self._txBuf)
            self._log.debug("JSON: Send through serial to remote client. Chunk: " + self._txBuf + " Size: " + str(len(self._txBuf)))
            self._jsonBuf = self._jsonBuf[self._chunkSize:]
        else:
            self._basicOutput("J0F: No JSON chunks.")
            self._log.debug("No more chunks for this JSON payload. Exiting writeToExternalJSON.")
