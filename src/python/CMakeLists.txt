add_files(
    call_py.hpp call_py.cpp
    instance.hpp instance.cpp
    msg.cpp
    msg_base.hpp msg_base.cpp
    msg_command.hpp msg_command.cpp
    msg_console.hpp msg_console.cpp
    msg_mode.hpp msg_mode.cpp
    object.hpp object.cpp
    queues.hpp queues.cpp
    setup.hpp setup.cpp
    support.hpp support.cpp
    task.hpp task.cpp
    wrap.hpp wrap.cpp
    )

nanobind_build_library(nanobind-static)

target_include_directories(openttd_lib PUBLIC
    ${Python_INCLUDE_DIRS}
    ${NB_DIR}/include)

#target_include_directories(openttd PUBLIC
#    ${Python_INCLUDE_DIRS}
#    ${NB_DIR}/include)
#
#target_link_libraries(openttd_lib
#     nanobind-static ${Python_LIBRARIES})

target_link_libraries(openttd
     nanobind-static ${Python_LIBRARIES})

 target_link_libraries(openttd_test PRIVATE
     nanobind-static ${Python_LIBRARIES})

nanobind_compile_options(openttd_lib)

nanobind_link_options(openttd)
nanobind_link_options(openttd_test)

# The code below auto-generates bindings for scripting

file(GLOB SCRIPT_API_FILES "${CMAKE_SOURCE_DIR}/src/script/api/script_*.hpp")

foreach(SCRIPT_API_FILE IN LISTS SCRIPT_API_FILES)
    if("${SCRIPT_API_FILE}" MATCHES ".*script_controller.*")
        continue()
    endif()
    if("${SCRIPT_API_FILE}" MATCHES ".*info_docs.*")
        continue()
    endif()
    get_filename_component(SCRIPT_API_FILE_NAME "${SCRIPT_API_FILE}" NAME_WE)
    string(REPLACE "script_" "python_" SCRIPT_API_FILE_NAME "${SCRIPT_API_FILE_NAME}")

    set(SCRIPT_API_BINARY_FILE "${CMAKE_CURRENT_BINARY_DIR}/${SCRIPT_API_FILE_NAME}.cpp")

    add_custom_command_timestamp(OUTPUT ${SCRIPT_API_BINARY_FILE}
            COMMAND ${CMAKE_COMMAND}
            -DSCRIPT=${CMAKE_CURRENT_SOURCE_DIR}/export.py
                    -DSCRIPT_API_SOURCE_FILE=${CMAKE_CURRENT_SOURCE_DIR}/export.cpp.in
                    -DSCRIPT_API_BINARY_FILE=${SCRIPT_API_BINARY_FILE}
                    -DSCRIPT_API_FILE=${SCRIPT_API_FILE}
                    -DSCRIPT_SOURCE_DIR=${CMAKE_CURRENT_SOURCE_DIR}
                    -P ${CMAKE_SOURCE_DIR}/cmake/scripts/PythonExport.cmake
            MAIN_DEPENDENCY ${SCRIPT_API_FILE}
            DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/export.cpp.in
                    ${CMAKE_CURRENT_SOURCE_DIR}/export.py
                    ${CMAKE_SOURCE_DIR}/cmake/scripts/PythonExport.cmake
            WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
            COMMENT "Generating python/${SCRIPT_API_FILE_NAME}.cpp"
    )
    set_property(SOURCE ${SCRIPT_API_BINARY_FILE} PROPERTY GENERATED ON)
    target_sources(openttd_lib PRIVATE ${SCRIPT_API_BINARY_FILE})
    list(APPEND SCRIPT_PYTHON_BINARY_FILES ${SCRIPT_API_BINARY_FILE})
endforeach()

add_custom_target_timestamp(script_python
        DEPENDS
        ${SCRIPT_PYTHON_BINARY_FILES}
)
add_dependencies(script_python
        script_window
)

set(INCLUDES_BINARY_FILE "${CMAKE_CURRENT_BINARY_DIR}/python_includes.cpp")
set_property(SOURCE ${INCLUDES_BINARY_FILE} PROPERTY GENERATED ON)
target_sources(openttd_lib PRIVATE ${INCLUDES_BINARY_FILE})
set(API_FILES "${CMAKE_CURRENT_BINARY_DIR}/python.files")
file(GENERATE OUTPUT ${API_FILES} CONTENT "${SCRIPT_PYTHON_BINARY_FILES}")
add_custom_command_timestamp(OUTPUT ${INCLUDES_BINARY_FILE}
        COMMAND ${CMAKE_COMMAND}
                -DINCLUDES_SOURCE_FILE=${CMAKE_CURRENT_SOURCE_DIR}/modules.cpp.in
                -DINCLUDES_BINARY_FILE=${INCLUDES_BINARY_FILE}
                -DAPI_FILES=${API_FILES}
                -P ${CMAKE_SOURCE_DIR}/cmake/scripts/PythonModules.cmake
        MAIN_DEPENDENCY ${CMAKE_CURRENT_SOURCE_DIR}/modules.cpp.in
        DEPENDS ${SCRIPT_PYTHON_BINARY_FILES}
                ${API_FILES}
                ${CMAKE_SOURCE_DIR}/cmake/scripts/PythonModules.cmake
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Generating ${INCLUDES_BINARY_FILE}"
)
add_custom_target_timestamp(script_python_includes
        DEPENDS
        ${INCLUDES_BINARY_FILE}
)
add_dependencies(script_python_includes
    script_python
)
add_dependencies(script_api
    script_python_includes
)

#target_include_directories(script_api
#        INTERFACE
#        ${CMAKE_CURRENT_BINARY_DIR}
#)

set(ENUM_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/export_enum.py)

foreach(ENUM
        "src/command_type.h;Commands/CMD_,CommandType/CMDT_,CommandPauseLevel/CMDPL_"
        "src/openttd.h;GameMode/GM_,SwitchMode/SM_,PauseMode/PM_PAUSED_/PM_"
        )
    list(GET ENUM 0 HEADER_FILE)
    list(GET ENUM 1 ENUM_NAMES)
    get_filename_component(ENUM_NAME "${HEADER_FILE}" NAME_WE)


    set(ENUM_SOURCE_FILE ${CMAKE_SOURCE_DIR}/${HEADER_FILE})
    set(ENUM_DEST_FILE ${CMAKE_CURRENT_BINARY_DIR}/enum_${ENUM_NAME}.cpp)
    add_custom_command(
        OUTPUT ${ENUM_DEST_FILE}
        COMMAND python3 ${ENUM_SCRIPT} ${ENUM_SOURCE_FILE} ${ENUM_DEST_FILE} ${ENUM_NAMES}
        MAIN_DEPENDENCY ${SCRIPT_API_SOURCE_FILE}
        DEPENDS ${ENUM_SOURCE_FILE}
            ${ENUM_SCRIPT}
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Generating ${ENUM_DEST_FILE}"
    )
    set_property(SOURCE ${ENUM_DEST_FILE} PROPERTY GENERATED ON)
    list(APPEND ENUM_BINARY_FILES ${ENUM_DEST_FILE})
    list(APPEND ENUM_COLLECT_NAMES ${ENUM_NAME})
endforeach()

add_custom_target_timestamp(script_python_enums
        DEPENDS
        ${ENUM_BINARY_FILES}
)

set(ENUM_COLLECT_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/collect_enum.py)
set(ENUM_BINARY_FILE ${CMAKE_CURRENT_BINARY_DIR}/export_enum.cpp)
add_custom_command(
  OUTPUT ${ENUM_BINARY_FILE}
  COMMAND python3 ${ENUM_COLLECT_SCRIPT} ${ENUM_BINARY_FILE} ${ENUM_COLLECT_NAMES}
  MAIN_DEPENDENCY ${ENUM_SOURCE_FILE}
  DEPENDS script_python_enums
    ${ENUM_COLLECT_SCRIPT}
  )

set_property(SOURCE ${ENUM_BINARY_FILE} PROPERTY GENERATED ON)
add_custom_target_timestamp(script_python_enum
    DEPENDS
    ${ENUM_BINARY_FILE}
)
add_dependencies(script_python
    script_python_enum
)
target_sources(openttd_lib PRIVATE ${ENUM_BINARY_FILE} ${ENUM_BINARY_FILES})
