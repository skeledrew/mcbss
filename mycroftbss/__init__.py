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


from os.path import exists, dirname

from mycroft.messagebus.message import Message


def whisper(this=None, msg=None):
    # direct query to a particular skill/intent; should prob not register
    if not find_brain(this): return False
    pattern = 'call intent (?P<Intent>.+) in skill (?P<Skill>.+) with data (?P<Data>.+)( and context )?(?P<Context>.+)?'
    if not this and not msg: return None #pattern
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
    if not find_brain(this): return False
    if not this: return None  # prevent addition as ability

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
    blob = {'target': 'BrainSkill:Accept000Intent', data: intents}
    whisper(skill, blob)
    return True

def subscribe_intents():
    # provide an intent that brain-skill can use to send intents
    if not find_brain(skill): return False
    return True

def find_brain(skill, quiet=False):
    bs_path = skill._dir.split('/')[:-1]
    bs_path = '/'.join(bs_path) + '/brain-skill'
    skill.log.debug('brain-skill path = {}'.format(bs_path))
    if exists(bs_path): return True
    no_brain = 'Brain skill not found. Please install it to continue'
    skill.log.error(no_brain)
    if not quiet: skill.speak(no_brain)
    return False

if __name__ == '__main__':
    print('This module is to be used by other Mycroft skills to interact with brain-skill.')
