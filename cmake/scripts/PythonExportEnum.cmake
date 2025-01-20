cmake_minimum_required(VERSION 3.16)

# runs SCRIPT to process SCRIPT_API_FILE, scanning for enum ENUM_NAME.
# Chop ENUM_PREFIX off the beginning of the constants.
# Insert the result into SCRIPT_API_SOURCE_FILE, writing to
# SCRIPT_API_BINARY_FILE.

if(NOT SCRIPT)
    message(FATAL_ERROR "Script needs SCRIPT defined")
endif()
if(NOT SCRIPT_API_SOURCE_FILE)
    message(FATAL_ERROR "Script needs SCRIPT_API_SOURCE_FILE defined")
endif()
if(NOT SCRIPT_API_BINARY_FILE)
    message(FATAL_ERROR "Script needs SCRIPT_API_BINARY_FILE defined")
endif()
if(NOT SCRIPT_API_FILE)
    message(FATAL_ERROR "Script needs SCRIPT_API_FILE defined")
endif()
if(NOT ENUM_NAME)
    message(FATAL_ERROR "Script needs ENUM_NAME defined")
endif()
if(NOT ENUM_PREFIX)
    message(FATAL_ERROR "Script needs ENUM_PREFIX defined")
endif()

execute_process(COMMAND python3 ${SCRIPT} ${SCRIPT_API_FILE} ${ENUM_NAME} ${ENUM_PREFIX}
        OUTPUT_VARIABLE PYTHON_EXPORT
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

configure_file(${SCRIPT_API_SOURCE_FILE} ${SCRIPT_API_BINARY_FILE})
