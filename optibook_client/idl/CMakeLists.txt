
capnp_generate_cpp(optibookIdlSources optibookIdlHeaders info.capnp exec.capnp management.capnp common.capnp)
add_library(optibook_idl ${optibookIdlSources} info.capnp exec.capnp management.capnp common.capnp)
target_link_libraries(optibook_idl PUBLIC CapnProto::capnp-rpc)
target_include_directories(optibook_idl PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
