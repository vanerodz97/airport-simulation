project(AirportSimulator)

cmake_minimum_required (VERSION 2.6)

set(CMAKE_CXX_STANDARD 11)
SET(CMAKE_CXX_COMPILER "/usr/bin/g++")

SET (CMAKE_LINKER  "/usr/bin/ld")

SET(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -g -Wall")


file(GLOB SOURCES "*src/*.cpp")



# Find Boost
find_package( Boost REQUIRED COMPONENTS program_options)
include_directories( ${Boost_INCLUDE_DIRS} )

find_package(  yaml-cpp REQUIRED )
include_directories( ${YAML_CPP_INCLUDE_DIR} )


add_executable(airport ${SOURCES})
target_link_libraries(airport ${Boost_LIBRARIES} ${YAML_CPP_LIBRARIES})
