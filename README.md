
# Servidor OPC UA para PLC Omron

Este proyecto implementa un servidor OPC UA que facilita la comunicación con un PLC Omron, permitiendo la lectura y escritura de variables a través de la red. Está diseñado para proporcionar una interfaz estandarizada para interactuar con el PLC en aplicaciones de automatización e IoT.

## Características

- Lectura de datos en tiempo real desde el PLC Omron.
- Escritura de datos hacia el PLC para control y automatización.
- Configuración flexible a través de un archivo JSON.
- Soporte para autenticación de usuarios y cifrado opcional.
- Fácil integración con otros sistemas OPC UA.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado Python 3.6 o superior y pip. Este proyecto ha sido probado en un entorno Windows, pero debería ser compatible con otros sistemas operativos que soporten Python.

## Instalación

1. Clona este repositorio en tu máquina local:

```bash
git clone https://github.com/Javimatic/PLC_OPCUA_Server.git
cd PLC_OPCUA_Server
2. Instala las dependencias necesarias:
bash
3. Copy code
pip install -r requirements.txt

4. Configuración
Edita el archivo config_server.json para ajustar la configuración del servidor, incluyendo la dirección IP del PLC, credenciales de usuario, y preferencias de seguridad.

Configura las variables OPC UA y sus permisos de lectura/escritura en el archivo plc_tags.json.

5. Ejecución
Para iniciar el servidor OPC UA, ejecuta:

bash
Copy code
python servidor_opcua.py
El servidor se iniciará y se conectará al PLC especificado, quedando listo para recibir solicitudes de clientes OPC UA.

### Contribuir
###########################################################################################################################
Las contribuciones son bienvenidas. Si tienes una sugerencia para mejorar este proyecto, por favor:

Bifurca el repositorio.
Crea una rama para tu característica (git checkout -b feature/AmazingFeature).
Haz commit de tus cambios (git commit -m 'Add some AmazingFeature').
Push a la rama (git push origin feature/AmazingFeature).
Abre un Pull Request.
Licencia
Este proyecto está distribuido bajo la Licencia MIT. Consulta el archivo LICENSE para obtener más información.

Contacto
Javier Falque - javierfalque85@gmail.com

Link del proyecto: https://github.com/Javimatic/PLC_OPCUA_Server
