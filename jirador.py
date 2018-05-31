#!/usr/bin/python3

# jirador.py : herramienta para levantar tickets de jira cuando
# falle un servidor en icinga2
# uso:
# jirador.py HOST_O_SERVICIO TIPO_NOTIFICACION [SERVICE_DESC] HOST_ALIAS \
#  HOST_ADDRESS HOST_STATE/SERVICE_STATE HOST_OUTPUT/SERVICE_OUTPUT
# Dependiendo si pasamos como primer par HOST o SERVICIO, procesa los proximos parámetros acorde

#import argparse
import subprocess
import shlex
import jira
import configparser
import os
import sys
import json


VERSION = '1.0.1'
CONFIG = '/opt/icinga2-jira/config.cfg'
VARS_VMPARENT = 'vm_parent'

def check_dependencias(alias):
    """
        check_dependencias(alias):
            Reviso dependencias
            placeholder. Determinar cuáles son (DNS/et. al.)

    """
    # dependencias = GET_DEPENDENCIAS_DE(alias)
    # for dependencia in dependencias:
    #   out = TEST_DEPENDENCIAS(dependencia)
    #   estatus[dependencia] = out
    #
    #   por cada key de estatus == False, una dependencia fallida
    #   determinar severidad y que hacer
    #
    #
    #
    #
    #
    pass
    return True



def jira_host(call,parametros):

    def jira_open(parametros):
        """
            jira_open(parametros):
                Permite abrir un ticket en jira
                los parámetros los agrego al dict 'issue_dict'        
        """
        issue_dict = {
            'project': {'key': config['JIRA']['jira_key']},
            'summary' : 'ICINGA2 | {0} - {1} is {2}'.format(parametros['tipo_notificacion'],
                                                parametros['host_alias'],
                                                parametros['host_state']),
            'description' : 'Notification Type: {0}\nHost Alias:\
         {1}\nHost Address: {2}\nHost State: {3}\nHost Output: {4}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          .format(
                                                parametros['tipo_notificacion'],
                                                parametros['host_alias'],
                                                parametros['host_address'],
                                                parametros['host_state'],
                                                parametros['host_output']
                                                ),
            'labels' : [config['JIRA']['label'],'icinga2'],
            'components' : [{'name': '{0}'.format(parametros['host_alias'])}],
            'issuetype' : {'name': config['JIRA']['jira_tipo_issue']},
        }
        #print(issue_dict)
        nuevo_issue = instance.create_issue(fields=issue_dict)
        #print(nuevo_issue)
        # Mando ack a jira
        #curl -k -s -u icingaweb2:Wijsn8Z9eRs5E25d -H 'Accept: application/json'
        #  -X POST 'https://localhost:5665/v1/actions/acknowledge-problem'
        # -d '{"type": "Host", "host": "host_down", "author": "admin", "comment": "comentario", "notify": true }'
        jason = """{0} "type": "Host", "host": "{1}", "author": "jirador", "comment": "<a href='https://exodev.atlassian.net/browse/{2}' target='_blank'>{2}</a>", "notify": true {3}""".format(
            chr(123), parametros['host_alias'], nuevo_issue, chr(125))
        o = str(subprocess.check_output(
                """curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}' -d '{3}'""".format(
                    config['ICINGA2']['api_user'],
                    config['ICINGA2']['api_password'],
                    config['ICINGA2']['url_com'],
                    jason), shell=True))
        #print(o)
        return True

    def jira_close(parametros):
        """
            jira_close(parametros)
                Busco el ticket con jira_check y lo cierro
                Agrego comentario en el ticket mostrando el último estado
        """
        alias = parametros['host_alias']
        ticket = jira_check(alias)
        #print('Cerrando {0}'.format(ticket[1]))
        parametros['ticket'] = ticket[1]
        jira_comment(parametros)
        instance.transition_issue(ticket[1],
        config['JIRA']['transition'],
        resolution={'name' : config['JIRA']['resolution']}
        )
        return True

    def jira_comment(parametros):
        """
            jira_comment(parametros)
                Agrega comentario con resultado al ticket existente

        """
        issue = parametros['ticket']
        instance.add_comment(issue,'Notification Type: {0}\nHost Alias:\
         {1}\nHost Address: {2}\nHost State: {3}\nHost Output: {4}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          .format(
             parametros['tipo_notificacion'],
             parametros['host_alias'],
             parametros['host_address'],
             parametros['host_state'],
             parametros['host_output']
         ))
        return True

    def jira_check(alias):
        """
            jira_check(alias):
                Revisa si el alias no cuenta con ticket
                (el alias está como tag), a futuro sería COMPONENTE
        """
        QUERY = 'project={0} AND issuetype={1} AND status="{2}" AND labels="{3}" AND labels="icinga2" AND component ="{4}"'.format(
            config['JIRA']['jira_key'],
            config['JIRA']['jira_tipo_issue'],
            config['JIRA']['jira_status'],
            config['JIRA']['label'],
            alias
        )
        result = instance.search_issues(QUERY)
        if len(result) == 0:
            # NO TICKET
            return [False,'']
        else:
            # EXISTE TICKET, INDICO CUAL
            return [True,result[0].key]

    try:
        #print('Conectando a jira...')
        instance = jira.JIRA(config['JIRA']['url'], basic_auth=(
            config['JIRA']['username'],
            config['JIRA']['password']))
    except:
        #print('Error al conectar con JIRA')
        exit(1)

    if call == 'CHECK':
        #print('Check')
        try:
            instance.create_component(parametros['host_alias'], config['JIRA']['jira_key'])
        except:
            pass
        try:
            salida = jira_check(parametros['host_alias'])
            #print(salida)
            return(salida)
        except:
            #print('Creo componente')
            instance.create_component(config['JIRA']['jira_key'], parametros['host_alias'])
            jira_host(call,parametros)

    elif call == 'OPEN':
        jira_open(parametros)
    elif call == 'COMMENT':
        return(jira_comment(parametros))
    elif call == 'CLOSE':
        return(jira_close(parametros))



def check_host(parametros):
    if parametros['host_state'] == 'DOWN':
        # HOST IS DOWN
        # CHECK SI SE LEVANTÓ TICKET
        # SI LEVANTÓ TICKET -> COMENTAR ESTADO
        # SI NO LEVANTO TICKET -> CHECKEAR SI TIENE VARIABLE VMPARENT
        #                                          -> SI TIENE VMPARENT, REVISO EL ESTADO DEL VMPARENT
        #                                               -> SI VMPARENT TIENE STATE 0 (OK), LEVANTO TICKET
        #                                               -> ELSE, IGNORA
        #                                          -> SI NO TIENE, CREAR TICKET
        #
        # CHECK SI EXISTE TICKET
        #print('Check si existe ticket')
        salida = jira_host('CHECK',parametros)
        if salida[0] == False: # No existe ticket para el elemento
            # CHECK SI TIENE VMPARENT
            o = str(subprocess.check_output(
                shlex.split(
                    "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".format(
                        config['ICINGA2']['api_user'],
                        config['ICINGA2']['api_password'],
                        config['ICINGA2']['url'],
                        parametros['host_alias'].lower()))))
            o = o[2:-1]
            salida = json.loads(o)
            #print(salida)
            #print(parametros['host_alias'])
            #input()
            salida = salida['results'][0]
            if VARS_VMPARENT in salida['attrs']['vars'].keys(): # Check si existe la variable custom vm parent
                VMPARENT = True
                #print('Tiene VMParent, reviso si el parent está OK')
                o = str(
                    subprocess.check_output(
                        shlex.split(
                            "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".
                            format(config['ICINGA2']['api_user'],
                                   config['ICINGA2']['api_password'],
                                   config['ICINGA2']['url'],
                                   salida['attrs']['vars'][VARS_VMPARENT]))))
                o = o[2:-1]
                salida_vmparent = json.loads(o)
                salida_vmparent = salida_vmparent['results'][0]
                if salida_vmparent['attrs']['state'] == 0.0: #el VMPARENT está OK, levanto ticket por host_alias
                    #print('Parent OK, levantando ticket')
                    jira_host('OPEN', parametros)
                    return True
                else: #el VMPARENT no está OK, ignoro la solicitud ya que eventualmente levanto ticket por host_alias
                    #print('Parent DOWN, no levanto ticket para este host')
                    pass

            else:
                VMPARENT = False
                #print('No tiene VMParent')
            if VMPARENT:
                # IGNORO TICKET DE MINION, CREO SOLO TICKET DE MASTER
                pass
                return True
            else:
                # ABRO TICKET
                jira_host('OPEN',parametros)
                return True
        else:
            # Existe, mando comentario sobre ticket
            #print('Ticket existe')
            parametros['ticket'] = salida[1] # agregro ticket a los parametros
            jira_host('COMMENT',parametros)
            return True
    elif parametros['host_state'] == 'UP':
        # HOST IS UP
        # CIERRO TICKET
        jira_host('CLOSE',parametros)
        return True

####### SERVICE
def jira_service(call, parametros):
    def jira_open(parametros):
        """
            jira_open(parametros):
                Permite abrir un ticket en jira
                los parámetros los agrego al dict 'issue_dict'        
        """
        issue_dict = {
            'project': {
                'key': config['JIRA']['jira_key']
            },
            'summary':
            'ICINGA2 | {0} - {1} - {2} is {3}'.format(parametros['tipo_notificacion'],
                                      parametros['host_alias'],
                                      parametros['service_desc'],
                                      parametros['service_state']),
            'description':
            'Notification Type: {0}\nService Description: {1}\nHost Alias:\
         {2}\nHost Address: {3}\nService State: {4}\nService Output: {5}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               .format(
                parametros['tipo_notificacion'],
                parametros['service_desc'],
                parametros['host_alias'],
                parametros['host_address'],
                parametros['service_state'],
                parametros['service_output']),
            'labels': [config['JIRA']['label'],'icinga2'],
            'components': [{
                'name': '{0}'.format(parametros['host_alias'])
            }],
            'issuetype': {
                'name': config['JIRA']['jira_tipo_issue']
            },
        }
        #print(issue_dict)
        nuevo_issue = instance.create_issue(fields=issue_dict)
        #print(nuevo_issue)
        # Mando ack a jira
        #curl -k -s -u icingaweb2:Wijsn8Z9eRs5E25d -H 'Accept: application/json'
        #  -X POST 'https://localhost:5665/v1/actions/acknowledge-problem'
        # -d '{"type": "Host", "host": "host_down", "author": "admin", "comment": "comentario", "notify": true }'
        jason = """{0} "type": "Service", "service": "{1}!{2}", "author": "jirador", "comment":  "<a href='https://exodev.atlassian.net/browse/{3}' target='_blank' >{3}</a>", "notify": true {4}""".format(
            chr(123), parametros['host_alias'], parametros['service_desc'],
            nuevo_issue, chr(125))
        o = str(
            subprocess.check_output(
                """curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}' -d '{3}'""".
                format(config['ICINGA2']['api_user'],
                       config['ICINGA2']['api_password'],
                       config['ICINGA2']['url_com'], jason),
                shell=True))
        #print(o)
        return True

    def jira_close(parametros):
        """
            jira_close(parametros)
                Busco el ticket con jira_check y lo cierro
                Agrego comentario en el ticket mostrando el último estado
        """
        alias = parametros['host_alias']
        ticket = jira_check(alias)
        #print('Cerrando {0}'.format(ticket[1]))
        parametros['ticket'] = ticket[1]
        jira_comment(parametros)
        instance.transition_issue(
            ticket[1],
            config['JIRA']['transition'],
            resolution={
                'name': config['JIRA']['resolution']
            })
        return True

    def jira_comment(parametros):
        """
            jira_comment(parametros)
                Agrega comentario con resultado al ticket existente

        """
        issue = parametros['ticket']
        instance.add_comment(issue, 'Notification Type: {0}\nService Description: {1} Host Alias:\
         {2}\nHost Address: {3}\nService State: {4}\nService Output: {5}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               .format(
            parametros['tipo_notificacion'],
            parametros['service_desc'],
            parametros['host_alias'],
            parametros['host_address'],
            parametros['service_state'],
            parametros['service_output']))
        return True

    def jira_check(alias):
        """
            jira_check(alias):
                Revisa si el alias no cuenta con ticket
                (el alias está como tag), a futuro sería COMPONENTE
                devuelve [TIENE_TICKET, '' o TICKET]
                Tiene Ticket = boolean
                Ticket o '' = string
        """
        QUERY = 'project={0} AND issuetype={1} AND status="{2}" AND labels="{3}" AND component ="{4}"'.format(
            config['JIRA']['jira_key'],
            config['JIRA']['jira_tipo_issue'],
            config['JIRA']['jira_status'],
            config['JIRA']['label'], parametros['host_alias'])
        #print(QUERY)
        result = instance.search_issues(QUERY)
        if len(result) == 0:
            # NO TICKET
            return [False, '']
        else:
            # EXISTE TICKET, INDICO CUAL
            return [True, result[0].key]

    try:
        #print('Conectando a jira...')
        instance = jira.JIRA(
            config['JIRA']['url'],
            basic_auth=(config['JIRA']['username'],
                        config['JIRA']['password']))
    except:
        #print('Error al conectar con JIRA')
        exit(1)

    if call == 'CHECK':
        #print('CHECK')
        try:
            instance.create_component(parametros['host_alias'], config['JIRA']['jira_key'])
        except:
            pass
        try:
            salida = jira_check(parametros['service_desc'])
            #print(salida)
            return (salida)
        except:
            #print('Creo componente {1} para {0}'.format(config['JIRA']['jira_key'], parametros['service_desc']))
            jira_service(call, parametros)
    elif call == 'OPEN':
        jira_open(parametros)
    elif call == 'COMMENT':
        return (jira_comment(parametros))
    elif call == 'CLOSE':
        return (jira_close(parametros))

def check_service(parametros):
    if parametros['service_state'] == 'CRITICAL' or parametros['service_state'] == 'WARNING' or parametros['service_state'] == 'UNKNOWN' :
        # SERVICE IS CRITICAL / WARNING OR UNKNOWN
        # CHECK SI SE LEVANTÓ TICKET
        # SI LEVANTÓ TICKET -> COMENTAR ESTADO
        # SI NO LEVANTO TICKET -> CHECKEAR SI EL HOST_ALIAS TIENE TICKET POR ESTO
        #                                          -> Si lo tiene, ignorar
        #                                          -> Si no lo tiene, levantar ticket
        #
        #
        #
        # CHECK SI EXISTE TICKET
        #print('Check si existe ticket')
        salida = jira_service('CHECK', parametros)
        if salida[0] == False: #no tiene ticket
            ## REVISO EL ESTADO DE HOST_ALIAS
            o = str(
                subprocess.check_output(
                    shlex.split(
                        "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".
                        format(config['ICINGA2']['api_user'],
                               config['ICINGA2']['api_password'],
                               config['ICINGA2']['url'],
                               parametros['host_alias']))))
            o = o[2:-1]
            salida_hostalias = json.loads(o)
            salida_hostalias = salida_hostalias['results'][0]
            if salida_hostalias['attrs']['state'] == 0.0: #HOST_ALIAS OK, levanto ticket por servicio
                #print('Parent OK, levanto ticket por servicio')
                jira_service('OPEN',parametros)
                return True
            else: #HOST_ALIAS NOT OK, ignoro
                #print('Parent sin estado OK, ignoro')
                pass
        ###
        else: #tiene ticket, comento
            #print('Ticket existe')
            parametros['ticket'] = salida[1] # agregro ticket a los parametros
            jira_service('COMMENT',parametros)
            return True
    else:  #Service is OK /
        jira_service('CLOSE', parametros)
        return True



def main(tipo):
    try:
        if tipo == 'SERVICIO':
            #jirador.py SERVICIO TIPO_NOTI SERVICE_DESC HOST_ALIAS HOST_ADDRESS SERVICE_STATE SERVICE_OUTPUT
            #len(argvs) = 8
            if len(sys.argv) != 8:
                #print('Cantidad de parámetros incorrecta')
                exit(1)
            parametros = {
                'tipo_notificacion': sys.argv[2].lower(),
                'service_desc'     : sys.argv[3],
                'host_alias'       : sys.argv[4],
                'host_address'     : sys.argv[5].upper(),
                'service_state'    : sys.argv[6].upper(),
                'service_output'   : sys.argv[7].upper()
                }
            salida = check_service(parametros)
            exit(salida)
        elif tipo == 'HOST':
            #jirador.py HOST TIPO_NOTI HOST_ALIAS HOST_ADDRESS HOST_STATE HOST_OUTPUT
            #len(argvs) = 7
            if len(sys.argv) != 7:
                #print('Cantidad de parámetros incorrecta')
                exit(1)
            parametros = {
                'tipo_notificacion' : sys.argv[2].lower(),
                'host_alias'        : sys.argv[3],
                'host_address'      : sys.argv[4].upper(),
                'host_state'        : sys.argv[5].upper(),
                'host_output'       : sys.argv[6].upper()
            }
            salida = check_host(parametros)
            exit(salida)
        else:
            #print('error')
            exit(1)
    except IndexError:
        #print('No se agregaron arguméntos')
        exit(1)

if __name__ == '__main__':
    if os.path.isfile(CONFIG) == False:
        #print('Error al abrir config. ¿existe el archivo en {0}?'.format(CONFIG))
        exit(1)
    else:
        config = configparser.ConfigParser()
        config.read(CONFIG)  #leo config.cfg
    try:
        main(sys.argv[1].upper())
    except IndexError:
        exit(1)
        #print('Error en parámetros {0}'.format(sys.argv))
