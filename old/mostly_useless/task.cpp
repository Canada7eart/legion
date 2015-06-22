#define PORT 6000

#include <boost/asio.hpp>
#include <string>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <cassert>
#include <memory>
#include <functional>

#include <boost/asio.hpp>
#include <boost/program_options.hpp>
#include <rapidjson/document.h>

namespace po = boost::program_options;
using namespace std;
using boost::asio::ip::tcp;

// checks if b is in a.
template <class T0, class T1>
bool in(T0 b, T1 a) {
    return a.find(b) != a.end();
}

void serverAcceptedFunc(const boost::system::error_code& ec) {
    cout<<"serverFunc\n";
    if (ec) {
        cout<<"serverFunc::error\n";
    }
}

void serverConnectedFunc(const boost::system::error_code& ec,
    boost::asio::ip::tcp::resolver::iterator iterator, tcp::socket& socket) {
    cout<<"clientFunc\n";
    if (!ec) {
        cout<<"clientFunc::error\n";
    }
}



int main(int argc, char** argv) {
    po::options_description desc("Allowed options");
    desc.add_options()
        ("help", "produce help message")
        ("server", "start process as server")
        ("json_path", po::value<string>(), "path to a description of the tensors to be kept")
        ("nodes", po::value<string>(), "initial list of neighbors")
        ("json", po::value<string>(), "initial list of neighbors")
        ;

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    cout<<"Arguments:\n";
    if (vm.size() == 0) {
        cout<<"No arguments.\n";
    }
    for (const auto& item : vm) {    
        cout<<"\t--"<<item.first<<"="<<item.second.as<string>()<<"\n";
    }

    if (in(string("help"), vm)) {
        cout << "This is the help!\n";
        return 0;
    }

    string jsonText;
    if (!in(string("json_path"), vm) && !in(string("json"), vm)) {
        cout << "No json_path argument: we are aborting, we need a description of what we are saving.\n";
        abort();
    } 
    else if (in(string("json_path"), vm)) {
        ifstream file(vm["json_path"].as<string>());
        if (file.fail()) {
            cout << "Failed to load file\n";
            abort();
        }
        else {
            cout<<"\nJson file:\n";
            
            string line;
            getline(file, line);
            jsonText += string("") + "\t" + line + "\n";

            while(!file.eof()) {
                getline(file, line);
                jsonText += string("") + "\t" + line + "\n";
            };
            
            cout<<jsonText<<"\n";
        }
    }
    else if (in(string("json"), vm)) {
        jsonText = vm["json"].as<string>();
        jsonText.erase(0, 1);
        jsonText.erase(jsonText.size() - 1, 1);
    }    

    rapidjson::Document d;
    cout<<"jsonText : "<<jsonText<<"\n";
    d.Parse<0>(jsonText.c_str());
    cout<<"Parsed json file:\n";
    cout<<"\tip-list:\n";
    assert(!d["ip-list"].IsNull());
    for(rapidjson::SizeType i = 0; i < d["ip-list"].Size(); ++i) {
        cout<<"\t\t"<<d["ip-list"][i].GetString()<<"\n";
    }

    if (in(string("server"), vm)) {
        
        boost::asio::io_service io_service;
        tcp::acceptor acceptor(io_service, tcp::endpoint(tcp::v4(), PORT));
        tcp::socket socket(io_service);
        acceptor.async_accept(socket, &serverAcceptedFunc);
        cout<<"Starting to accept connections!\n";
        tcp::resolver resolver(io_service);

        vector<tcp::socket> sockets;
        vector<tcp::resolver::iterator> endpoint_iterators;
        for(rapidjson::SizeType i = 0; i < d["ip-list"].Size(); ++i) {
            sockets.emplace_back(io_service);
            endpoint_iterators.push_back(resolver.resolve({d["ip-list"][i].GetString(), to_string(PORT)}));
            async_connect(
                sockets[sockets.size() - 1], 
                endpoint_iterators[sockets.size() - 1], 
                    [&](const boost::system::error_code& ec,
                    boost::asio::ip::tcp::resolver::iterator iterator){
                        serverConnectedFunc(ec, endpoint_iterators[endpoint_iterators.size() - 1], sockets[sockets.size() - 1]);
                    }
                );
        }
         
        io_service.run();
    }
    else {
        cout<<"Not server!\n";

        boost::asio::io_service io_service;
        tcp::resolver resolver(io_service);

        vector<tcp::socket> sockets;
        vector<tcp::resolver::iterator> endpoint_iterators;
        for(rapidjson::SizeType i = 0; i < d["ip-list"].Size(); ++i) {
            sockets.emplace_back(io_service);
            endpoint_iterators.push_back(resolver.resolve({d["ip-list"][i].GetString(), to_string(PORT)}));
            async_connect(
                sockets[sockets.size() - 1], 
                endpoint_iterators[sockets.size() - 1], 
                    [&](const boost::system::error_code& ec,
                    boost::asio::ip::tcp::resolver::iterator iterator){
                        serverConnectedFunc(ec, endpoint_iterators[endpoint_iterators.size() - 1], sockets[sockets.size() - 1]);
                    }
                );
        }
         
        io_service.run();

        
    }
    // Start a listening thread for the different sync tasks

    // Start a thread with the training job


    return 0;
}