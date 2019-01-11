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

def check_dependencies(alias):
    """
        check_dependencies(alias):
            TODO: Create a list of "dependencies"
            to check before creating an issue
            (for example: if a https service is down, check before if there is
            an internet connection.)

    """
    pass
    return True

def jira_host(call,params):
    """
    jira_host(call, params):
        All the functions to use with host are here. Hope to change This
        To use a module and save a lot of code.
    """
    def jira_open(params):
        """
            jira_open(params):
                opens the ticket on Jira.
                Change the 'summary' with the title you want.
        """
        issue_dict = {
            'project': {'key': config['JIRA']['jira_key']},
            'summary' : 'ICINGA2 | {0} - {1} is {2}'.format(params['tipo_notificacion'],
                                                params['host_alias'],
                                                params['host_state']),
            'description' : 'Notification Type: {0}\nHost Alias:\
         {1}\nHost Address: {2}\nHost State: {3}\nHost Output: {4}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          .format(
                                                params['tipo_notificacion'],
                                                params['host_alias'],
                                                params['host_address'],
                                                params['host_state'],
                                                params['host_output']
                                                ),
            'labels' : [config['JIRA']['label'],'icinga2'],
            'components' : [{'name': '{0}'.format(params['host_alias'])}],
            'issuetype' : {'name': config['JIRA']['jira_tipo_issue']},
        }
        new_issue = instance.create_issue(fields=issue_dict)
        jason = """{0} "type": "Host", "host": "{1}", "author": "jirador", "comment": "<a href='{4}{2}' target='_blank'>{2}</a>", "notify": true {3}""".format(
            chr(123), params['host_alias'], new_issue, chr(125), config['JIRA']['url'])
        o = str(subprocess.check_output(
                """curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}' -d '{3}'""".format(
                    config['ICINGA2']['api_user'],
                    config['ICINGA2']['api_password'],
                    config['ICINGA2']['url_com'],
                    jason), shell=True))
        return True

    def jira_close(params):
        """
            jira_close(params)
                Searches for the issue and closes it
                Add comment with the last state.
        """
        alias = params['host_alias']
        ticket = jira_check(alias)
        params['ticket'] = ticket[1]
        jira_comment(params)
        instance.transition_issue(ticket[1],
        config['JIRA']['transition'],
        resolution={'name' : config['JIRA']['resolution']}
        )
        return True

    def jira_comment(params):
        """
            jira_comment(params)
                add a comment to an issue

        """
        issue = params['ticket']
        instance.add_comment(issue,'Notification Type: {0}\nHost Alias:\
         {1}\nHost Address: {2}\nHost State: {3}\nHost Output: {4}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          .format(
             params['tipo_notificacion'],
             params['host_alias'],
             params['host_address'],
             params['host_state'],
             params['host_output']
         ))
        return True

    def jira_check(alias):
        """
            jira_check(alias):
            Check if the alias does not have a ticket
                (the alias is as tag), in the future it would be COMPONENT
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
            instance.create_component(params['host_alias'], config['JIRA']['jira_key'])
        except:
            pass
        try:
            exit = jira_check(params['host_alias'])
            return(exit)
        except:
            instance.create_component(config['JIRA']['jira_key'], params['host_alias'])
            jira_host(call,params)

    elif call == 'OPEN':
        jira_open(params)
    elif call == 'COMMENT':
        return(jira_comment(params))
    elif call == 'CLOSE':
        return(jira_close(params))

def check_host(params):
    """
    check_host(params):
        If a host is down, checks if there an issue createdself.
        If there's an issue: comments on it.
        If not, checks for VmParent
                If Vmparent is down: does nothing
                If VmParent is up, creates an issue
    """
    if params['host_state'] == 'DOWN':
        exit = jira_host('CHECK',params)
        if exit[0] == False: # No existe ticket para el elemento
            #Checks for VmParent on icinga2
            o = str(subprocess.check_output(
                shlex.split(
                    "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".format(
                        config['ICINGA2']['api_user'],
                        config['ICINGA2']['api_password'],
                        config['ICINGA2']['url'],
                        params['host_alias'].lower()))))
            o = o[2:-1]
            exit = json.loads(o)
            exit = exit['results'][0]
            if VARS_VMPARENT in exit['attrs']['vars'].keys(): # VmParent is a Var of the host?
                VMPARENT = True
                #Check status of VmParent
                o = str(
                    subprocess.check_output(
                        shlex.split(
                            "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".
                            format(config['ICINGA2']['api_user'],
                                   config['ICINGA2']['api_password'],
                                   config['ICINGA2']['url'],
                                   exit['attrs']['vars'][VARS_VMPARENT]))))
                o = o[2:-1]
                exit_vmparent = json.loads(o)
                exit_vmparent = exit_vmparent['results'][0]
                if exit_vmparent['attrs']['state'] == 0.0: #VMPARENT OK, issues ticket
                    jira_host('OPEN', params)
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
                jira_host('OPEN',params)
                return True
        else:
            # Ticket exists, comments on it.
            params['ticket'] = exit[1]
            jira_host('COMMENT',params)
            return True
    elif params['host_state'] == 'UP':
        # HOST IS UP
        # closes TICKET
        jira_host('CLOSE',params)
        return True

####### SERVICE
def jira_service(call, params):
    """
    jira_service
        same as jira_host. i don't know how to code
        Working to get this to a MODULE
    """
    def jira_open(params):
        """
            jira_open(params):
                Opens a jira issue
        """
        issue_dict = {
            'project': {
                'key': config['JIRA']['jira_key']
            },
            'summary':
            'ICINGA2 | {0} - {1} - {2} is {3}'.format(params['tipo_notificacion'],
                                      params['host_alias'],
                                      params['service_desc'],
                                      params['service_state']),
            'description':
            'Notification Type: {0}\nService Description: {1}\nHost Alias:\
         {2}\nHost Address: {3}\nService State: {4}\nService Output: {5}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               .format(
                params['tipo_notificacion'],
                params['service_desc'],
                params['host_alias'],
                params['host_address'],
                params['service_state'],
                params['service_output']),
            'labels': [config['JIRA']['label'],'icinga2'],
            'components': [{
                'name': '{0}'.format(params['host_alias'])
            }],
            'issuetype': {
                'name': config['JIRA']['jira_tipo_issue']
            },
        }
        new_issue = instance.create_issue(fields=issue_dict)
        jason = """{0} "type": "Service", "service": "{1}!{2}", "author": "jirador", "comment":  "<a href={4}{3}' target='_blank' >{3}</a>", "notify": true {4}""".format(
            chr(123), params['host_alias'], params['service_desc'],
            new_issue, chr(125), config['JIRA']['url'])
        o = str(
            subprocess.check_output(
                """curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}' -d '{3}'""".
                format(config['ICINGA2']['api_user'],
                       config['ICINGA2']['api_password'],
                       config['ICINGA2']['url_com'], jason),
                shell=True))
        #print(o)
        return True

    def jira_close(params):
        """
            jira_close(params)
                closes a ticket
        """
        alias = params['host_alias']
        ticket = jira_check(alias)
        #print('Cerrando {0}'.format(ticket[1]))
        params['ticket'] = ticket[1]
        jira_comment(params)
        instance.transition_issue(
            ticket[1],
            config['JIRA']['transition'],
            resolution={
                'name': config['JIRA']['resolution']
            })
        return True

    def jira_comment(params):
        """
            jira_comment(params)
                comments on a ticket

        """
        issue = params['ticket']
        instance.add_comment(issue, 'Notification Type: {0}\nService Description: {1} Host Alias:\
         {2}\nHost Address: {3}\nService State: {4}\nService Output: {5}'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               .format(
            params['tipo_notificacion'],
            params['service_desc'],
            params['host_alias'],
            params['host_address'],
            params['service_state'],
            params['service_output']))
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
            config['JIRA']['label'], params['host_alias'])
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
            instance.create_component(params['host_alias'], config['JIRA']['jira_key'])
        except:
            pass
        try:
            exit = jira_check(params['service_desc'])
            return (exit)
        except:
            jira_service(call, params)
    elif call == 'OPEN':
        jira_open(params)
    elif call == 'COMMENT':
        return (jira_comment(params))
    elif call == 'CLOSE':
        return (jira_close(params))

def check_service(params):
    """
    check_service(params):
        IF SERVICE IS CRITICAL
            CHECKS if ticket is up
             If ticket exists, comments on it
            # if ticket does not exist -> checks if host_alias has a ticket
            #                    -> if host_alias has an issue, ignores this
            #                    -> if host_alias is ok, raises a  ticket
    """

    if params['service_state'] == 'CRITICAL' :
        exit = jira_service('CHECK', params)
        if exit[0] == False: does not have a ticket
            o = str(
                subprocess.check_output(
                    shlex.split(
                        "curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}/hosts?host={3}'".
                        format(config['ICINGA2']['api_user'],
                               config['ICINGA2']['api_password'],
                               config['ICINGA2']['url'],
                               params['host_alias']))))
            o = o[2:-1]
            exit_hostalias = json.loads(o)
            exit_hostalias = exit_hostalias['results'][0]
            if exit_hostalias['attrs']['state'] == 0.0: #HOST IS OK
            #raises a ticket for service
                jira_service('OPEN',params)
                return True
            else: #HOST_ALIAS NOT OK, ignores it
                pass
        ###
        else: #has ticket, comments it
            params['ticket'] = exit[1]
            jira_service('COMMENT',params)
            return True
    else:  #Service is OK / closes ticket
        jira_service('CLOSE', params)
        return True



def main(tipo):
    try:
        if tipo == 'SERVICE':
            #Issue is raised for a service. Needs 8 args
            if len(sys.argv) != 8:

                exit(1)
            params = {
                'tipo_notificacion': sys.argv[2].lower(),
                'service_desc'     : sys.argv[3],
                'host_alias'       : sys.argv[4],
                'host_address'     : sys.argv[5].upper(),
                'service_state'    : sys.argv[6].upper(),
                'service_output'   : sys.argv[7].upper()
                }
            exit = check_service(params)
            exit(exit)
        elif tipo == 'HOST':
            #Issue is raised for a HOST. Needs 7 args
            if len(sys.argv) != 7:
                exit(1)
            params = {
                'tipo_notificacion' : sys.argv[2].lower(),
                'host_alias'        : sys.argv[3],
                'host_address'      : sys.argv[4].upper(),
                'host_state'        : sys.argv[5].upper(),
                'host_output'       : sys.argv[6].upper()
            }
            exit = check_host(params)
            exit(exit)
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
