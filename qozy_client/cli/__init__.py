import subprocess
import sys
import os
import argparse
import json
from tempfile import NamedTemporaryFile
from qozy_client.client import Client, Channel
from qozy_client.utils.cli import CliWriter, colorize, italic, Color, colored_bool
from qozy_client.utils.jsonschema import JsonSchemaReader


writer = CliWriter(sys.stdout)


def pretty_json(object):
    return json.dumps(object, indent=2)


def pretty_print_json(object):
    print(pretty_json(object))


class BridgeCLI():
    TYPE_NAME = "bridge"

    def __init__(self, client: Client):
        self.client = client

    def execute(self, options):
        bridge = self.client.bridge(options.id)

        if options.command == "settings":
            if options.settings_command == "schema":
                pretty_print_json(
                    bridge.settings_schema
                )
            elif options.settings_command == "set":
                if options.interactive:
                    jsonschema_reader = JsonSchemaReader(writer)
                    settings = jsonschema_reader.read(bridge.settings_schema)
                else:
                    temporary_file = NamedTemporaryFile(delete=False, mode="w")
                    temporary_file.write(pretty_json(bridge.settings))
                    temporary_file.close()

                    # open editor
                    subprocess.run(["vim", temporary_file.name])

                    with open(temporary_file.name) as f:
                        settings = f.read()

                    os.unlink(temporary_file.name)

                    try:
                        settings = json.loads(settings)
                    except:
                        writer.alert("Couldn't parse settings")
                        return

                try:
                    bridge.set_settings(settings)
                    writer.success("Updated settings for bridge \"{:s}\"".format(options.id))
                except:
                    writer.alert("Couldn't update settings for bridge \"{:s}\"".format(options.id))
            else:
                pretty_print_json(
                    bridge.settings
                )
        elif options.command == "remove":
            bridge.remove()

            writer.success("Bridge \"{:s}\" removed.".format(bridge.id))
        else:
            things = list(bridge.things())

            dict_writer = writer.dict()
            dict_writer.add("Id", bridge.id)
            dict_writer.add("Active", bridge.active)
            dict_writer.add("Vendor", bridge.vendor_prefix)
            dict_writer.add("Things", len(things))
            dict_writer.write()

            if len(things) > 0:
                writer.headline("Things")

                table = writer.table("ID", "ONLINE", "CHANNELS")
                for thing in things:
                    table.row(
                        thing.id,
                        colored_bool(thing.online()),
                        str(len(thing.channels()))
                    )

                table.write()

    @staticmethod
    def create_argument_parser(parser):
        parser.add_argument("id")

        subparsers = parser.add_subparsers(dest="command")

        settings_parser = subparsers.add_parser("settings")

        settings_parser_subparsers = settings_parser.add_subparsers(dest="settings_command")
        settings_parser_subparsers.add_parser("schema")

        settings_parser_set = settings_parser_subparsers.add_parser("set")
        settings_parser_set.add_argument("--interactive", "-i", action="store_true")

        subparsers.add_parser("remove")


class BridgesCLI():
    TYPE_NAME = "bridges"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        if options.command == "add":
            try:
                bridge = self.client.add_bridge(options.type)
                writer.success("Added bridge, id \"{:s}\"".format(bridge.id))
            except:
                writer.alert("Could not add bridge")
        elif options.command == "types":
            bridge_types = self.client.bridge_types()

            list_writer = writer.list()

            for bridge_type in bridge_types:
                list_writer.add(bridge_type)

            list_writer.write()
        else:
            # list

            bridges = self.client.bridges()

            table = writer.table("ID", "ACTIVE", "VENDOR", "THINGS")

            for bridge in bridges:
                table.row(
                    bridge.id,
                    colored_bool(bridge.active),
                    bridge.vendor_prefix,
                    str(len(list(bridge.things())))
                )

            table.write()

    @staticmethod
    def create_argument_parser(parser):
        subparsers = parser.add_subparsers(dest="command")

        add_parser = subparsers.add_parser("add")
        add_parser.add_argument("type")

        subparsers.add_parser("types")


class ThingCLI():
    TYPE_NAME = "thing"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        thing = self.client.thing(options.id)

        if options.command == "set":
            try:
                channel = thing.channel(options.channel)

                if channel.type == "SwitchChannel":
                    value = True if options.value == "on" else False
                else:
                    value = json.loads(options.value)

                thing.channel(options.channel).apply(value)

                writer.success("Applied value \"{:s}\" to \"{:s}\", channel \"{:s}\"".format(options.value, options.id, options.channel))
            except Exception as e:
                writer.alert("Couldn't set value, reason: {:s}".format(str(e)))
        elif options.command == "remove":
            thing.remove()
            writer.success("Thing \"{:s}\" removed.".format(thing.id))
        elif options.command == "name":
            thing.set_name(options.name)
            writer.success("Thing \"{:s}\" renamed to \"{:s}\".".format(thing.id, thing.name))
        elif options.command == "tags":
            for tag in options.add:
                thing.add_tag(tag)

            for tag in options.remove:
                thing.remove_tag(tag)

            writer.headline("Tags")
            tag_writer = writer.list(thing.tags)
            tag_writer.write()
        else:
            dict_writer = writer.dict()
            dict_writer.add("Id", thing.id)
            dict_writer.add("Bridge", thing.bridge_id)
            dict_writer.add("Online", colored_bool(thing.online()))
            dict_writer.add("Channels", str(len(thing.channels())))
            dict_writer.write()

            channel_writer = writer.table("NAME", "SENSOR", "VALUE")

            writer.writeline()

            for channel in thing.channels().values():
                channel_writer.row(channel.channel, colored_bool(channel.sensor), channel.value)

            channel_writer.write()

            if thing.tags:
                writer.headline("Tags")
                tag_writer = writer.list(thing.tags)
                tag_writer.write()

    @staticmethod
    def create_argument_parser(parser):
        parser.add_argument("id")

        subparsers = parser.add_subparsers(dest="command")

        set_parser = subparsers.add_parser("set")
        set_parser.add_argument("channel")
        set_parser.add_argument("value")

        subparsers.add_parser("remove")

        name_parser = subparsers.add_parser("name")
        name_parser.add_argument("name")

        tags_parser = subparsers.add_parser("tags")
        tags_parser.add_argument("--add", "-a", dest="add", nargs="?", action="append", default=[])
        tags_parser.add_argument("--remove", "-r", dest="remove", nargs="?", action="append", default=[])


class ThingsCLI():
    TYPE_NAME = "things"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        things = self.client.things(filter_tags=options.tags)

        if options.command == "tags":
            tags = set()

            for thing in things:
                tags = tags.union(thing.tags)

            writer.list(tags).write()
        elif options.command == "scan":
            self.client.scan()
        else:
            table = writer.table("ID", "NAME", "ONLINE", "CHANNELS")
            for thing in things:
                table.row(
                    thing.id,
                    italic("<not set>") if not thing.has_name() else thing.name,
                    colored_bool(thing.online()),
                    str(len(thing.channels()))
                )

            table.write()

    @staticmethod
    def create_argument_parser(parser):
        subparsers = parser.add_subparsers(dest="command")
        subparsers.add_parser("tags")

        subparsers.add_parser("scan")

        parser.add_argument("--tag", "-t", dest="tags", nargs="?", action="append", default=[])


class NotificationsCLI():
    TYPE_NAME = "notifications"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        table = writer.table("CREATED", "TITLE", "SUMMARY", "DISMISSABLE")

        for notification in self.client.notifications():
            table.row(
                notification.created,
                notification.title,
                notification.summary,
                colored_bool(notification.dismissable),
            )

        table.write()

    @staticmethod
    def create_argument_parser(parser):
        pass


class TriggersCLI():
    TYPE_NAME = "triggers"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        table = writer.table("ID", "EVENT NAME")

        for trigger in self.client.triggers():
            table.row(
                trigger.id,
                trigger.event_name,
            )

        table.write()

    @staticmethod
    def create_argument_parser(parser):
        pass


class RulesCLI():
    TYPE_NAME = "rules"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        if options.command == "add":
            try:
                rule = self.client.add_rule()
                writer.writeline(rule.id)
            except:
                raise  # todo
        else:
            table = writer.table("ID", "NAME", "TRIGGERS", "ACTIONS")

            for rule in self.client.rules():
                table.row(
                    rule.id,
                    rule.name,
                    str(len(rule.triggers())),
                    str(len(rule.actions)),
                )

            table.write()

    @staticmethod
    def create_argument_parser(parser):
        subparsers = parser.add_subparsers(dest="command")

        subparsers.add_parser("add")


class RuleCLI():
    TYPE_NAME = "rule"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        rule = self.client.rule(options.id)

        if options.command == "add-trigger":
            trigger_id = options.trigger_id

            trigger = self.client.trigger(trigger_id)

            try:
                rule.add_trigger(trigger)
                writer.success("Successfully added trigger \"{:s}\" to rule \"{:s}\".".format(trigger.id, rule.id))
            except:
                raise  # todo
        else:
            triggers = rule.triggers()

            dict_writer = writer.dict()
            dict_writer.add("Id", rule.id)
            dict_writer.add("Name", rule.name)
            dict_writer.add("Triggers", len(triggers))
            dict_writer.add("Actions", len(rule.actions))
            dict_writer.write()

            if len(triggers) > 0:
                writer.headline("Triggers")

                trigger_list = writer.list()
                for trigger in rule.triggers():
                    trigger_list.add(trigger.id)

                trigger_list.write()

    @staticmethod
    def create_argument_parser(parser):
        parser.add_argument("id")

        subparsers = parser.add_subparsers(dest="command")

        add_trigger_parser = subparsers.add_parser("add-trigger")
        add_trigger_parser.add_argument("trigger_id")


class PluginsCLI():
    TYPE_NAME = "plugins"

    def __init__(self, client):
        self.client = client

    def execute(self, options):
        plugins = self.client.plugins()

        writer.list(plugins).write()

    @staticmethod
    def create_argument_parser(parser):
        pass


def main():
    cli_classes = {
        BridgeCLI.TYPE_NAME: BridgeCLI,
        BridgesCLI.TYPE_NAME: BridgesCLI,
        ThingCLI.TYPE_NAME: ThingCLI,
        ThingsCLI.TYPE_NAME: ThingsCLI,
        NotificationsCLI.TYPE_NAME: NotificationsCLI,
        TriggersCLI.TYPE_NAME: TriggersCLI,
        RuleCLI.TYPE_NAME: RuleCLI,
        RulesCLI.TYPE_NAME: RulesCLI,
        PluginsCLI.TYPE_NAME: PluginsCLI,
    }

    parser = argparse.ArgumentParser(description="Qozy command line interface")
    parser.add_argument("--host", type=str, default=os.getenv("QOZY_REMOTE_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=os.getenv("QOZY_REMOTE_PORT", 9876))
    parser.add_argument("--no-colors", action="store_true", dest="no_colors")

    subparsers = parser.add_subparsers(dest="group")
    subparsers.required = True

    for group_name, group_cls in cli_classes.items():
        subparser = subparsers.add_parser(group_name)
        group_cls.create_argument_parser(subparser)

    opts = parser.parse_args()

    try:
        client = Client(opts.host, opts.port)
    except ConnectionRefusedError:
        writer.alert("Could not connect to Qozy daemon at {}:{}".format(opts.host, opts.port))
        exit(1)

    if opts.no_colors:
        writer.disable_colors()

    cli_class = cli_classes[opts.group]
    cli = cli_class(client)
    cli.execute(opts)


if __name__ == "__main__":
    main()
