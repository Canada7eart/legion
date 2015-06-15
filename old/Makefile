CXXFLAGS = -std=c++14 
CXXLDFLAGS = -stdlib=libc++
BOOST_INCLUDE = -I/usr/local/Cellar/boost/1.57.0/include 
INCLUDES = -I./rapidjson/include/ $(BOOST_INCLUDE)
#BOOST_LIB = -L/usr/local/Cellar/boost/1.57.0/lib/ 
LIBS = $(BOOST_LIB)
#only osx
BOOST_DYLIBS = -lboost_program_options -lboost_system 

all: task
task: task.o
	$(CXX) $(CXXFLAGS) $(CXXLDFLAGS) $(BOOST_DYLIBS) $(LIBS) task.o -o task

task.o: task.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) task.cpp -c -o task.o

clean:
	rm ./*.o 2>/dev/null
	rm ./task 2>/dev/null