import re


class MPRealParser:

    def parse(self, filepath):

        with open(filepath, "r") as f:
            content = f.read()

        components = []

        blocks = re.findall(r'component\s+(.*?)\s+end', content, re.DOTALL)

        for block in blocks:

            comp = {}

            id_match = re.search(r'^(\w+)', block.strip())
            if id_match:
                comp["id"] = id_match.group(1)

            type_match = re.search(r'type:\s*(\w+)', block)
            if type_match:
                comp["type"] = type_match.group(1)

            inputs_match = re.search(r'inputs:\s*(.*)', block)
            if inputs_match:
                comp["inputs"] = [x.strip() for x in inputs_match.group(1).split(",")]

            input_match = re.search(r'input:\s*(\w+)', block)
            if input_match:
                comp["inputs"] = [input_match.group(1)]

            path_match = re.search(r'path:\s*(.*)', block)
            if path_match:
                comp["path"] = path_match.group(1).strip().replace('"', '')

            keys_match = re.search(r'keys:\s*(.*)', block)
            if keys_match:
                comp["keys"] = [x.strip() for x in keys_match.group(1).split(",")]

            components.append(comp)

        return components