#!/usr/bin/python3

# jirador.py : Create a jira issue when a icinga2 notification is sent.
# Check Readme!
# Copyright (c) 2018 Nicolás Giorgetti
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import subprocess
import shlex
import jira
import configparser
import os
import sys
import json


VERSION = '1.0.1'
# Full path where to look for the config.cfg
CONFIG = '/opt/icinga2-jira/config.cfg'
# Custom Variable on icinga2 to check for vm parents
VARS_VMPARENT = 'vm_parent'

def check_dependencias(alias):
    """
        check_dependencias(alias):
            TODO: Create a list of "dependencies"
            to check before creating an issue
            (for example: if a https service is down, check before if there is
            an internet connection.)

    """
    pass
    return True

def jira_host(call,parametros):
    """
    jira_host(call, parametros):
        All the functions to use with host are here. Hope to change This
        To use a module and save a lot of code.
    """
    def jira_open(parametros):
        """
            jira_open(parametros):
                opens the ticket on Jira.
                Change the 'summary' with the title you want.
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
        nuevo_issue = instance.create_issue(fields=issue_dict)
        jason = """{0} "type": "Host", "host": "{1}", "author": "jirador", "comment": "<a href='{4}{2}' target='_blank'>{2}</a>", "notify": true {3}""".format(
            chr(123), parametros['host_alias'], nuevo_issue, chr(125), config['JIRA']['url'])
        o = str(subprocess.check_output(
                """curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}' -d '{3}'""".format(
                    config['ICINGA2']['api_user'],
                    config['ICINGA2']['api_password'],
                    config['ICINGA2']['url_com'],
                    jason), shell=True))
        return True

    def jira_close(parametros):
        """
            jira_close(parametros)
                Searches for the issue and closes it
                Add comment with the last state.
        """
        alias = parametros['host_alias']
        ticket = jira_check(alias)
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
                add a comment to an issue

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
            # TICKET EXIST
            return [True,result[0].key]

    try:
        instance = jira.JIRA(config['JIRA']['url'], basic_auth=(
            config['JIRA']['username'],
            config['JIRA']['password']))
    except:
        #Error on login
        exit(1)

    if call == 'CHECK':
        try:
            instance.create_component(parametros['host_alias'], config['JIRA']['jira_key'])
        except:
            pass
        try:
            salida = jira_check(parametros['host_alias'])
            return(salida)
        except:
            instance.create_component(config['JIRA']['jira_key'], parametros['host_alias'])
            jira_host(call,parametros)

    elif call == 'OPEN':
        jira_open(parametros)
    elif call == 'COMMENT':
        return(jira_comment(parametros))
    elif call == 'CLOSE':
        return(jira_close(parametros))

def check_host(parametros):
    """
    check_host(parametros):
        If a host is down, checks if there an issue createdself.
        If there's an issue: comments on it.
        If not, checks for VmParent
                If Vmparent is down: does nothing
                If VmParent is up, creates an issue
    """
    if parametros['host_state'] == 'DOWN':
        salida = jira_host('CHECK',parametros)
        if salida[0] == False: # No existe ticket para el elemento
            #Checks for VmParent on icinga2
            o = str(subprocess.check_output(
                shlex.split(
                    "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".format(
                        config['ICINGA2']['api_user'],
                        config['ICINGA2']['api_password'],
                        config['ICINGA2']['url'],
                        parametros['host_alias'].lower()))))
            o = o[2:-1]
            salida = json.loads(o)
            salida = salida['results'][0]
            if VARS_VMPARENT in salida['attrs']['vars'].keys(): # VmParent is a Var of the host?
                VMPARENT = True
                #Check status of VmParent
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
                if salida_vmparent['attrs']['state'] == 0.0: #VMPARENT OK, issues ticket
                    jira_host('OPEN', parametros)
                    return True
                else:
                    #VMPARENT is NOT OK,
                    #Does nothing. Hopes that icinga2 sends notification
                    #when VMPARENT = HOST_ALIAS
                    pass

            else:
                VMPARENT = False
                #NO VMParent
            if VMPARENT:
                pass
                return True
            else:
                # Opens Ticket
                jira_host('OPEN',parametros)
                return True
        else:
            # Ticket exists, comments on it.
            parametros['ticket'] = salida[1]
            jira_host('COMMENT',parametros)
            return True
    elif parametros['host_state'] == 'UP':
        # HOST IS UP
        # closes TICKET
        jira_host('CLOSE',parametros)
        return True

####### SERVICE
def jira_service(call, parametros):
    """
    jira_service
        same as jira_host. i don't know how to code
        Working to get this to a MODULE
    """
    def jira_open(parametros):
        """
            jira_open(parametros):
                Opens a jira issue
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
        nuevo_issue = instance.create_issue(fields=issue_dict)
        jason = """{0} "type": "Service", "service": "{1}!{2}", "author": "jirador", "comment":  "<a href={4}{3}' target='_blank' >{3}</a>", "notify": true {4}""".format(
            chr(123), parametros['host_alias'], parametros['service_desc'],
            nuevo_issue, chr(125), config['JIRA']['url'])
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
                closes a ticket
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
                comments on a ticket

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
                check if alias has a ticket
                returns [TIENE_TICKET, '' o TICKET]
        """
        QUERY = 'project={0} AND issuetype={1} AND status="{2}" AND labels="{3}" AND component ="{4}"'.format(
            config['JIRA']['jira_key'],
            config['JIRA']['jira_tipo_issue'],
            config['JIRA']['jira_status'],
            config['JIRA']['label'], parametros['host_alias'])
        result = instance.search_issues(QUERY)
        if len(result) == 0:
            # NO TICKET
            return [False, '']
        else:
            # HAS TICKET, RETURNS IT
            return [True, result[0].key]

    try:
        instance = jira.JIRA(
            config['JIRA']['url'],
            basic_auth=(config['JIRA']['username'],
                        config['JIRA']['password']))
    except:
        #ERROR ON JIRA LOGIN
        exit(1)

    if call == 'CHECK':
        try:
            #Creates component for alias.
            instance.create_component(parametros['host_alias'], config['JIRA']['jira_key'])
        except:
            pass
        try:
            salida = jira_check(parametros['service_desc'])
            return (salida)
        except:
            jira_service(call, parametros)
    elif call == 'OPEN':
        jira_open(parametros)
    elif call == 'COMMENT':
        return (jira_comment(parametros))
    elif call == 'CLOSE':
        return (jira_close(parametros))

def check_service(parametros):
    """
    check_service(parametros):
        IF SERVICE IS CRITICAL / WARNING OR UNKNOWN
            CHECKS if ticket is up
             If ticket exists, comments on it
            # if ticket does not exist -> checks if host_alias has a ticket
            #                    -> if host_alias has an issue, ignores this
            #                    -> if host_alias is ok, raises a  ticket
    """

    if parametros['service_state'] == 'CRITICAL' or parametros['service_state'] == 'WARNING' or parametros['service_state'] == 'UNKNOWN' :
        salida = jira_service('CHECK', parametros)
        if salida[0] == False: does not have a ticket
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
            if salida_hostalias['attrs']['state'] == 0.0: #HOST IS OK
            #raises a ticket for service
                jira_service('OPEN',parametros)
                return True
            else: #HOST_ALIAS NOT OK, ignores it
                pass
        ###
        else: #has ticket, comments it
            parametros['ticket'] = salida[1]
            jira_service('COMMENT',parametros)
            return True
    else:  #Service is OK / closes ticket
        jira_service('CLOSE', parametros)
        return True



def main(tipo):
    try:
        if tipo == 'SERVICE':
            #Issue is raised for a service. Needs 8 args
            if len(sys.argv) != 8:

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
            #Issue is raised for a HOST. Needs 7 args
            if len(sys.argv) != 7:
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
            exit(1)
    except IndexError:
        #No arguments
        exit(1)

if __name__ == '__main__':
    if os.path.isfile(CONFIG) == False:
        #No config
        exit(1)
    else:
        config = configparser.ConfigParser()
        config.read(CONFIG)  #reads config.cfg
    try:
        main(sys.argv[1].upper())
    except IndexError:
        exit(1)
        #print('Error on parameters {0}'.format(sys.argv))
