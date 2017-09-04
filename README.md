# Mycroft Brain Skill Services


## Description
An extension of the Mycroft [brain-skill](https://github.com/skeledrew/brain-skill) to aid communication with other skills

## Installation
- Automatically done by brain-skill
- Manually for skill dev: pip install git+https://github.com/skeledrew/mcbss.git

## Usage
- Ensure brain-skill is installed
- Use the functions to communicate among skills!
  - Use `shout` to broadcast an utterance to all skills
  - Use `whisper` to pass data to a specified skill's intent
  - Pass a skill to `submit_intents` to register its intents with brain-skill
  - Call `subscribe_intents` to get intents from other skills

## To Do
- Fix submit and subscribe functions
- Option to auto install brain-skill if not found