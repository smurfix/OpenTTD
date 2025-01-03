add_files(
    call_py.hpp call_py.cpp
    msg_base.hpp msg_base.cpp
    queues.hpp queues.cpp
    setup.hpp setup.cpp
    task.hpp task.cpp
    )

nanobind_build_library(nanobind-static)

target_include_directories(${OPENTTD_LIB} PUBLIC
    ${Python_INCLUDE_DIRS}
    ${NB_DIR}/include)

target_link_libraries(openttd
     nanobind-static ${Python_LIBRARIES})

if(TARGET openttd_test)
    target_link_libraries(openttd_test PRIVATE
        nanobind-static ${Python_LIBRARIES})
endif()

nanobind_compile_options(${OPENTTD_LIB})

nanobind_link_options(openttd)
nanobind_link_options(openttd_test)

