#Icinga2Jira module for jirador

def jira_open(type='HOST', config, parametros):
    """
        jira_open(type='HOST', config, parametros):
            opens the ticket on Jira.
            Change the 'summary' with the title you want.
    """
    if type=='HOST':
        desc = 'Notification Type: {0}\nHost Alias:\
     {1}\nHost Address: {2}\nHost State: {3}\nHost Output: {4}'.format(
                                            parametros['tipo_notificacion'],
                                            parametros['host_alias'],
                                            parametros['host_address'],
                                            parametros['host_state'],
                                            parametros['host_output']
                                            )

        jason = """{0} "type": "Host", "host": "{1}", "author": "jirador", "comment": "<a href='{4}{2}' target='_blank'>{2}</a>", "notify": true {3}""".format(
             chr(123), parametros['host_alias'], nuevo_issue, chr(125), config['JIRA']['url'])

    elif type=='SERVICE':
        desc = 'Notification Type: {0}\nService Description: {1}\nHost Alias:\
      {2}\nHost Address: {3}\nService State: {4}\nService Output: {5}'.format(
                                             parametros['tipo_notificacion'],
                                             parametros['service_desc'],
                                             parametros['host_alias'],
                                             parametros['host_address'],
                                             parametros['service_state'],
                                             parametros['service_output'])

        jason = """{0} "type": "Service", "service": "{1}!{2}", "author": "jirador", "comment":  "<a href={4}{3}' target='_blank' >{3}</a>", "notify": true {4}""".format(
            chr(123), parametros['host_alias'], parametros['service_desc'],
            nuevo_issue, chr(125), config['JIRA']['url'])


    issue_dict = {
        'project': {'key': config['JIRA']['jira_key']},
        'summary' : 'ICINGA2 | {0} - {1} is {2}'.format(
                                            parametros['tipo_notificacion'],
                                            parametros['host_alias'],
                                            parametros['host_state']),
        'description' : desc,
        'labels' : [config['JIRA']['label'],'icinga2'],
        'components' : [{'name': '{0}'.format(parametros['host_alias'])}],
        'issuetype' : {'name': config['JIRA']['jira_tipo_issue']},
    }
    nuevo_issue = instance.create_issue(fields=issue_dict)
    o = str(subprocess.check_output(
            """curl -k -s -u {0}:{1} -H 'Accept: application/json' '{2}' -d '{3}'""".format(
                config['ICINGA2']['api_user'],
                config['ICINGA2']['api_password'],
                config['ICINGA2']['url_com'],
                jason), shell=True))
    return True


def jira_close(config, parametros):
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

def jira_comment(type='HOST', config, parametros):
    """
        jira_comment(parametros)
            add a comment to an issue

    """
    if type=='HOST':
        dict = 'Notification Type: {0}\nHost Alias:\
         {1}\nHost Address: {2}\nHost State: {3}\nHost Output: {4}'.format(
             parametros['tipo_notificacion'],
             parametros['host_alias'],
             parametros['host_address'],
             parametros['host_state'],
             parametros['host_output']
         )
    elif type=='SERVICE':
        dict='Notification Type: {0}\nService Description: {1} Host Alias:\
    {2}\nHost Address: {3}\nService State: {4}\nService Output: {5}'.format(
            parametros['tipo_notificacion'],
            parametros['service_desc'],
            parametros['host_alias'],
            parametros['host_address'],
            parametros['service_state'],
            parametros['service_output'])

    issue = parametros['ticket']
    instance.add_comment(issue,dict)
    return True
