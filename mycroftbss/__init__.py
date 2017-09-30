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


from os.path import exists, dirname, abspath
import inspect

import rpyc

from mycroft.skills.core import MycroftSkill
from mycroft.messagebus.message import Message


__version__ = '0.1.0'


class SudoClient(object):

    def __init__(self, skill, port=9999, interval=.1):
        if not find_brain(skill): return None
        if not self.registered_skill(skill): return None
        self._skill = skill
        self._port = port
        self._interval = interval
        self.ready = False
        self._status = 'pending'

    def _connect(self):
        conn = None

        try:
            conn = rpyc.connect('localhost', self._port)

        except Exception as e:
            self._status = e
            self.ready = False
        if conn: self.ready = True
        self.sudo_service = conn.root

    def _run_as_sudo(self, func_name, arg_dict={}, callback=None):
        # TODO: process bash commands also

        if not self.valid_sudo_request(self._skill):
            announce(self._skill, '{} cannot request sudo access'.format(self._skill.name))
            return False
        auth_meta = {}
        auth_meta['skill_path'] = dirname(abspath(self._skill.__module__))
        auth_meta['skill_name'] = self._skill.name
        #auth_meta['sse'] = SudoServicesError
        arg_dict['auth_meta'] = auth_meta
        self._connect()
        if not self.ready: return False
        self.callback = callback
        self.ready = False
        self._result = self.sudo_service.call(func, arg_dict)
        if isinstance(self._result, Exception): raise self._result
        return True

    def run_as_sudo(self, func, args=[], kwargs={}, wait=False, callback=None):
        args_dict = {'args': args, 'kwargs': kwargs}
        result = None

        try:
            if not callback or not wait: return self._run_as_sudo(func, args_dict)
            self._run_as_sudo(func, args_dict, callback)

    def get_result(self):
        if not self.ready and not self.callback: raise Exception('Ensure results are ready before asking for results, or provide a callback')
        if self.ready and not self.callback: return self._result
        if not self.ready and self.callback: Timer(self._interval, self.get_result)
        if self.ready and self.callback: self.callback(self._skill, self._result)

    def registered_skill(self, skill):
        # TODO: validate skill with brain
        return True

    def valid_sudo_request(skill):
        auth_conf = get_auth_confidence(skill)
        return True if auth_conf == 1.0 else False


def whisper(this=None, msg=None):
    # direct query to a particular skill/intent; should prob not register
    pattern = 'call intent (?P<Intent>.+) in skill (?P<Skill>.+) with data (?P<Data>.+)( and context )?(?P<Context>.+)?'
    if not this and not msg: return None #pattern
    if not find_brain(this): return False
    data = {}

    if isinstance(msg, unicode) and re.search(pattern, msg):
        match = re.match(pattern, msg)
        skill_id = match.group('Skill')
        skill_id = ''.join(skill_id.title().split(' '))
        intent_name = match.group('Intent')
        intent_name = ''.join(intent_name.title().split(' '))
        target = '{}:{}'.format(skill_id, intent_name)
        data = match.group('Data')  # massage string into a dict
        data = re.sub(' *and *', '&', re.sub(' *equal *', '=', data))
        data = {key: value for key, value in [[d.split('=')[0], d.split('=')[1]] for d in data.split('&')]}
        context = match.group('Context') #if 'Context' in msg.data else None
        this.log.info('Generated message params: target = {}, data = {}, context = {}'.format(target, data, context))
        this.emitter.emit(Message(target, data, context))
        return True

    elif isinstance(msg, dict) and 'target' in msg:
        # called as a regular function
        target = msg['target']
        data = msg['data']
        context = msg['context'] if 'context' in msg else None
        this.emitter.emit(Message(target, data, context))
        return True
    this.log.error('Unable to process whispered message: {}'.format(repr(msg.data)))
    return False

def shout(this=None, utterances=None):
    # broadcast query so any skill/intent can handle
    if not this: return None  # prevent addition as ability
    if not find_brain(this): return False

    if not type(utterances) in [str, list, unicode]:
        this.log.error('Expected string or list, got: {} which is {}'.format(repr(utterances), str(type(utterances))[1:-1]))
        return None
    if isinstance(utterances, unicode): utterances = [utterances.strip()]
    this.emitter.emit(Message("recognizer_loop:utterance", {"lang": "en-us", "utterances": utterances}))
    return True

def submit_intents(skill):
    # get all intents; can prob have a special name for subscribe
    if not find_brain(skill): return False
    intents = [[skill.name, i[1].__dict__] for i in skill.registered_intents]
    blob = {'target': 'BrainSkill:Accept000Intent', 'data': intents}
    whisper(skill, blob)
    return True

def subscribe_intents():
    # provide an intent that brain-skill can use to send intents
    if not find_brain(skill): return False
    return True

def find_brain(skill=None, quiet=False):
    # TODO: use a more robust and foolproof method
    if not isinstance(skill, MycroftSkill): return None
    bs_path = abspath(skill.__module__).split('/')[:-1]
    bs_path = '/'.join(bs_path) + '/brain-skill'
    global brain_skill_path
    skill.log.debug('brain-skill dumb path = "{}" and smart path = "{}"'.format(bs_path, brain_skill_path))
    if brain_skill_path and not brain_skill_path == bs_path: return False
    if exists(bs_path): return True
    no_brain = 'Brain skill not found. Please install it to continue'
    skill.log.error(no_brain)
    if not quiet: skill.speak(no_brain)
    return False

def set_brain_path(brain_skill):
    # only allows one set; brain-skill should raise an error if it exists and doesn't match, cuz it means another skill interfered
    if not isinstance(brain_skill, MycroftSkill): raise Exception('Only Mycroft skills can set this')
    global brain_skill_path
    if brain_skill_path: return brain_skill_path
    brain_skill_path = dirname(abspath(brain_skill.__module__))
    return False

def announce(skill, words, quiet=False):
    blob = {'target': 'BrainSkill:AnnounceWordsIntent', 'data': {'Words': words}}
    skill.enclosure.speak_text(words)
    if not quiet: whisper(skill, blob)
    return True

def get_auth_confidence(skill):
    if not find_brain(skill): return 0.0
    test_cnt = 0
    fail_cnt = 0
    if not hasattr(skill, 'create_skill_ref') or not inspect.isfunction(skill.create_skill_ref): return 0.0
    skill_clone = skill.create_skill_ref()
    test_cnt += 1
    if not skill.name == skill_clone.name: fail_cnt += 1
    test_cnt += 1
    if not isinstance(skill, MycroftSkill) or not isinstance(skill_clone, MycroftSkill): fail_cnt += 1
    test_cnt += 1
    if not type(skill) == type(skill_clone): fail_cnt += 1
    test_cnt += 1
    if not inspect.getfile(skill.create_skill_ref) == inspect.getfile(skill_clone.create_skill_ref): fail_cnt += 1
    test_cnt += 1
    if not skill._dir == skill_clone._dir: fail_cnt += 1
    test_cnt += 1
    if not abspath(skill.__module__) == abspath(skill.create_skill_ref.__module__): fail_cnt += 1
    return float((test_cnt - fail_cnt) / test_cnt)


brain_skill_ref = None
brain_skill_path = ''

if __name__ == '__main__':
    print('This module is to be used by other Mycroft skills to interact with brain-skill.')
