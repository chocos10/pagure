#!/usr/bin/env python

from __future__ import print_function
import os
import argparse
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError

import pagure.config
import pagure.lib
import pagure.lib.model as model

if 'PAGURE_CONFIG' not in os.environ \
        and os.path.exists('/etc/pagure/pagure.cfg'):
    print('Using configuration file `/etc/pagure/pagure.cfg`')
    os.environ['PAGURE_CONFIG'] = '/etc/pagure/pagure.cfg'

_config = pagure.config.reload_config()


def main(check=False, debug=False):
    ''' The function that actually sends the email
    in case the expiration date is near'''

    current_time = datetime.utcnow()
    day_diff_for_mail = [10, 5, 1]
    email_dates = [email_day.date() for email_day in \
            [current_time + timedelta(days=i) for i in day_diff_for_mail]]

    session = pagure.lib.create_session(_config['DB_URL'])
    tokens = session.query(model.Token).all()

    for token in tokens:
        if debug:
            print(token.id, token.expiration.date())
        if token.expiration.date() in email_dates:
            user = token.user
            username = user.fullname or user.username
            user_email = user.default_email
            project = token.project
            days_left = token.expiration.day - datetime.utcnow().day
            subject = 'Pagure API key expiration date is near!'
            text = '''Hi %s, \nYour Pagure API key for the project %s will expire
    in %s day(s). Please get a new key for non-interrupted service. \n
    Thanks, \nYour Pagure Admin. ''' % (username, project.name, days_left)
            if not check:
                msg = pagure.lib.notify.send_email(text, subject, user_email)
            else:
                print('Sending email to %s (%s) about key: %s' % (
                    username, user_emailk, token.id))
            if debug:
                print('Sent mail to %s' % username)

    session.remove()
    if debug:
        print('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Script to send email before the api token expires')
    parser.add_argument(
        '--check', dest='check', action='store_true', default=False,
        help='Print the some output but does not send any email')
    parser.add_argument(
        '--debug', dest='debug', action='store_true', default=False,
        help='Print the debugging output')
    args = parser.parse_args()
    main(debug=args.debug)
