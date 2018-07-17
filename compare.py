#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Module for compare git for projects:
comments   - create diff comments
changelist - make release notes

Get data for this script
git log --oneline [hash]..HEAD > git.log
"""

import sys
import re
from jira import JIRA
from slackweb import Slack
import requests

# array to store dict of commit data
commits = []
issueLength = 7
login = 'technical_user'
password = 'password'
issueId = 'test-'
urlSlack = "https://hooks.slack.com/services/"
uriSlack = ""
uriSlackMaster = ""
urlDiscord = "https://discordapp.com/api/webhooks/"
uriDiscord = ""
uriDiscordMaster = ""
urlJira = "https://jira.example.ru"
uriJira = "/projects/test/issues/"

def parse_commit(commitLines):
    # dict to store commit data
    # commit = {}
    # iterate lines and save
    for nextLine in commitLines:
        # ignore empty lines
        if nextLine != '' or nextLine != '\n':
            # split line to commit hash and message
            data = nextLine.split(' ', 1)
            if len(data[0]) != 0:		## new commit
                commit = {'hash': data[0], 'message': data[1].rstrip('\n')}
                commits.append(commit)


def find_comments(commits):
    changes = set()
    for item in commits:
        message = item['message'].lower()
        # location of jira issue
        loc = message.find(issueId)
        if item == '':
            print('error ', item['hash'], 'commit is null')
        # comment without jira issue
        elif loc < 0 and message.find('merge') < 0:
            changes.add(message)
        # with jira issue
        elif loc >=0:
            message = message[loc: loc + issueLength]
            changes.add(message)
    return changes


def make_change_list(comments):
    changeList = set()
    for comment in comments:
        if comment == '':
            pass
        # add issue name to comments with jira issue id
        elif comment.find(issueId) == 0:

            # connect to jira
            jira = JIRA(urlJira, basic_auth=(login, password))
            issue = jira.issue(comment)

            # print issue.fields.project.key             # 'JRA'
            # print issue.fields.issuetype.name          # 'New Feature'
            # print issue.fields.reporter.displayName    # 'Mike Cannon-Brookes [Atlassian]'

            try:
                # jira issue name
                summary = issue.fields.summary
                # making a changelist from jira
                link = summary + urlJira + uriJira + comment
                changeList.add(link)
            except:
                print('JIRA gone away')
        # comments without jira issue id
        elif comment.find(issueId) <0:
            changeList.add(comment)
    return changeList


def make_message(changeList):
    # making str from set
    message = u' New release '
    for change in changeList:
        message = message + "\n" + change

    print(message)
    return message


def send_slack_notify(message):
    slack = Slack(url=urlSlackWebhook)

    # slack.notify(text="Release at catalog", channel="#test", username="sushi-bot", icon_emoji=":sushi:")

    # sending notify to Slack
    attachments = []
    attachment = {"title": title, "text": message,
                  "mrkdwn_in": ["text", "pretext"]}
    attachments.append(attachment)
    slack.notify(attachments=attachments)


def send_discord_notify(message):

    # Post the message to the Discord webhook
    data = {"content": message}
    response = requests.post(urlDiscordWebhook, data=data)

    print('Discord status code:', response.status_code)


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print('Missing git data. Use example:'
              'python compare.py repo changelist git.log')
    elif len(sys.argv) >= 3:
        repo = sys.argv[1]
        title = u"New release at " + repo
        # change discord uri for deployment on production
        if repo == "web_master" or repo == "catalog_master":
            urlSlackWebhook = urlSlack + uriSlackMaster
            urlDiscordWebhook = urlDiscord + uriDiscordMaster
        else:
            urlSlackWebhook = urlSlack + uriSlack
            urlDiscordWebhook = urlDiscord + uriDiscord
        opName = sys.argv[2]
        fileName = sys.argv[3]
        try:
            with open(fileName, 'r', encoding='UTF-8') as log:
                parse_commit(log.readlines())
        except OSError:
            print('Log file not found')

    # parse log data
    comments = find_comments(commits)

    # print git log comments
    if opName == 'comments':
        print(comments)
    # print and send changelist to Slack
    elif opName == 'changelist':
        # make list of comments
        changeList = make_change_list(comments)
        if not changeList:
            print('No changes')
        else:
            # make message for notify
            message = make_message(changeList)
            # send Slack message and print the response
            send_slack_notify(message)
            # send Discord message and print the response
            send_discord_notify(title + "\n" + message)

