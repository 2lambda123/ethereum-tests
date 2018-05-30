#!/usr/bin/env python3

# For help:
#
# - Run with no arguments.
# - Ask Everett Hildenbrandt (@ehildenb).

# Goals:
#
# - Validate test inputs with JSON Schemas.
# - Filter test fillers based on properties.
# - Convert between various test filler formats.

# Non-goals:
#
# - Test filling.
# - Test post-state checking.

# Dependencies:
#
# - python-json
# - python-jsonschema

import sys
import os
import json
import jsonschema

exit_status = 0
error_log   = []

def _report(*msg):
    print("== " + sys.argv[0] + ":", *msg, file=sys.stderr)

def _logerror(*msg):
    global exit_status
    _report("ERROR:", *msg)
    error_log.append(" ".join(msg))
    exit_status = 1

def _die(*msg, exit_code=1):
    _report(*msg)
    _report("exiting...")
    sys.exit(exit_code)

def readJSONFile(fname):
    if not os.path.isfile(fname):
        _die("Not a file:", fname)
    with open(fname, "r") as f:
        fcontents = f.read()
        return json.loads(fcontents)

def writeJSONFile(fname, fcontents):
    if not os.path.exists(os.path.dirname(fname)):
        os.makedirs(os.path.dirname(fname))
    with open(fname, "w") as f:
        f.write(json.dumps(fcontents, indent=4, sort_keys=True))

def findTests(filePrefix=""):
    return [ fullTest for fullTest in [ os.path.join(root, file) for root, _, files in os.walk(".")
                                                                 for file in files
                                                                  if file.endswith(".json")
                                      ]
                       if fullTest.startswith(filePrefix)
           ]

def listTests(filePrefixes=[""]):
    return [ test for fPrefix in filePrefixes
                  for test in findTests(filePrefix=fPrefix)
           ]

def validateSchema(jsonFile, schemaFile):
    testSchema = readJSONFile(schemaFile)
    defSchema  = readJSONFile("JSONSchema/definitions.json")
    schema     = { "definitions"        : dict(defSchema["definitions"], **testSchema["definitions"])
                 , "patternProperties"  : testSchema["patternProperties"]
                 }

    jsonInput  = readJSONFile(jsonFile)
    try:
        jsonschema.validate(jsonInput, schema)
    except:
        _logerror("Validation failed:", "schema", schemaFile, "on", jsonFile)

def validateTestFile(jsonFile):
    if jsonFile.startswith("./src/VMTestsFiller/"):
        schemaFile = "JSONSchema/vm-filler-schema.json"
    elif jsonFile.startswith("./src/GeneralStateTestsFiller/"):
        schemaFile = "JSONSchema/st-filler-schema.json"
    elif jsonFile.startswith("./src/BlockchainTestsFiller/"):
        schemaFile = "JSONSchema/bc-filler-schema.json"
    elif jsonFile.startswith("./VMTests/"):
        schemaFile = "JSONSchema/vm-schema.json"
    elif jsonFile.startswith("./GeneralStateTests/"):
        schemaFile = "JSONSchema/st-schema.json"
    elif jsonFile.startswith("./BlockchainTests/"):
        schemaFile = "JSONSchema/bc-schema.json"
    else:
        _logerror("Do not know how to validate file:", jsonFile)
        return
    validateSchema(jsonFile, schemaFile)

def _usage():
    usage_lines = [ ""
                  , "    usage: " + sys.argv[0] + " [list|format|validate]  [<TEST_FILE_PREFIX>*]"
                  , "    where:"
                  , "            list:               command to list the matching tests."
                  , "            format:             command to format/sort the JSON file."
                  , "            validate:           command to check a file against the associated JSON schema (defaults to all files)."
                  , "            <TEST_FILE_PREFIX>: file path prefix to search for tests with."
                  , "                                eg. './src/VMTestsFiller' './VMTests' for all VMTests and their fillers."
                  ]
    _die("\n".join(usage_lines))

def main():
    if len(sys.argv) < 2:
        _usage()
    test_command = sys.argv[1]
    if len(sys.argv) == 2:
        testList = listTests()
    else:
        testList = listTests(filePrefixes=sys.argv[2:])

    if len(testList) == 0:
        _die("No tests listed!!!")

    if test_command == "list":
        testDo = lambda t: print(t)
    elif test_command == "format":
        testDo = lambda t: writeJSONFile(t, readJSONFile(t))
    elif test_command == "validate":
        testDo = validateTestFile
    else:
        _usage()

    for test in testList:
        _report(test_command + ":", test)
        testDo(test)

    if exit_status != 0:
        _die("Errors reported!\n[ERROR] " + "\n[ERROR] ".join(error_log))

if __name__ == "__main__":
    main()
