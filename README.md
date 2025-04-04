# ovos-skill-my-tasmota-mqtt
## Introduction
This OVOS skill is used to control IoT devices that are operated with the Tasmota firmware. Actually only MQTT (unencrypted, QoS 0) is considered as the communication protocol. The default syntax %prefix%/%topic%/ as well as %topic%/%prefix%/ (= setoption19 resp. homeassistant mode) is available. The skill is currently originally designed for use in German and is case sensitive for topics.

# Examples
"Switch on radio" where 'radio' is a specific mqtt name of a single device.
"What are the values from garden" to receive sensor values of a device.
"Tell me the timers from chicken lights" to hear a report of the on/off switching times. 
"Switch on heating in workshop" where a device in a room is called under specific conditions (paragraph Hivemind).

## Configuration/setup
### Basic settings
It's a clean JSON file. Be carefully. It does not forgive mistakes and delets all!
```
{
    "__mycroft_skill_firstrun": false,
    "protocol": "mqtt",
    "user": "admin",
    "password": "joker",
    "mqtthost": "IP.OF.MQTT.HOST",
    "mqttport": 1883,
    "tasmota_mqtt_modus": "homeassistant",
    "capitalization": true,
    ...
}
```
Line 1: standard from OVOS
Line 2: choose "mqtt" or "http" (actually not implemented)
Line 3 and line 4: standard user and password for using web interface, change if necessessary - only fpr http communication (actually not installed)
Line 5: Ip of MQTT host
Line 6: MQTT port
Line 7: Choice between the %prefix%/%topic%/ ("default") or %topic%/%prefix%/ ("homeassistant")
Line 8: if using MQTT names beginning with capitals use 'true' else 'false' 

## Device settings:
```
{
    ...,
    "devices": {
        "device_01": {
            "ip": "IP.OF.TASMOTA.DEVICE_1",
            "mqtt_name": "mqtt name",
            "sensor": "sensor_name_1"
        },
        "device_01": {
            "ip": "IP.OF.TASMOTA.DEVICE_2",
            "mqtt_name": "mqtt name",
            "sensor": ""
        }
    },
    "nicknames": {
        "nickname_1": {
            "realname": "device_01",
            "line": "1"
        }
    },
    ...
}
```
"devices": Do not change! It's a keyword.
"device_01" A free name for a Tasmota device. Normally fetched from speech-to-text (STT) service.
"ip": It's a preparation for http use. Not necessary for MQTT so can be "".
"mqtt_name": recommended for using MQTT. It's used for the '%topic%' key of MQTT protocol.
"sensor": If device has a sensor sensor's name is necessary, else "".
"nicknames": Do not change! It's a keyword too. Nicknames are usefull for multiple channels (lines) devices as Sonoff CH4 for example. Nicknames are mainly abbreviations for multi channels switches.
"nickname_1": Maybe "Computer"
"realname": refers to an existing name from "devices" section, maybe "multiswitch"
"line": one of the 2 or 4 lines of "multiswitch" device

Additionally are there intents which recognizes speeches like "switch on multiswitch line 4". With a nickname like "computer" you can replace "multiswitch line 4" with a single word.

## Language settings
At the time this skill was programmed automatic translations were not very well developed. May be there a more intelligent strategies today. I've decide to use "hard" coded translation for some words and values.
```
{
    ...,
        "lang_specifics": {
        "decimal_char": ",",
        "ON": "on",
        "OFF": "off",
        "1": "on",
        "0": "off",
        "timer_specifics": {
            "single_days": [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday"
            ],
            "days_repeat": [
                "sundays",
                "mondays",
                "tuesdays",
                "wednesdays"
                "thursdays",
                "fridays",
                "saturdays"
            ],
            "day_groups": {
                "1000001": "weekend",
                "0111110": "monday to friday",
                "0111111": "working days monday to saturday",
                "1111111": "every day"
            },
            "timer_repetition": [
                "no, one time",
                "yes "
            ]
        }
    },
    "log_level": "INFO"
}
```
"decimal_char": standard of Tasmota is using a dot. European countries usually use ",". It's better for correct speaking of text-to-speech (TTS) service.
"ON" / "OFF" / "1" / "0": replace with the words which are used in your language
"timer_specifics": It's a keyword. Do not change!
"single_days": It's a keyword too. Do not change!
["Sunday" ... "Saturday"]: replace with the day names of your language. **Do not change the order.** Tasmota (and this skill) uses positions and values 1/0 for designate or identify a specific day and validity.
"days_repeat": your words for "every Sunday", "every Tuesday" ...
"day_groups": replace if neccessary.
"timer_repetition": replace with words for a single event or repeated actions.
"log_level": an OVOS key to control content of skills.log. Values are "INFO", "WARNING" or "DEBUG". Only "INFO" messages are used in this skill.

## Deutsche Version
Dieser Skill dient der Steuerung von IoT-Geräten, die mit der Firmware Tasmota betrieben werden. Als Kommunikationsprotokoll ist ausschließlich MQTT (unverschlüsselt, QoS 0) berücksichtigt. Zur Auswahl steht die default Syntax %prefix%/%topic%/ sowie %topic%/%prefix%/ (= setoption19/homeassistant Modus). Der Skill ist derzeit besonders auf die Nutzung in Deutsch ausgelegt und berücksichtigt die Groß- und Kleinschreibung von topics. Folgendes  Modul muss installiert werden: paho-mqtt.

## Configuration/Setup
### MQTT-Settings
* IP des MQTT-Brokers eingeben
* Portnummer des MQTT-Brokers eingeben (1883 ist vorbelegt)

### Tasmota FullTopicSyntax
* Auswahl zwischen dem Typ %prefix%/%topic%/ (vorbelegt) oder %topic%/%prefix%/ (Homeassstant bzw. setoption19 Typ)

### Capitalization
Falls die Topics mit einem Großbuchstaben anfangen, dann diese Checkbox wählen. Es werden dann ALLE Topics (= devices, = Geräte) mit einem führenden Großbuchstaben erzeugt. Das bedeutet gleichzeitig, dass kein weiterer Großbuchstabe z. B. wie TH10/TH16 oder POW NICHT vorkommen darf.

Dies bezieht sich allerdings auch auf die Schreibweise der auszuwertenden Sensordaten (Datei SensorKeywords.voc) 

Weitere Hinweise im Wiki

