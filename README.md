# Icinga2Jira
Create jira issues when a icingaweb2 notification is sent.

## Origins
I created this script at work, when I found out that our monitoring system (icinga2) sends emails to all sysadminds when a critical service or host is down. When a sysadmin acknowledges the issue on icinga, it also needs to create a jira issue by hand. This script automates that. When icinga2 sends the notification, it also creates the issue using the jira API


## Requirements
* Python3
* jira-python [Read the docs](https://jira.readthedocs.io/en/master/)
* Icinga2
* Api access for Icinga2 [Check Icinga2 Documentation ](https://www.icinga.com/docs/icinga2/latest/doc/12-icinga2-api/)
* Jira instance

## Objetive
Create a Jira issue using the specified parameters inside config.cfg when the script is called, ideally when a icinga2 notification ([See here](https://www.icinga.com/docs/icinga2/latest/doc/03-monitoring-basics/#notifications)) is sent.

## How does it work?
The script was created by mimic the parameters icinga2 sends to the example scripts **mail_host_notification.sh** and **mail_service_notification.sh** that come with the default installation as examples (you can check them [here](https://github.com/Icinga/icinga2/tree/master/etc/icinga2/scripts)).

If a **service** is down:

    ./jirador.py SERVICE \
		NOTIFICATION_TYPE\
		SERVICE_DESCRIPTION\
		HOST_ALIAS\
		HOST_ADDRESS\
		SERVICE_STATE\
		SERVICE_OUTPUT

If a **host** is down:

    jirador.py HOST\
		NOTIFICATION_TYPE\
		HOST_ALIAS\
		HOST_ADDRESS\
		HOST_STATE\
		HOST_OUTPUT

When the script is called, checks for the firts parameter to determine if the issue is caused by a service or a host. After that, it connects to the Jira instance and:

* Checks if there is already a ticket created for this service/host and tagged with the tags specified on the config.cfg (i.e "icinga2", so it can filter and specify only the issues generated with this script.)
	* If there is already a ticket generated, it comments on it the default message, giving the SERVICE_STATE, SERVICE_OUTPUT and timestamps.
	* If there is none, it creates one, creating a jira componment (by default, the HOST_ALIAS) if needed.

In addition, when it creates a ticket, it checks if the HOST_ALIAS has a custom variable in icinga2 called "VmParent", that tells us if the specified host is a virtual one. If that is the case, jirador checks the status of the vmparent *before* creating an issue:
* If the VmParent is Down, it does not create nothing (it will create an issue when icinga2 sends a notification for the VmParent)
* If the VmParent is Up, it creates an issue for the HOST_ALIAS

This was intented to limit the creating of issues on jira, i.e. if a VmParent is down, there is no need to create indivual tickets for all the virtual hosts on that parent, it only creates one.

When the issue is created, it creates a comment on the host/service description on icinga2 linking to the jira issue. If you modify the **url_com** on the config.cfg, you can create an acknowledge instead of a comment, up to your sysadmin needs.

When the host/service is in RECOVERY state, and you specify icinga2 to send emails of this RECOVERY, it will look for the issue on jira, comment on it the RECOVERY message and closes the issue.

All the configurations are on the config.cfg.


## TODO:
* Check dependencies
* Refactoring. Too much redundancy.
	* Create a module to call instead of using jira_host and jira_service

## Final words
Im justs a n00b sysadmin, i know that this code could be improved, but it looks like a nice first step if you want to automate this proccess and populate your jira with monitoring alerts. More tickets, yay!
