import time
import json

from opcua import Server, ua
from aphyt import omron

import numpy as np
from urllib.parse import urlparse


#########################################################
# Read the configuration file
#########################################################

try:
    with open('config_server.json', 'r') as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"Error loading configuration file: {e}")
    exit(1)

plc_ip_address = config["plc_ip_address"]
server_endpoint = config["server_endpoint"]
namespace_uri = config["namespace_uri"]
json_config_path = config["json_config_path"]
label_object = config["label_Object"]
update_interval = config["update_interval"]
timeout = config["timeout"]
use_encryption = config["use_encryption"]
use_pass = config["use_pass"]
certificate_path = config["certificate_path"]
private_key_path = config["private_key_path"]
security_policy = config["security_policy"]
username = config["username"]
password = config["password"]

#========================================
# Subscription to events class
#========================================

class SubHandler(object):
    def datachange_notification(self, node, val, data):
        
        node_id_str = node.nodeid.to_string()
        
        if not init_server:
            return
        try:
            for nombre_tag, nodeid_str in nodeid_to_plctag.items():
                if nodeid_str == node_id_str:
                    # Make sure val is a dictionary and has the 'value' key
                    if isinstance(val, dict) and 'value' in val:
                        actual_value = val['value']  # Extract the actual value
                    else:
                        actual_value = val  # Handle the case where val is not a dictionary
                        
                    # Now use actual_value instead of val for comparison and writing
                    if (datos_plc.get(nombre_tag, None) != actual_value)and (keep_trying==False):  
                        write_to_plc(nombre_tag, actual_value)
                        return
                    elif (keep_trying==True):
                        
                        print("\nFailed to write to PLC\n")
                            
        except KeyError as e:
            print(f"Error: Tag {e} not found in the data dictionary.")
        except Exception as e:
            print(f"Unexpected error processing the data change notification: {e}")

#========================================
# Authentication management function
#========================================

def user_manager(isession, username, password):
    
    result = False
    
    if username == config["username"] and password == config["password"]:
        print("Correct authentication")
        result = True
    else:
        print("Incorrect authentication")
        result = False
    
    return result


#========================================
# PLC Reconection
#========================================
    
def reconnect_to_plc():
    
    global keep_trying
    
    while keep_trying:
         
        try:
            print("Attempting to reconnect...")
          
            eip_instance.close_explicit()
            eip_instance.connect_explicit(plc_ip_address)
            eip_instance.register_session()
            print("Reconnection successful.")
            keep_trying = False
            opc_data["COM_PLC_FAIL"].set_value(False)
            return
        except Exception as e:
            print(f"Reconnection failed: {e}. Retrying...")
            time.sleep(3)  # Wait a bit before retrying

    
#========================================
# Function to read data from OMRON PLC
#========================================

def read_plc_data():
    
    datos = {}
    global keep_trying
   
      
    print("\n- Reading data: \n")
        
    for tag in plc_tags:
            
        try:  
            value = eip_instance.read_variable(tag)

            format_value = format_tag_value(value)
            
            datos[tag] = format_value
            print(f"{tag}: {format_value}")
              
        except Exception as exc:
            
            if "WinError 10054" or "WinError 10060" in str(exc):  
                print("Connection lost. Attempting to reconnect...")
                
                keep_trying=True
                opc_data["COM_PLC_FAIL"].set_value(True)    
                reconnect_to_plc()
                
            else:
                print(f"Failed to read from PLC: {exc}")

    return datos

#==========================================
# Function to write data to OMRON PLC
#==========================================

def write_to_plc(tag_name, tag_value):
    
    try:
       
        # Write the value to the specified tag
        eip_instance.write_variable(tag_name, tag_value)
        print(f"\nValue {tag_value} successfully written to {tag_name}\n")

    except Exception as exc:
        print(f"\nFailed to write to PLC: {exc}\n")

#========================================================
# Function Converts a Python data type to an OPC UA data type
#========================================================
    
def convert_to_opc_type(py_type):
    
    if py_type == "int":
        return ua.VariantType.Int32
    elif py_type == "float":
        return ua.VariantType.Float
    elif py_type == "bool":
        return ua.VariantType.Boolean
    elif py_type == "str":
        return ua.VariantType.String
    
    # .. other conversions 
    else:
        raise ValueError(f"/nUnsupported data type: {py_type}") 
    
#===================================
# Data type formatting function
#===================================
    
def format_tag_value(tag_value):
    
    # Try converting to string if necessary
    if type(tag_value).__name__ == 'CIPString' or isinstance(tag_value, (str, bytes)):
        # Ensure the value is handled as a string
        format_value = str(tag_value)
    else:
        # For other data types, use the value as is
        format_value = tag_value
        
    return format_value

#=====================================================================================================================================================
#==================================================================================================================================================

# PLC Tags
##=======================================================================================================    

# Read the JSON file and deduce the data types and write permissions
with open(json_config_path, 'r') as file:
    plc_config = json.load(file)

# Initialize the dictionary to store the data types and write permissions for each tag
plc_tag_properties = {}

for tag, properties in plc_config.items():
    # properties is now a dictionary with "value" and "write"
    value = properties["value"]  # Access the value to determine its type
    is_writable = properties["write"]  # Access the write property
    plc_tag_properties[tag] = {
        "type": type(value).__name__,
        "write": is_writable
    }

#=========================================================================================================

# Rest of the code to configure and run the OPC UA server
try:
    server = Server()
    server.set_endpoint(server_endpoint)
    uri = namespace_uri
    idx = server.register_namespace(uri)

# Security Configuration (Encryption)

    # Security and encryption configuration
    if use_encryption:
        server.load_certificate(certificate_path)
        server.load_private_key(private_key_path)
        server.set_security_policy([ua.SecurityPolicyType[security_policy]])
        server.set_security_IDs(["Username"])
    
    # Credentials and authentication configuration
    if use_pass:
        
        result = server.user_manager.set_user_manager(user_manager)
        print("Successful authentication", result)
    
    objects = server.get_objects_node()
    myobject = objects.add_object(idx, label_object)

    opc_data = {}
    plc_tags = []
    
    nodeid_to_plctag = {}  # Temporary dictionary containing the NodeIds of the tags
    init_server = False  # Flag for data initialization

    # Create and configure OPC UA variables
    for tag, properties in plc_tag_properties.items():
        
        value = plc_config[tag]["value"]
        is_writable = properties["write"]
    
        opc_data_type = convert_to_opc_type(properties["type"])
        variable = myobject.add_variable(idx, tag, plc_config[tag], opc_data_type)
        variable.set_writable(is_writable)
        plc_tags.append(tag)
        opc_data[tag] = variable
        
        nodeid_to_plctag[tag] = variable.nodeid.to_string()

    # Tag to COM with PLC
    
    variable = myobject.add_variable(idx, "COM_PLC_FAIL",False)
    opc_data["COM_PLC_FAIL"] = variable
    
    # ================================================================================
    
    # 1-Create instance for communication with Omron controller
    eip_instance = omron.n_series.NSeries()
    keep_trying=False

    # 2-Connect to Omron controller using its IP address
    eip_instance.connect_explicit(plc_ip_address)

    # 3-Register the session
    eip_instance.register_session()
    
    # 4-Start Server
    server.start()
    print("OPC UA Server started successfully.")
    
    
    # =================================================================================
    
    ## Event subscription handling when the value of variables changes
    
    handler = SubHandler()  
    subscription = server.create_subscription(1000, handler)
    
    for variable in opc_data.values():
        
        subscription.subscribe_data_change(variable)

    ## PLC Data reading loop
    
    while True:
        
        datos_plc = read_plc_data()
    
        for tag, tag_value in datos_plc.items():
            if tag in opc_data:
                opc_data[tag].set_value(tag_value)
                        
        time.sleep(update_interval)
        init_server = True
      
except KeyboardInterrupt:
    print("Interruption by user, closing server...")
except Exception as e:
    print(f"Error during server execution: {e}")
finally:
    server.stop()
    print("Server stopped.")
