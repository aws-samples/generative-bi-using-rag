guidance_prompt_dict = {}
guidance_prompt_dict['haiku-20240307v1-0'] = """
you should always keep the words from question unchanges when writing SQL. \n\n
"""

guidance_prompt_dict['sonnet-20240229v1-0'] = """

"""

class GuidancePromptMapper:
    def __init__(self):
        self.variable_map = guidance_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)