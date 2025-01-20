cmake_minimum_required(VERSION 3.16)

if(NOT INCLUDES_SOURCE_FILE)
    message(FATAL_ERROR "Script needs INCLUDES_SOURCE_FILE defined")
endif()
if(NOT INCLUDES_BINARY_FILE)
    message(FATAL_ERROR "Script needs INCLUDES_BINARY_FILE defined")
endif()
if(NOT API_FILES)
    message(FATAL_ERROR "Script needs API_FILES defined")
endif()

file(READ "${API_FILES}" SCRIPT_API_BINARY_FILES)

foreach(FILE IN LISTS SCRIPT_API_BINARY_FILES)
    file(STRINGS "${FILE}" LINES REGEX "^void init_.*\\(py::module_? &m\\)$")
    if(LINES)
        foreach(LINE IN LISTS LINES)
            if("${LINE}" MATCHES "^void init_(.*)\\(py::module_? &m\\)$")
                set(MOD ${CMAKE_MATCH_1})
                string(REGEX REPLACE "^.*void " "	" LINE "${LINE}")
                string(REGEX REPLACE "Squirrel \\*" "" LINE "${LINE}")
                string(APPEND PYTHON_DEFS "    extern void init_${MOD}(py::module_ &m);\n")
                string(APPEND PYTHON_REGISTER "    proc(\"${MOD}\", &PyTTD::init_${MOD});\n")
            endif()
        endforeach()
    endif()
endforeach()

configure_file(${INCLUDES_SOURCE_FILE} ${INCLUDES_BINARY_FILE})
