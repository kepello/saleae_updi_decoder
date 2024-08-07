cmake_minimum_required (VERSION 3.11)
project(ll_analyzer)

add_definitions( -DLOGIC2 )

set(CMAKE_OSX_DEPLOYMENT_TARGET "10.14" CACHE STRING "Minimum supported MacOS version" FORCE)

# enable generation of compile_commands.json, helpful for IDEs to locate include files.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# custom CMake Modules are located in the cmake directory.
set(CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake)

include(ExternalAnalyzerSDK)

set(SOURCES 
src/ll_analyzer.cpp
src/ll_analyzer.h
src/ll_results.cpp
src/ll_results.h
src/ll_settings.cpp
src/ll_settings.h
)

add_analyzer_plugin(ll_analyzer SOURCES ${SOURCES})
