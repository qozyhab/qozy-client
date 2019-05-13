import json
import requests


class Client():
    VERSION = "0.1"
    URL_SCHEME = "http://{host:s}:{port:d}/api"

    def __init__(self, host, port):
        self.base_url = self.URL_SCHEME.format(host=host, port=port)

        info = self.get("")

        if info["version"] != self.VERSION:
            raise Exception("Incompatible Versions {server_version:s} (client version {client_version:s}".format(str(info["version"]), client_version=self.VERSION))

    def get(self, path, params={}):
        response = requests.get(self.base_url + path, params=params)

        if response.status_code != 200:
            raise Exception(response.text)

        data = json.loads(response.text)

        return data

    def post(self, path, params={}, payload=None):
        response = requests.post(self.base_url + path, params=params, json=payload)

        if response.status_code != 200:
            raise Exception(response.text)

        data = json.loads(response.text)

        return data

    def put(self, path, params={}, payload=None):
        response = requests.put(self.base_url + path, params=params, json=payload)

        if response.status_code != 200:
            raise Exception(response.text)

        data = json.loads(response.text)

        return data

    def delete(self, path, params={}, payload=None):
        response = requests.delete(self.base_url + path, params=params, json=payload)

        if response.status_code != 200:
            raise Exception(response.text)

        data = json.loads(response.text)

        return data

    def close(self):
        pass

    def bridge(self, id):
        bridge = self.get("/bridges/{:s}".format(id))

        return Bridge(
            self,
            bridge["id"],
            bridge["vendorPrefix"],
            bridge["instanceId"],
            bridge["settingsSchema"],
            bridge["settings"],
        )

    def bridges(self):
        bridges = self.get("/bridges", params={"expand": True})

        for bridge in bridges.values():
            yield Bridge(
                self,
                bridge["id"],
                bridge["vendorPrefix"],
                bridge["instanceId"],
                bridge["settingsSchema"],
                bridge["settings"],
            )

    def bridge_types(self):
        return self.get("/bridges/types")

    def add_bridge(self, type):
        bridge_id = self.post("/bridges", payload=type)

        return self.bridge(bridge_id)

    def thing(self, id):
        thing = self.get("/things/{thing_id:s}".format(thing_id=id))

        result_thing = Thing(
            self,
            thing["id"],
            thing["name"],
            thing["bridge_id"],
            thing["tags"],
        )

        result_thing._channels = {
            channel_name:
            Channel(
                self,
                result_thing,
                channel["id"],
                channel["name"],
                channel["sensor"],
                channel["type"],
                channel["value"],
            )
            for channel_name, channel in thing["channels"].items()
        }

        return result_thing

    def tags(self):
        return self.get("/things/tags")

    def scan(self):
        return self.get("/things/scan")

    def things(self, filter_tags=None):
        things = self.get("/things", params={"expand": True, "tag": filter_tags})
        
        for thing in things.values():
            result_thing = Thing(
                self,
                thing["id"],
                thing["name"],
                thing["bridge_id"],
                thing["tags"],
            )

            result_thing._channels = {
                channel_name:
                Channel(
                    self,
                    result_thing,
                    channel["id"],
                    channel["name"],
                    channel["sensor"],
                    channel["type"],
                    channel["value"],
                )
                for channel_name, channel in thing["channels"].items()
            }

            yield result_thing

    def notifications(self):
        notifications = self.get("/notifications")

        for notification in notifications:
            yield Notification(
                self,
                notification["contextId"],
                notification["type"],
                notification["dismissable"],
                notification["created"],
                notification["title"],
                notification["summary"],
            )

    def triggers(self):
        triggers = self.get("/triggers")

        for trigger in triggers.values():
            yield Trigger(
                self,
                trigger["id"],
                trigger["eventName"],
            )

    def trigger(self, id):
        trigger = self.get("/triggers/{trigger_id:s}".format(trigger_id=id))

        return Trigger(
            self,
            trigger["id"],
            trigger["eventName"],
        )

    def rules(self):
        rules = self.get("/rules")
        
        for rule in rules.values():
            result_rule = Rule(
                self,
                rule["id"],
                rule["name"],
                rule["actions"],
            )

            result_rule._triggers = {
                trigger["id"]:
                Trigger(self, trigger["id"], trigger["eventName"])
                for trigger in rule["triggers"]
            }

            yield result_rule

    def rule(self, id):
        rule = self.get("/rules/{rule_id:s}".format(rule_id=id))

        result_rule = Rule(
            self,
            rule["id"],
            rule["name"],
            rule["actions"],
        )

        result_rule._triggers = {
            trigger["id"]:
            Trigger(self, trigger["id"], trigger["eventName"])
            for trigger in rule["triggers"]
        }

        return result_rule

    def add_rule(self):
        rule_id = self.post("/rules")
        
        return self.rule(rule_id)

    def plugins(self):
        return self.get("/plugins")


class TriggerList(list):
    def __init__(self, rule, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rule = rule


class Rule():
    def __init__(self, client, id, name, actions):
        self.client = client
        
        self.id = id
        self.name = name
        self.actions = actions
        self._triggers = {}

    def triggers(self):
        return TriggerList(self, self._triggers.values())

    def add_trigger(self, trigger):
        return self.client.post("/rules/{rule_id:s}/triggers".format(rule_id=self.id), payload=trigger.id)


class Trigger():
    def __init__(self, client, id, event_name):
        self.client = client
        
        self.id = id
        self.event_name = event_name


class Notification():
    def __init__(self, client, context_id, type, dismissable, created, title, summary):
        self.client = client
        
        self.context_id = context_id
        self.type = type
        self.dismissable = dismissable
        self.created = created
        self.title = title
        self.summary = summary

    def dismiss(self):
        if self.dismissable:
            pass


class Thing():
    def __init__(self, client, id, name, bridge_id, tags):
        self.client = client

        self.id = id
        self.name = name
        self.bridge_id = bridge_id
        self.tags = tags
        self._channels = {}

    def online(self):
        return self.client.get("/things/{thing_id:s}/online".format(thing_id=self.id))

    def set_name(self, name):
        response = self.client.put("/things/{thing_id:s}/name".format(thing_id=self.id), payload=name)

        if response:
            self.name = name
            
            return True

        return False

    def has_name(self):
        return self.name != None

    def bridge(self):
        bridge = self.client.get("/bridges/{:s}".format(self.bridge_id))

        return Bridge(
            self.client,
            bridge["id"],
            bridge["vendorPrefix"],
            bridge["instanceId"],
            bridge["settingsSchema"],
            bridge["settings"],
        )

    def add_tag(self, tag):
        self.tags = self.client.post("/things/{thing_id:s}/tags".format(thing_id=self.id), payload=tag)

    def remove_tag(self, tag):
        self.tags = self.client.delete("/things/{thing_id:s}/tags".format(thing_id=self.id), payload=tag)

    def channel(self, name):
        return self._channels[name]

    def channels(self):
        return self._channels

    def remove(self):
        self.client.delete("/things/{thing_id:s}".format(thing_id=self.id))


class Channel():
    def __init__(self, client, thing, id, channel, sensor, type, value):
        self.client = client

        self.thing = thing
        self.id = id
        self.channel = channel
        self.sensor = sensor
        self.type = type
        self.value = value

    def apply(self, value):
        self.client.put("/things/{thing_id:s}/channels/{channel:s}".format(thing_id=self.thing.id, channel=self.channel), payload=value)


class ThingList(list):
    def __init__(self, bridge, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bridge = bridge


class Bridge():
    def __init__(self, client, id, vendor_prefix, instance_id, settings_schema, settings):
        self.client = client

        self.id = id
        self.vendor_prefix = vendor_prefix
        self.instance_id = instance_id
        self.settings_schema = settings_schema
        self.settings = settings

    def things(self):
        things = self.client.get("/bridges/{bridge_id:s}/things".format(bridge_id=self.id))

        result = ThingList(self)

        for thing in things.values():
            result_thing = Thing(
                self.client,
                thing["id"],
                thing["name"],
                thing["bridge_id"],
                thing["tags"],
            )

            result_thing._channels = {
                channel_name:
                Channel(
                    self.client,
                    result_thing,
                    channel["id"],
                    channel["name"],
                    channel["sensor"],
                    channel["type"],
                    channel["value"],
                )
                for channel_name, channel in thing["channels"].items()
            }

            result.append(result_thing)
        
        return result

    @property
    def active(self):
        return self.client.get("/bridges/{bridge_id:s}/running".format(bridge_id=self.id))

    def set_settings(self, settings):
        try:
            self.client.put("/bridges/{bridge_id:s}/settings".format(bridge_id=self.id), payload=settings)
        except:
            raise

    def remove(self):
        self.client.delete("/bridges/{bridge_id:s}".format(bridge_id=self.id))
