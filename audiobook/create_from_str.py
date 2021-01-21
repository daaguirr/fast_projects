# -*- coding: utf-8 -*-
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer
from environs import Env

env = Env()
env.read_env()

text = """
"""

with env.prefixed("CREATE_"):
    subscription_key = env.str("SUBSCRIPTION_KEY")
    region = env.str("REGION")

speech_config = SpeechConfig(subscription=subscription_key, region=region)
synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)

lines = text.split('\n')
current = ''
current_letter = 'a'
cap = '1'


def process(string):
    ssml_string = f"""
    <speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="es-MX">
        <voice name="es-MX-DaliaNeural">
            <prosody rate="0.9">
                <break time="200ms"/>
                    {string}
            </prosody>
        </voice>
    </speak>
    
    """
    result = synthesizer.speak_ssml(ssml_string)

    stream = AudioDataStream(result)
    stream.save_to_wav_file(f"out/rebeca{cap}{current_letter}.wav")


with open('out/process.txt', 'w') as f:
    for line in lines:
        new_size = len(line)
        if len(current) + new_size > 7250:
            print(current_letter)
            f.write(current)
            f.write("\n----------------------------------------------------------\n")
            process(current)
            current = ''
            current_letter = chr(ord(current_letter) + 1)

        current = current + '\n' + line
    print(current_letter)
    f.write(current)
    process(current)
