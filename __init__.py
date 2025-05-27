from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
from ovos_bus_client.session import SessionManager
from threading import Event
import time
import json
import paho.mqtt.client as mqtt
#

DEFAULT_SETTINGS = {
    "__mycroft_skill_firstrun": "False",
    "protocol": "mqtt",
    "mqtthost": "IP.OF.MQTT.SERVER",
    "mqttport": 1883,
    "tasmota_mqtt_modus": "default",
    "capitalization": "True",
    "devices": {
        "device_01": {
            "ip": "IP.OF.TASMOTA.DEVICE",
            "mqtt_name": "mqtt name",
            "sensor": ""
        }
    },
    "nicknames": {
        "computer": {
            "realname": "multischalter",
            "line": "1"
        },
        "zusatzbildschirm": {
            "realname": "multischalter",
            "line": "3"
        },
        "zusatzgeräte": {
            "realname": "multischalter",
            "line": "4"
        }
    },
    "lang_specifics": {
        "decimal_char": ".",
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
                "wednesdays",
                "thursdays",
                "fridays",
                "saturdays"
            ],
            "day_groups": {
                "1000001": "Weekend",
                "0111110": "Monday to Friday",
                "0111111": "working days Monday to Saturday",
                "1111111": "every day"
            },
            "timer_repetition": [
                "no, one time ",
                "yes "
            ]
        }
    },
    "log_level": "INFO"
}
global line
line = None

class TasmotaMQTT(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # be aware that below is executed after `initialize`
        self.override = True

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(
            internet_before_load=False,
            network_before_load=False,
            gui_before_load=False,
            requires_internet=False,
            requires_network=False,
            requires_gui=False,
            no_internet_fallback=True,
            no_network_fallback=True,
            no_gui_fallback=True,
        )
    
    def initialize(self):
        #from template
        self.settings.merge(DEFAULT_SETTINGS, new_only=True)
        self.settings_change_callback = self.on_settings_changed
        #from joergz2
        self.mqtthost = self.settings.get("mqtthost", "localhost")
        self.mqttport = self.settings.get("mqttport", 1883)
        self.devices = self.settings.get("devices", None)
        self.nicknames = self.settings.get("nicknames", None)
        self.lang_specifics = self.settings.get("lang_specifics", None)
        self.tasmota_mqtt_modus = self.settings.get("tasmota_mqtt_modus", "default")
        if self.lang_specifics:
            self.day_groups = self.lang_specifics["timer_specifics"]["day_groups"]
            self.single_days = self.lang_specifics["timer_specifics"]["single_days"]
            self.timer_repetition = self.lang_specifics["timer_specifics"]["timer_repetition"]
        self.capitalization = self.settings.get("capitalization", False)

    def on_settings_changed(self):
        """This method is called when the skill settings are changed."""

#Helpers
    #checks before executing
    def check_device_exists(self, device):
        device_wrong = device
        if len(device.split()) > 1:
            device = device.split()
            for i in device:
                if i in self.nicknames:
                    line = self.nicknames[device]['line']
                    device = self.nicknames[device]['realname']
                    device = {"dev_name": i, "mqtt_name": self.devices[i]['mqtt_name'], "sensor": self.devices[i]['sensor'], "ip": self.devices[i]['ip'], "line": line}
                    return device
                if i in self.devices:
                    device = {"dev_name": i, "mqtt_name": self.devices[i]['mqtt_name'], "sensor": self.devices[i]['sensor'], "ip": self.devices[i]['ip']}
                    return device
        if device in self.nicknames:
            line = self.nicknames[device]['line']
            device = self.nicknames[device]['realname']
            device = {"dev_name": device, "mqtt_name": self.devices[device]['mqtt_name'], "sensor": self.devices[device]['sensor'], "ip": self.devices[device]['ip'], "line": line}
            return device
        if device in self.devices:
            device = {"dev_name": device, "mqtt_name": self.devices[device]['mqtt_name'], "sensor": self.devices[device]['sensor'], "ip": self.devices[device]['ip']}
            return device
        else:
            LOG.debug("From CHECK_DEVICE_EXISTS " + str(device_wrong) + " not found in devices.")
            self.speak_dialog('device_error',{'device': device_wrong})

    def check_line(self, line):
        line = "power" + str(line)
        return line
    
    #checks and evaluations after executing
    def language_check(self,value):
        value = self.lang_specifics[value]
        return value
    
    def separate_power_line(self,values_dict):
        if "POWER" in values_dict:
            return "POWER"
        if "POWER1" in values_dict:
            return "POWER1"
        if "POWER2" in values_dict:
            return "POWER2"
        if "POWER3" in values_dict:
            return "POWER3"
        if "POWER4" in values_dict:
            return "POWER4"
        else:
            return None
    
    def evaluate_power_state_from_status_line(self,power_value):
        power_value = int(power_value)
        if power_value > 15:
            answer = self.dialog_renderer.render('power_lines_out_of_range')
            return answer
        divisor = [8, 4, 2, 1]
        line = len(divisor)
        answer = ""
        if power_value == 0:
            part_answer = self.dialog_renderer.render('power_lines_all_off')
            answer += part_answer
            return answer
        for i in range(line):
            result = power_value / divisor[i]
            if result < 1:
                line -= 1
                continue
            if result >= 1:
                part_answer = self.dialog_renderer.render('power_line_on', {"line": line})
                power_value -= divisor[i]
                answer = part_answer + answer
                line -= 1
        return answer
        
    def evaluate_timer_informations(self, values):
        answer = ""
        days = ""
        if values['Timers'] == "OFF":
            answer = self.dialog_renderer.render('timers_inactive')
            return answer
        for timer_nr in range(1, 17):
            timer = "Timer" + str(timer_nr)
            if values[timer]['Enable'] == 1:
                timer_time = values[timer]['Time']
                timer_days =  values[timer]['Days']
                timer_action = values[timer]['Action']; timer_action = self.lang_specifics[str(timer_action)]
                timer_repeat = values[timer]['Repeat']; timer_repeat = self.timer_repetition[timer_repeat]
                if str(timer_days) in self.day_groups.keys():
                    days = self.day_groups[str(timer_days)]
                    part_answer = self.dialog_renderer.render('group_days', {'timer_nr': timer_nr, "timer_time": timer_time, "timer_action": timer_action, "days": days, "timer_repeat": timer_repeat})
                    answer = answer + part_answer
                    continue
                for single_day in range(7):
                    if str(timer_days[single_day]) == "0":
                        continue
                    if str(timer_days[single_day]) != "0":
                        days = days + self.single_days[single_day] + ", "
                answer = answer + days
            self.dialog_renderer.render('group_days', {'timer_nr': timer_nr, "timer_time": timer_time, "timer_action": timer_action, "days": days, "timer_repeat": timer_repeat})
        return answer


    def evaluate_values_dict(self,values_dict,device):
        device = device.lower()
        device = self.check_device_exists(device)
        dev_name = device['dev_name']
        sensor_name = device['sensor']
        if 'Timers' in values_dict.keys():
            #values = values_dict["Timers"]
            answer = self.evaluate_timer_informations(values_dict)
            return answer
        if "POWER" in values_dict.keys() or "POWER1" in values_dict.keys() or \
        "POWER2" in values_dict.keys() or "POWER3" in values_dict.keys() or \
        "POWER4" in values_dict.keys():
            key = self.separate_power_line(values_dict)
            if key[-1] == '1' or key[-1] =='2' or key[-1] == '3' or key[-1] == '4':
                line = str(key[-1])
            else:
                line = '1'
            state = values_dict[key]
            state = self.language_check(state)
            answer = self.dialog_renderer.render('switch_state', {'device': dev_name, 'state': state, 'line': line})
            return answer

        #Sensor informations
        if "StatusSNS" in values_dict.keys():
            #solarpower
            if "MT631" in values_dict["StatusSNS"]:
                total_in = str(values_dict["StatusSNS"]["MT631"]["Total_in"]).replace('.', self.lang_specifics["decimal_char"])
                total_out = str(values_dict["StatusSNS"]["MT631"]["Total_out"]).replace('.', self.lang_specifics["decimal_char"])
                power_cur = str(values_dict["StatusSNS"]["MT631"]["Power_cur"]).replace('.', self.lang_specifics["decimal_char"])
                if int(power_cur) <= 0:
                    power_cur = int(power_cur)*(-1)
                    answer = self.dialog_renderer.render('solar_plus', {'total_out': total_out, "total_in": total_in, "power_cur": power_cur})
                    return answer
                if int(power_cur) > 0:
                    answer = self.dialog_renderer.render('solar_minus', {'total_out': total_out, "total_in": total_in, "power_cur": power_cur})
                    return answer
    
            #energy sensor informations
            if "ENERGY" in values_dict["StatusSNS"]:
                enrg_total = str(values_dict["StatusSNS"]["ENERGY"]["Total"]).replace('.', self.lang_specifics["decimal_char"])
                enrg_today = str(values_dict["StatusSNS"]["ENERGY"]["Today"]).replace('.', self.lang_specifics["decimal_char"])
                enrg_current = str(values_dict["StatusSNS"]["ENERGY"]["Current"]).replace('.', self.lang_specifics["decimal_char"])
                enrg_voltage = str(values_dict["StatusSNS"]["ENERGY"]["Voltage"]).replace('.', self.lang_specifics["decimal_char"])
                answer = self.dialog_renderer.render('energy_information', {'enrg_total': enrg_total, "enrg_today": enrg_today, "enrg_current": enrg_current, "enrg_voltage": enrg_voltage})
                return answer
            
            #temp and humidity sensor
            if sensor_name != "":
                LOG.debug("From EVALUATE_VALUES_DICT: " + str(values_dict))
                temp = str(values_dict["StatusSNS"][sensor_name]["Temperature"]).replace('.', self.lang_specifics["decimal_char"])
                hum = str(values_dict["StatusSNS"][sensor_name]["Humidity"]).replace('.', self.lang_specifics["decimal_char"])
                dew = str(values_dict["StatusSNS"][sensor_name]["DewPoint"]).replace('.', self.lang_specifics["decimal_char"])
                answer = self.dialog_renderer.render('weather_information', {'temp': temp, 'hum': hum, 'device': dev_name})
                #answer = self.translator.translate(answer, source="de-de", target="fr-fr") #just a test
                return answer
            
        #status general
        if "Power" in values_dict["Status"]:
            power_value = values_dict["Status"]["Power"]
            answer = self.evaluate_power_state_from_status_line(power_value)
            return answer

        #timer informations

#MQTT Execution
    def handle_mqtt_connection(self, mqtt_cmd, command_action, subscribe_str, device):
        self.mqttc = mqtt.Client("Ovos")
        self.mqttc.connect(self.mqtthost,self.mqttport)
        self.mqttc.on_message = self.on_message
        self.mqttc.loop_start()
        self.mqttc.subscribe(subscribe_str)
        self.mqttc.publish(mqtt_cmd, command_action)
        time.sleep(1)
        self.mqttc.disconnect()

    def execute_mqtt(self,device,command,command_action,line=None):
        LOG.debug("Info aus EXECUTE_MQTT: " +str(device) +", " + str(line))
        mqtt_name = device['mqtt_name']
        #if self.capitalization:
            #device =  device.capitalize()
        if self.tasmota_mqtt_modus == "homeassistant":
            if line:
                mqtt_cmd = mqtt_name + "/cmnd/" + command + line
            else:
                mqtt_cmd = mqtt_name + "/cmnd/" + command
            subscribe_str = "+/stat/#"
        else:
            if line:
                mqtt_cmd = "cmnd/" + mqtt_name +"/" + command + line
            else:
                mqtt_cmd = "cmnd/" + mqtt_name +"/" + command
            subscribe_str = "stat/+/#"
        LOG.debug("From end of EXECUTE_MQTT: " + str(mqtt_cmd))
        self.handle_mqtt_connection(mqtt_cmd, command_action, subscribe_str, device)

    def execute_http(self, device_ip, command, option):
        address = "http://" + str(device_ip) + "/cm?&user=" + self.user + "&password=" + self.password + "&cmnd=" + str(command) + " " + str(option)
        response = self.http.request('GET', address)
        data = response.data
        values = json.loads(data)
        return values

    
    #intents
    @intent_handler("power.on.intent")
    def power_on_intent(self,message):
        sess = SessionManager.get(message)
        self.dialog_to_speak = None
        self.event = Event()
        device = message.data.get('device').lower().replace(' ','_')
        device = self.check_device_exists(device)
        if "line" in device:
            line = device['line']
        else:
            line = message.data.get('line','1')
        command = "Power"
        command_action = "1"
        self.execute_mqtt(device,command,command_action,line)
        self.event.wait()
        self.speak_dialog(self.dialog_to_speak)

    @intent_handler("power.off.intent")
    def power_off_intent(self,message):
        sess = SessionManager.get(message)
        self.dialog_to_speak = None
        self.event = Event()
        device = message.data.get('device').lower().replace(' ','_')
        device = self.check_device_exists(device)
        if "line" in device:
            line = device['line']
        else:
            line = message.data.get('line','1')
        command = "Power"
        command_action = "0"
        self.execute_mqtt(device,command,command_action,line)
        self.event.wait()
        self.speak_dialog(self.dialog_to_speak)


    @intent_handler("power.state.intent")
    def power_state_intent(self,message):
        sess = SessionManager.get(message)
        self.dialog_to_speak = None
        self.event = Event()
        device = message.data.get('device').lower().replace(' ','_')
        device = self.check_device_exists(device)
        if "line" in device:
            line = device['line']
        else:
            line = message.data.get('line','1')
        command = "Status"
        command_action = ""
        self.execute_mqtt(device,command,command_action,line)
        self.event.wait()
        self.speak_dialog(self.dialog_to_speak)

    @intent_handler("sensor.intent")
    def fetch_sensor_data(self, message):
        sess = SessionManager.get(message)
        self.dialog_to_speak = None
        self.event = Event()
        device = message.data.get('device').lower().replace(' ','_')
        LOG.debug("Device from FETCH_SENSOR_DATA: " + str(device))
        device = self.check_device_exists(device)
        if "line" in device:
            line = device['line']
        else:
            line = message.data.get('line','1')
        command = "Status"
        command_action = "10"
        LOG.debug("Command line from  FETCH_SENSOR_DATA: " +str(device) +", " +str(command) + ", " +str(command_action))
        self.execute_mqtt(device,command,command_action)
        self.event.wait()
        self.speak_dialog(self.dialog_to_speak)
    
    @intent_handler("timers.intent")
    def fetch_timer_informations(self, message):
        sess = SessionManager.get(message)
        self.dialog_to_speak = None
        self.event = Event()
        device = message.data.get('device').lower().replace(' ','_')
        device = self.check_device_exists(device)
        command = "Timers"
        command_action = ""
        self.execute_mqtt(device,command,command_action)
        self.event.wait()
        self.speak_dialog(self.dialog_to_speak)

    #globals
    def on_message(self,mqttclient,userdata,msg):
        splitTopic = msg.topic.split('/')
        if self.tasmota_mqtt_modus == "default":
            device = splitTopic[1]
        if self.tasmota_mqtt_modus == "homeassistant":
            device = splitTopic[0]
        values = str(msg.payload.decode())
        values_dict = json.loads(values)
        LOG.debug("From ON_MESSAGE: " + str(values_dict))
        self.dialog_to_speak = self.evaluate_values_dict(values_dict,device)
        self.event.set()
        return


    def stop(self):
        """Optional action to take when "stop" is requested by the user.
        This method should return True if it stopped something or
        False (or None) otherwise.
        If not relevant to your skill, feel free to remove.
        """
        pass
