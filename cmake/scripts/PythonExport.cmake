cmake_minimum_required(VERSION 3.16)

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

# message("python3 ${SCRIPT} ${SCRIPT_API_FILE} ${APIUC} ${APILC}")
execute_process(COMMAND python3 ${SCRIPT} ${SCRIPT_API_FILE}
        OUTPUT_VARIABLE PYTHON_EXPORT
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

configure_file(${SCRIPT_API_SOURCE_FILE} ${SCRIPT_API_BINARY_FILE})
