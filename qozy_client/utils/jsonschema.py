from qozy_client.utils.cli import CliWriter, colorize, Color


class JsonSchemaReader():
    def __init__(self, writer: CliWriter):
        self.writer = writer

    def _ask_enum(self, values, prompt="", default=None, help_text=None):
        self.writer.writeline()
        
        default_index = (values.index(default) + 1) if default else None

        for index, value in enumerate(values, 1):
            self.writer.write("  ")
            self.writer.write(colorize(str(index) + ") ", Color.CYAN))
            self.writer.writeline(value)

        while True:
            answer = self._ask_int(prompt, required=True, default=default_index, help_text=help_text)

            if 0 <= (answer - 1) < len(values):
                return values[answer - 1]

    def _ask_one_of(self, schemas, prompt="", help_text=None):
        self.writer.writeline()

        for index, schema in enumerate(schemas, 1):
            self.writer.write("  ")
            self.writer.write(colorize(str(index) + ") ", Color.CYAN))
            self.writer.writeline(schema["title"])  # how to ensure that each sub-schema has an title?

        while True:
            answer = self._ask_int(prompt or "Type", required=True, help_text=help_text)

            if 0 <= (answer - 1) < len(schemas):
                return self.read(schemas[answer - 1])

    def _ask_int(self, prompt="", default=None, required=False, help_text=None):
        while True:
            answer = self._ask(prompt, default=default, required=required, help_text=help_text)

            try:
                return int(answer)
            except:
                if answer == "" and not required:
                    return None

    def _ask_boolean(self, prompt="", default=True, help_text=None):
        answer_map = {"y": True, "n": False, "": default}

        while True:
            answer = self._ask(prompt + " <y/n>", default="y" if default else "n", help_text=help_text)

            if answer in answer_map:
                return answer_map[answer]

    def _ask_number(self, prompt="", default=None, required=False, help_text=None):
        while True:
            answer = self._ask(prompt, default=default, required=required, help_text=help_text)

            try:
                return int(answer)
            except:
                try:
                    return float(answer)
                except:
                    if answer == "" and not required:
                        return None

    def _ask(self, prompt="", default=None, required=False, help_text=None):
        while True:
            prompt_parts = [prompt]
            if required:
                prompt_parts.append(colorize("*", Color.MAGENTA))
            
            if default:
                prompt_parts.append(colorize(" [" + str(default) + "]", Color.BROWN))

            if help_text:
                prompt_parts.append(colorize(" (" + help_text + ")", Color.GREEN))

            prompt_parts.append(": ")

            for prompt_part in prompt_parts:
                self.writer.write(prompt_part)

            self.writer.writeline()
            self.writer.write("> ")
            
            answer = input()

            if answer:
                return answer
            elif answer == "" and default:
                return default
            elif answer == "" and not required:
                return ""

    def read(self, json_schema, prompt="", required=False):
        description = json_schema.get("description", None)
        default = json_schema.get("default", None)

        if "const" in json_schema:
            return json_schema["const"]
        elif "enum" in json_schema:
            return self._ask_enum(json_schema["enum"], prompt=prompt, default=default, help_text=description)
        elif "oneOf" in json_schema:
            return self._ask_one_of(json_schema["oneOf"], prompt=prompt, help_text=description)
        elif "anyOf" in json_schema:
            return self._ask_one_of(json_schema["anyOf"], prompt=prompt, help_text=description)
        elif json_schema["type"] == "string":
            return self._ask(prompt=prompt, required=required, default=default, help_text=description)
        elif json_schema["type"] in ("number", "integer"):
            return self._ask_number(prompt=prompt, required=required, default=default, help_text=description)
        elif json_schema["type"] == "boolean":
            return self._ask_boolean(prompt=prompt, help_text=description)
        elif json_schema["type"] == "object":
            required_fields = json_schema.get("required", ())

            result = {}

            for field, subschema in json_schema["properties"].items():
                title = subschema.get("title", None)
                is_required = field in required_fields

                sub_result = self.read(subschema, prompt=(title or field), required=is_required)

                if is_required or (not is_required and sub_result != None):
                    result[field] = sub_result

            return result
        elif json_schema["type"] == "array":
            result = []

            self.writer.writeline()
            
            while True:
                add_new = self._ask_boolean("Add entry?")
                if not add_new:
                    break
                result.append(self.read(json_schema["items"]))

            return result
