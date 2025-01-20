add_files(
    call_py.hpp call_py.cpp
    msg.cpp
    msg_base.hpp msg_base.cpp
    msg_console.hpp msg_console.cpp
    queues.hpp queues.cpp
    setup.hpp setup.cpp
    task.hpp task.cpp
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

