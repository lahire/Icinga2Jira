# Icinga2Jira
Script para generar issues de Jira por problemas reportados en IcingaWeb2

## Requerimientos
Python3
jira-python (pip install jira)
Servidor de Icingaweb2 con acceso API
Servidor de JIRA

## Objetivo
Automatiza el proceso de generación de tickets en Jira si se envía una notificación de IcingaWeb2. 

En el caso particular por lo que este script fue creado, el servidor de icingaweb2 sólo envia notificaciones por mail a los sysadmins si el servicio o host está marcado como crítico. Como la práctica es "Si es crítico, levantar ticket en jira y luego comentar el número de ticket en icingaweb2", se armó este script para automatizar este proceso.

## Cómo funciona
El script requiere que se le pasen parámetros.

### Case: Service
jirador.py SERVICIO TIPO_NOTI SERVICE_DESC HOST_ALIAS HOST_ADDRESS SERVICE_STATE SERVICE_OUTPUT

### Case: Host
jirador.py HOST TIPO_NOTI HOST_ALIAS HOST_ADDRESS HOST_STATE HOST_OUTPUT

Cada uno de estos son generados por el script "mail_host_notification" y "mail_service_notification" de ejemplo de icingaweb2.

Una vez que tenemos esos parámetros, el script se conecta a la instancia de Jira y revisa:
* Si existe un ticket creado por este problema
	* Si existe el ticket, no crea un ticket nuevo pero comenta en el mismo los datos que envía icingaweb2 (útil para hacer seguimiento)
	* Si no existe el ticket, lo crea en el project_key especificado en el archivo de configuración
* Si el host tiene VM_PARENT. Esta es una variable personalizada que tenemos en nuestro entorno de trabajo: indica el nombre del "parent vm" del host con problemas.
	* Si el host está virtualizado (o sea, tiene vm parent), se fija si existe un ticket por problemas en el host vm parent.
		* Si el parent vm no tiene ticket, crea un issue para el host que tiene problema
		* Si el parent vm tiene ticket, no genera un ticket nuevo para este host (esto es para evitar generar tickets excesivamente, ya que un ticket para el servidor de virutalización alcanza)
* Crea el ticket (si no estaba creado antes)
	* Como componente, coloca el servidor/servicio que tiene el problema
		* Si no existe el componente, lo crea.
* Envía un comentario a icingaweb2, enlazando al issue generado.

* Si se envía una notificación de RECOVERY (se levantó un servicio), cierra el ticket generado y comenta en el mismo el resultado

## config.cfg

El config.cfg es el archivo que tiene la configuración del script. Si algo de eso no está bien, el programa se rompe.

[JIRA]
La URL al server de Jira:
url = https://JIRAURL.atlassian.net/
El usuario que usará el script para login:
username = USERNAME
password = PASSWORD

El Project key del proyecto en el que se generan los tickets. Por ejemplo: El ticket "SIS-1112" tiene como project key: "SIS"
jira_key = PROJECT_KEY

El tipo de issue. Por ejemplo "Incidente"
jira_tipo_issue = TYPE_OF_ISSUE

El Status que tiene el ticket al ser generado. Por ejemplo "Esperando por la asistencia"
jira_status = STATUS_TYPE

La etiqueta con la que se tiene que generar el ticket, útil para filtros
label = icinga2

ID de Transición del workflow que permite cerrar el ticket 
transition = NUMBER OF TRANSITION

Tipo de resolución (por ejemplo: Done)
resolution = TYPE OF RESOLUTION


[ICINGA2]
Usuario y password para usar la api de icinga:
api_user = API_USER
api_password = AP_PASSWORD

URLS
url = URLOFICINGAWEB2/v1/objects/
url_com = URLOFICINGAWEB2/v1/actions/add-comment
*url_com es la url de la api que agrega el comentario. Si además de generar el comentario queremos hacer un ack, url_com sería (por ejemplo) "https://localhost:5665/v1/actions/acknowledge-problem"
		
Cómo soy medio nuevo dentro de esto que es programar, se que se puede hacer bocha de refactoring. Pero no hay mucho de esto (y nos da una mano grande en el laburo). Espero que te sirva a vos también.


