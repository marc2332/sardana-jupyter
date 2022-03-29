from jupyter_kernel_test import msgspec_v5
from jsonschema import Draft4Validator, validators
from datetime import datetime


def main():
    def get_msg_content_validator(msg_type, version_minor):
        """
        Reimplementation of
        https://github.com/jupyter/jupyter_kernel_test/blob/eecfdbf3fede60e7cfed887ca3a682c2c69a7cf2/jupyter_kernel_test/msgspec_v5.py#L15
        that also supports datetime types
        """
        frag = msgspec_v5.schema_fragments[msg_type]
        schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "description": "{} message contents schema".format(msg_type),
            "type": "object",
            "properties": {},
            "additionalProperties": version_minor
            > msgspec_v5.protocol_version[1],
        }
        schema.update(frag)

        if "required" not in schema:
            # Require all keys by default
            schema["required"] = sorted(schema["properties"].keys())

        validator = Draft4Validator(schema)

        def is_datetime(_, inst):
            return isinstance(inst, datetime)

        date_check = validator.TYPE_CHECKER.redefine("datetime", is_datetime)

        Validator = validators.extend(validator, type_checker=date_check)

        return Validator(schema=schema)

    msgspec_v5.get_msg_content_validator = get_msg_content_validator

    """
    Also add the needed schema for some Jupyter Channel messages
    They are not supported by default as stated in
    https://github.com/jupyter/jupyter_kernel_test#coverage
    """

    msgspec_v5.schema_fragments["comm_open"] = {
        "properties": {
            "data": {
                "state": {
                    "type": {
                        "enum": [{"type": "string"}, {"type": "datetime"}]
                    }
                },
            },
        }
    }

    msgspec_v5.schema_fragments["comm_msg"] = {
        "properties": {
            "data": {
                "method": "string",
                "state": {
                    "value": "number",
                },
                "buffer_paths": "array",
                "comm_id": "string",
            },
        }
    }
