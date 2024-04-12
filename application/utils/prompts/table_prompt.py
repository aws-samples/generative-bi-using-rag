table_prompt_dict = {}
table_prompt_dict['haiku-20240307v1-0']="""

"""

table_prompt_dict['sonnet-20240229v1-0']="""

"""

class TablePromptMapper:
    def __init__(self):
        self.variable_map = table_prompt_dict

    def get_variable(self, name):
        return self.variable_map.get(name)