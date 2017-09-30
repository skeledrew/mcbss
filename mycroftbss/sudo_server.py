#! /usr/local/bin/python

# This file is part of brain-skill

# mycroftbss - This is an extension that is intended to assist in communicating with brain-skill for Mycroft.

# @author Andrew Phillips
# @copyright 2017 Andrew Phillips <skeledrew@gmail.com>

# brain-skill is free software; you can redistribute it and/or
# modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
# License as published by the Free Software Foundation; either
# version 3 of the License, or any later version.

# brain-skill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU AFFERO GENERAL PUBLIC LICENSE for more details.

# You should have received a copy of the GNU Affero General Public
# License along with brain-skill.  If not, see <http://www.gnu.org/licenses/>.


import sys

import rpyc

from mycroft.skills.settings import SkillSettings


class SudoServicesError(Exception):

    def __init__(self, message):
        super(SudoServicesError, self).__init__(message)
        self._message = message

    def __str__(self):
        return self._message

class SudoService(rpyc.Service):

    def on_connect(self):
        self._dir = '/etc/mycroftbss'
        self.settings = SkillSettings(self._dir)

    def on_disconnect(self):
        self.settings.store()

    def service_error(self):
        return SudoServicesError('An error occurred. Please submit an issue containing details to replicate.')

    def exposed_register(self, skill):
        if not type(skill) == type(self.get_brain(skill)): return SudoServicesError('{} at {} is not allowed to register skills for sudo'.format(skill.name, skill._dir))

    def exposed_call(self, func, arg_dict):
        try:
            return self.call(func, arg_dict)

        except Exception as e:
            print 'Exception in exposed_call: {}'.format(repr(e))
            return self.service_error()

    def call(self, func, arg_dict):
        #if not 'auth_meta' in arg_dict or not arg_dict['auth_meta']['skill_path'] in self.settings['sudoers']: return SudoServicesError('{} at {} is not a recognized sudoer'.format(arg_dict['auth_meta']['skill_name'], arg_dict['auth_meta']['skill_path']))
        return func(arg_dict)

    def exposed_shutdown(self, skill):
        try:
            return self.shutdown(skill)

        except Exception as e:
            print 'Exception in exposed_shutdown: {}'.format(repr(e))
            return self.service_error()

    def shutdown(self, skill):
        if not type(skill) == type(self.get_brain(skill)): return False
        shutdown = True
        brain_skill = skill

    def get_brain(self, skill):
        return None

brain_skill = None
shutdown = False

if __name__ == '__main__':
    port = 9999 if len(sys.argv) < 2 else sys.argv[1]
    from rpyc.utils.server import OneShotServer

    while not shutdown: #and not brain_skill.kill_sudo_server():
        server = None

        try:
            server = OneShotServer(SudoService, 'localhost', port=port)
            server.start()
            server = None

        except KeyboardInterrupt:
            print 'Terminating server...'
            break

        except Exception as e:
            print 'Something broke: {}. Restarting...'.format(repr(e))
            server = None
