import json


class jsonManager:
    # This is the JSON Manager that stores all the complete JSON payload
    # JSON payload can be accessed by keys provided when inserting them
    # History limits can be configured to control the memory consumption
    # For those entries that are exceeding the history limit, they will be overwritten
    _prefix = "JSON-"

    def __init__(self, srcHistoryLimits):
        self._records = dict()
        self._historyLimits = srcHistoryLimits  # 0 means unlimited history
        self._internalCountAccepted = -3
        self._internalCountRejected = -2
        self._internalCountDelta = -1
        # If there is a restriction on JSON history length,
        # initialize these items with None value
        if self._historyLimits >= 3:  # Limited dict
            for i in range(0, self._historyLimits):
                self._records[self._prefix + str(i)] = None
        elif self._historyLimits == 0:  # Unlimited dict
            pass
        else:  # Invalid JSON history length, negative
            raise ValueError('History limits too small.')
        # Set limits for accepted/rejected/delta JSON
        if self._historyLimits % 3 == 0:
            self._acceptedHistoryLimits = self._historyLimits - 3
            self._rejectedHistoryLimits = self._historyLimits - 2
            self._deltaHistoryLimits = self._historyLimits - 1
        elif self._historyLimits % 3 == 1:
            self._acceptedHistoryLimits = self._historyLimits - 1
            self._rejectedHistoryLimits = self._historyLimits - 3
            self._deltaHistoryLimits = self._historyLimits - 2
        else:
            self._acceptedHistoryLimits = self._historyLimits - 2
            self._rejectedHistoryLimits = self._historyLimits - 1
            self._deltaHistoryLimits = self._historyLimits - 3

    def storeNewJSON(self, JSONPayload, Type):
        # Store a new JSON entry into the dictonary
        # Return the key to access this JSON payload
        if JSONPayload == "REQUEST TIME OUT":
            return "JSON-X"
        else:
            tempCount = -1
            if Type == 'accepted':
                if self._historyLimits != 0 and self._internalCountAccepted >= self._acceptedHistoryLimits:
                    self._internalCountAccepted = 0
                else:
                    self._internalCountAccepted += 3
                tempCount = self._internalCountAccepted
            elif Type == 'rejected':
                if self._historyLimits != 0 and self._internalCountRejected >= self._rejectedHistoryLimits:
                    self._internalCountRejected = 1
                else:
                    self._internalCountRejected += 3
                tempCount = self._internalCountRejected
            else:
                if self._historyLimits != 0 and self._internalCountDelta >= self._deltaHistoryLimits:
                    self._internalCountDelta = 2
                else:
                    self._internalCountDelta += 3
                tempCount = self._internalCountDelta
            # Format key
            currKey = self._prefix + str(tempCount)
            # Insert the key-value
            self._records[currKey] = JSONPayload
            # Return the assigned key
            return currKey

    def retrieveJSONByKey(self, key):
        # Get the JSON payload by key
        # If key is not present, None will be returned
        return self._records.get(key)

    def getValueByKeyInJSON(self, JSONPayload, key):
        # Get the value using the key in JSON
        # If key is not present/Invalid JSON input detected, None will be returned
        # ***Need to work on property that contains ':'
        try:
            levels = key.split('"')
            tempDict = json.loads(JSONPayload)
            returnValue = tempDict
            for i in range(0, len(levels)):
                if levels[i] != '':
                    if returnValue is not None:
                        returnValue = returnValue.get(levels[i])
                    else:
                        break
            if returnValue is None:
                return None
            else:
                if isinstance(returnValue, basestring):
                    return returnValue
                else:
                    return json.dumps(returnValue)
        except ValueError:
            return None
