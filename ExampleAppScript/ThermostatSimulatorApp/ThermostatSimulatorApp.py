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
import getopt
import time
import json
import glob
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
# Tkinter
try:
    import tkinter  # Python 3.x
except ImportError:
    import Tkinter as tkinter

# Class that defines and manages callback used in this app
class ThermoSimAppCallbackPool:
    def __init__(self, srcTkRoot, srcReportedDataDisplayBox, srcDeviceShadowHandler, srcReportedDataVariable, srcDesiredDataVariable):
        self._tkRootHandler = srcTkRoot
        self._reportedDataDisplayBox = srcReportedDataDisplayBox
        self._reportedDataVariableHandler = srcReportedDataVariable
        self._desiredDataVariableHandler = srcDesiredDataVariable
        self._deviceShadowHandler = srcDeviceShadowHandler
        self._reportedTemperatureDataFromNetwork = "XX.X"

    def buttonCallback(self, srcSetTemperatureInputBox, srcDesiredDataVariable):
        desiredData = None
        try:
            desiredData = "{:.1f}".format((float)(srcSetTemperatureInputBox.get()))
            if float(desiredData) >= 100.0:
                print("Cannot set temperature higher than 100 F.")
            elif float(desiredData) <= -100.0:
                print("Cannot set temperature lower than -100 F.")
            else:
                JSONString = '{"state":{"desired":{"Temp":' + str(desiredData) + '}}}'
                srcDesiredDataVariable.set(str(desiredData) + " F")
                self._deviceShadowHandler.shadowUpdate(JSONString, None, 5)
        except ValueError:
            print("Setting desired temperature: Invalid temperature value!")
        except Exception as e:
            print(e.message)

    def shadowGetCallback(self, payload, responseStatus, token):
        print(payload)
        print("---------------")
        print(responseStatus)
        print("\n\n")
        if responseStatus == "accepted":
            try:
                JSONResponseDictionary = json.loads(payload)
                self._reportedTemperatureDataFromNetwork = JSONResponseDictionary[u"state"][u"reported"][u"Temp"]
            except:
                print("Invalid JSON or missing attribute")

    def sendShadowGetForReportedTemperature(self, event=None):
        try:
            self._deviceShadowHandler.shadowGet(self.shadowGetCallback, 5)
        except Exception as e:
            print(e.message)
        self._tkRootHandler.after(500, self.sendShadowGetForReportedTemperature)

    def updateReportedTemperatureDataVariable(self, event=None):
        # Also update the color
        currentDesiredData = self._desiredDataVariableHandler.get()[:4]
        if currentDesiredData != "XX.X":
            if self._reportedTemperatureDataFromNetwork > float(currentDesiredData):
                self._reportedDataDisplayBox.config(fg="blue")
            elif self._reportedTemperatureDataFromNetwork < float(currentDesiredData):
                self._reportedDataDisplayBox.config(fg="red")
            else:
                self._reportedDataDisplayBox.config(fg="black")
        self._reportedDataVariableHandler.set(str(self._reportedTemperatureDataFromNetwork) + " F")
        self._tkRootHandler.after(500, self.updateReportedTemperatureDataVariable)

# Class that generates the GUI and starts the application
class ThermoSimAppGUI:

    _usage = """Usage:

    Make sure that you put all your credentials under: ./certs/
    with the following naming conventions:
    Root CA file: *CA.crt
    Certificate file (not required if using MQTT over WebSocket): *.pem.crt
    Private key file (not required if using MQTT over WebSocket): *.pem.key

    Use X.509 certificate based mutual authentication:
    python ThermostatSimulatorApp -e <endpoint>

    Use MQTT over WebSocket:
    python ThermostatSimulatorApp -e <endpoint> -w

    Type "python ThermostatSimulatorApp -h" for detailed command line options.


    """

    _helpInfo = """Available command line options:
    -e, --endpoint: Your custom AWS IoT custom endpoint
    -w, --websocket: Use MQTT over websocket
    -h, --help: Help infomation


    """

    def __init__(self):
        # Init data members
        # Connection related
        self._endpoint = ""
        self._rootCAFilePathList = ""
        self._certificateFilePathList = ""
        self._privateKeyFilePathList = ""
        self._useWebsocket = False
        self._AWSIoTMQTTShadowClient = None
        self._thermostatSimulatorShadowHandler = None
        # GUI related
        self._tkRootHandler = tkinter.Tk()
        self._reportedDataVariable = None
        self._reportedDataDisplayBox = None
        self._desiredDataVariable = None
        self._desiredDataDisplayBox = None
        self._setTemperatureInputBox = None
        self._setTemperatureButton = None
        # Check command line inputs
        if not self._checkInputs():
            raise ValueError("Malformed/Missing command line inputs.")
        # Create and configure AWSIoTMQTTShadowClient
        self._AWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("ThermostatSimulatorApp", useWebsocket=self._useWebsocket)
        if self._useWebsocket:
            self._AWSIoTMQTTShadowClient.configureEndpoint(self._endpoint, 443)
            self._AWSIoTMQTTShadowClient.configureCredentials(self._rootCAFilePathList[0])
        else:
            self._AWSIoTMQTTShadowClient.configureEndpoint(self._endpoint, 8883)
            self._AWSIoTMQTTShadowClient.configureCredentials(self._rootCAFilePathList[0], self._privateKeyFilePathList[0], self._certificateFilePathList[0])
        self._AWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 128, 20)
        self._AWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)
        self._AWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)
        # Set keepAlive interval to be 1 second and connect
        # Raise exception if there is an error in connecting to AWS IoT
        self._AWSIoTMQTTShadowClient.connect(5)
        self._thermostatSimulatorShadowHandler = self._AWSIoTMQTTShadowClient.createShadowHandlerWithName("room", True)
        # Generate GUI
        self._packModule()

    # Validate command line inputs
    # Return False there is any malformed inputs
    # Return True if all the necessary inputs have been discovered
    def _checkInputs(self):
        gotEoughInputs = True
        # Check command line inputs
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hwe:", ["endpoint=", "websocket", "help"])
            if len(opts) == 0:
                raise getopt.GetoptError("No input parameters")
            for opt, arg in opts:
                if opt in ("-e", "--endpoint"):
                    self._endpoint = arg
                if opt in ("-w", "--websocket"):
                    self._useWebsocket = True
                if opt in ("-h", "--help"):
                    print(self._helpInfo)
                    gotEoughInputs = False
        except getopt.GetoptError:
            print(self._usage)
            gotEoughInputs = False
        # Check credential files
        if gotEoughInputs:
            self._rootCAFilePathList = glob.glob("./certs/*CA.crt")
            if self._useWebsocket:
                gotEoughInputs = gotEoughInputs and len(self._rootCAFilePathList) != 0
                if not gotEoughInputs:
                    print("Missing rootCA in ./certs/")
            else:
                self._certificateFilePathList = glob.glob("./certs/*.pem.crt")
                self._privateKeyFilePathList = glob.glob("./certs/*.pem.key")
                gotEoughInputs = gotEoughInputs and len(self._rootCAFilePathList) != 0 and len(self._certificateFilePathList) != 0 and len(self._privateKeyFilePathList) != 0
                if not gotEoughInputs:
                    print("Missing rootCA, certificate or private key in ./certs/")
        return gotEoughInputs

    def _packModule(self):
        self._tkRootHandler.title("ThermostatSimulatorApp")
        self._tkRootHandler.geometry("500x250")
        self._tkRootHandler.resizable(width=False, height=False)
        # Pack all frames
        baseFrame = tkinter.Frame(self._tkRootHandler)
        temperatureFrame = tkinter.Frame(baseFrame)
        temperatureFrame.pack(side="top")
        controlPanelFrame = tkinter.Frame(baseFrame)
        controlPanelFrame.pack(side="bottom")
        baseFrame.pack()
        # Pack all modules for temperature frame
        self._reportedDataVariable = tkinter.StringVar()
        self._reportedDataVariable.set("XX.X F")
        reportedDataTag = tkinter.Label(temperatureFrame, text="Reported Temperature:", justify="left")
        self._reportedDataDisplayBox = tkinter.Label(temperatureFrame, textvariable=self._reportedDataVariable, font=("Arial", 55), justify="left")
        #
        self._desiredDataVariable = tkinter.StringVar()
        self._desiredDataVariable.set("XX.X F")
        desiredDataTag = tkinter.Label(temperatureFrame, text="Desired Temperature:", justify="left")
        self._desiredDataDisplayBox = tkinter.Label(temperatureFrame, textvariable=self._desiredDataVariable, font=("Arial", 55), justify="left")
        #
        reportedDataTag.pack()
        self._reportedDataDisplayBox.pack()
        desiredDataTag.pack()
        self._desiredDataDisplayBox.pack()
        # Create a callback pool
        self._callbackPoolHandler = ThermoSimAppCallbackPool(self._tkRootHandler, self._reportedDataDisplayBox, self._thermostatSimulatorShadowHandler, self._reportedDataVariable, self._desiredDataVariable)
        # Pack all modules for control panel frame
        self._setTemperatureInputBox = tkinter.Entry(controlPanelFrame)
        self._setTemperatureInputBox.pack(sid="left")
        self._setTemperatureButton = tkinter.Button(controlPanelFrame, text="SET", command=lambda: self._callbackPoolHandler.buttonCallback(self._setTemperatureInputBox, self._desiredDataVariable))
        self._setTemperatureButton.pack()

    def runApp(self):
        # Start and run the app
        self._tkRootHandler.after(500, self._callbackPoolHandler.sendShadowGetForReportedTemperature)  # per 500ms
        self._tkRootHandler.after(500, self._callbackPoolHandler.updateReportedTemperatureDataVariable)  # per 500ms
        self._tkRootHandler.mainloop()

# Main
if __name__ == '__main__':
    # Start the app
    try:
        thisThermoSimAppGUI = ThermoSimAppGUI()
        thisThermoSimAppGUI.runApp()
    except ValueError:
        print("Terminated.")
    except KeyboardInterrupt:
        print("Terminated.")

