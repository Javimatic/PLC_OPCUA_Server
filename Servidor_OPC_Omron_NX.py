import time
import json
from opcua import Server, ua
from aphyt import omron

import numpy as np
from urllib.parse import urlparse


# Leer el archivo de configuración
#####################################################
try:
    with open('config_server.json', 'r') as config_file:
        config = json.load(config_file)
except Exception as e:
    print(f"Error al cargar el archivo de configuración: {e}")
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
private_key_path =config["private_key_path"]
security_policy = config["security_policy"]
username = config["username"]
password = config["password"]



#========================================
# Clase Suscripción a eventos
#========================================

class SubHandler(object):
    def datachange_notification(self, node, val, data):
        node_id_str = node.nodeid.to_string()
        
        
        if inicializacion_server == False:
            return
        try:
            for nombre_tag, nodeid_str in nodeid_to_plctag.items():
                if nodeid_str == node_id_str:
                    # Asegúrate de que val sea un diccionario y tenga la clave 'value'
                    if isinstance(val, dict) and 'value' in val:
                        actual_value = val['value']  # Extrae el valor real
                    else:
                        actual_value = val  # Maneja el caso donde val no es un diccionario
                        
                    # Ahora usa actual_value en lugar de val para la comparación y escritura
                    if datos_plc.get(nombre_tag, None) != actual_value:  
                        write_to_plc(nombre_tag, actual_value)
                        return
                            
        except KeyError as e:
            print(f"Error: No se encontró el tag {e} en el diccionario de datos.")
        except Exception as e:
            print(f"Error inesperado al procesar la notificación de cambio de datos: {e}")
              
    
#========================================
# Función de gestión de autenticación
#========================================

def user_manager(isession, username, password):
    
    result=False
    
    if username == config["username"] and password == config["password"]:
        print("Autenticación correcta")
        result=True
    else:
        print("Autenticación incorrecta")
        result=False
    
    return result


#========================================
# Función para leer datos del PLC OMRON
#========================================

def leer_datos_plc():
    
    datos = {}
   
    try:
        
        print("\n- Lectura de datos: \n")
        
        for tag in plc_tags:
            value = eip_instance.read_variable(tag)

            valor_formateado=format_tag_value(value)
            
            datos[tag] = valor_formateado
            print(f"{tag}: {valor_formateado}")
             
    except Exception as exc:
        print(f"Fallo al leer del PLC: {exc}")

    
    return datos

    
#==========================================
# Función para escribir datos al PLC OMRON
#==========================================

def write_to_plc(tag_name, tag_value):
    
    try:
       
        # Escribe el valor en el tag especificado
        eip_instance.write_variable(tag_name, tag_value)
        print(f"\nValor {tag_value} escrito exitosamente en {tag_name}\n")

    except Exception as exc:
        print(f"\nFallo al escribir en el PLC: {exc}\n")


    
#=================================================================
# Función Convierte un tipo de dato Python a un tipo de dato OPC UA
#==================================================================
    
def convert_to_opc_type(py_type):
    
    if py_type == "int":
        return ua.VariantType.Int32
    elif py_type == "float":
        return ua.VariantType.Float
    elif py_type == "bool":
        return ua.VariantType.Boolean
    elif py_type == "str":
        return ua.VariantType.String
    # Puedes agregar más conversiones según sea necesario
    else:
        raise ValueError(f"/nTipo de dato no soportado: {py_type}") 
    
#===================================
# Función formatos tipo de dato
#===================================
    
def format_tag_value( tag_value):
    
    # Intentar convertir a string si es necesario
    if type(tag_value).__name__ == 'CIPString' or isinstance(tag_value, (str, bytes)):
        # Asegurar que el valor se maneje como una cadena
        valor_formateado = str(tag_value)
    else:
        # Para otros tipos de datos, usar el valor tal cual
        valor_formateado = tag_value
        
    return valor_formateado
   
#=====================================================================================================================================================
#==================================================================================================================================================
    
    
    
#Tags PLC 
##=======================================================================================================    

# Leer el archivo JSON y deducir los tipos de datos y permisos de escritura
with open(json_config_path, 'r') as file:
    plc_config = json.load(file)

# Inicializar el diccionario para almacenar los tipos de datos y los permisos de escritura de cada tag
plc_tag_properties = {}

for tag, properties in plc_config.items():
    # properties ahora es un diccionario con "value" y "write"
    value = properties["value"]  # Acceder al valor para determinar su tipo
    is_writable = properties["write"]  # Acceder a la propiedad de escritura
    plc_tag_properties[tag] = {
        "type": type(value).__name__,
        "write": is_writable
    }


#=========================================================================================================

# Resto del código para configurar y ejecutar el servidor OPC UA
try:
    server = Server()
    server.set_endpoint(server_endpoint)
    uri = namespace_uri
    idx = server.register_namespace(uri)
    

    
# Configuracion de Seguridad (Encriptacion)

    # Configuración de seguridad y cifrado
    if use_encryption:
        server.load_certificate(certificate_path)
        server.load_private_key(private_key_path)
        server.set_security_policy([ua.SecurityPolicyType[security_policy]])
        server.set_security_IDs(["Username"])
    
    
    # Configuración de credenciales y autenticación
    if use_pass:
        
        result=server.user_manager.set_user_manager(user_manager)
        print("Autenticación exitosa",result)
        

    
    objects = server.get_objects_node()
    myobject = objects.add_object(idx, label_object)

    variables_opc={}
    plc_tags =[]
    
    nodeid_to_plctag={}  # Diccionario temporal que contiene los NodeId de los tags
    inicializacion_server = False # Bandera para la inicializacion de datos
    

    # Crear y configurar variables OPC UA
    for tag, properties in plc_tag_properties.items():
        
        value = plc_config[tag]["value"]
        is_writable = properties["write"]
    
        opc_data_type = convert_to_opc_type(properties["type"])
        variable = myobject.add_variable(idx, tag, plc_config[tag], opc_data_type)
        variable.set_writable(is_writable)
        plc_tags.append(tag)
        variables_opc[tag] = variable
        
        nodeid_to_plctag[tag] = variable.nodeid.to_string()

    # Iniciar Servidor
    
    
    # Crear instancia para la comunicación con el controlador Omron
    eip_instance = omron.n_series.NSeries()

    # Conectar al controlador Omron utilizando su dirección IP
    eip_instance.connect_explicit(plc_ip_address)

    # Registrar la sesión
    eip_instance.register_session()
    
    
    server.start()
    print("Servidor OPC UA iniciado con éxito.")
    
    
    
    ## Manejo de suscripcion a eventos cuando se cambia el valor de las variables
    
    handler = SubHandler()  
    subscription = server.create_subscription(1000, handler)
    
    for variable in variables_opc.values():
        
        subscription.subscribe_data_change(variable)


    ## Bucle de lectura de Variables PLC
    
    while True:
           
        datos_plc = leer_datos_plc()
    
        for tag, valor in datos_plc.items():
            if tag in variables_opc:
                variables_opc[tag].set_value(valor)
                        
        time.sleep(update_interval)
        inicializacion_server = True
       
      
except KeyboardInterrupt:
    print("Interrupción por el usuario, cerrando el servidor...")
except Exception as e:
    print(f"Error durante la ejecución del servidor: {e}")
finally:
    server.stop()
    print("Servidor detenido.")