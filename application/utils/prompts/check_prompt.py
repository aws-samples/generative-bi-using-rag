import logging

logger = logging.getLogger(__name__)

required_syntax_map = {
    'text2sql': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': ['dialect'],
            'llama3-70b-instruct-0': ['dialect'],
            'haiku-20240307v1-0': ['dialect'],
            'sonnet-20240229v1-0': ['dialect'],
            'sonnet-3-5-20240620v1-0': ['dialect']
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': [
                'dialect_prompt',
                'sql_schema',
                'examples',
                'ner_info',
                'sql_guidance',
                'question'
            ],
            'llama3-70b-instruct-0': [
                'dialect_prompt',
                'sql_schema',
                'examples',
                'ner_info',
                'sql_guidance',
                'question'
            ],
            'haiku-20240307v1-0': [
                'dialect_prompt',
                'sql_schema',
                'examples',
                'ner_info',
                'sql_guidance',
                'question'
            ],
            'sonnet-20240229v1-0': [
                'dialect_prompt',
                'sql_schema',
                'examples',
                'ner_info',
                'sql_guidance',
                'question'
            ],
            'sonnet-3-5-20240620v1-0': [
                'dialect_prompt',
                'sql_schema',
                'examples',
                'ner_info',
                'sql_guidance',
                'question'
            ]
        }
    },
    'intent': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': ['question'],
            'llama3-70b-instruct-0': ['question'],
            'haiku-20240307v1-0': ['question'],
            'sonnet-20240229v1-0': ['question'],
            'sonnet-3-5-20240620v1-0': ['question']
        },
    },
    'knowledge': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': ['question'],
            'llama3-70b-instruct-0': ['question'],
            'haiku-20240307v1-0': ['question'],
            'sonnet-20240229v1-0': ['question'],
            'sonnet-3-5-20240620v1-0': ['question']
        }
    },
    'agent': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': ['table_schema_data',
                                        'sql_guidance',
                                        'example_data'
                                        ],
            'llama3-70b-instruct-0': ['table_schema_data',
                                      'sql_guidance',
                                      'example_data'],
            'haiku-20240307v1-0': ['table_schema_data',
                                   'sql_guidance',
                                   'example_data'],
            'sonnet-20240229v1-0': ['table_schema_data',
                                    'sql_guidance',
                                    'example_data'],
            'sonnet-3-5-20240620v1-0': ['table_schema_data',
                                    'sql_guidance',
                                    'example_data']
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': ['question'],
            'llama3-70b-instruct-0': ['question'],
            'haiku-20240307v1-0': ['question'],
            'sonnet-20240229v1-0': ['question'],
            'sonnet-3-5-20240620v1-0': ['question']
        }
    },
    'agent_analyse': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': [
                'question',
                'data'
            ],
            'llama3-70b-instruct-0': [
                'question',
                'data'
            ],
            'haiku-20240307v1-0': [
                'question'
                'data'
            ],
            'sonnet-20240229v1-0': [
                'question',
                'data'
            ],
            'sonnet-3-5-20240620v1-0': [
                'question',
                'data'
            ]
        }
    },
    'data_summary': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': [
                'question',
                'data'
            ],
            'llama3-70b-instruct-0': [
                'question',
                'data'
            ],
            'haiku-20240307v1-0': [
                'question'
                'data'
            ],
            'sonnet-20240229v1-0': [
                'question',
                'data'
            ],
            'sonnet-3-5-20240620v1-0': [
                'question',
                'data'
            ]
        }
    },
    'data_visualization': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': [
                'question',
                'data'
            ],
            'llama3-70b-instruct-0': [
                'question',
                'data'
            ],
            'haiku-20240307v1-0': [
                'question'
                'data'
            ],
            'sonnet-20240229v1-0': [
                'question',
                'data'
            ],
            'sonnet-3-5-20240620v1-0': [
                'question',
                'data'
            ]
        }
    },
    'suggestion': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': ['question'],
            'llama3-70b-instruct-0': ['question'],
            'haiku-20240307v1-0': ['question'],
            'sonnet-20240229v1-0': ['question'],
            'sonnet-3-5-20240620v1-0': ['question']
        }
    },
    'query_rewrite': {
        'system_prompt': {
            'mixtral-8x7b-instruct-0': [],
            'llama3-70b-instruct-0': [],
            'haiku-20240307v1-0': [],
            'sonnet-20240229v1-0': [],
            'sonnet-3-5-20240620v1-0': []
        },
        'user_prompt': {
            'mixtral-8x7b-instruct-0': ['chat_history', 'question'],
            'llama3-70b-instruct-0': ['chat_history', 'question'],
            'haiku-20240307v1-0': ['chat_history', 'question'],
            'sonnet-20240229v1-0': ['chat_history', 'question'],
            'sonnet-3-5-20240620v1-0': ['chat_history', 'question']
        }
    }
}


def check_prompt_syntax(system_prompt, user_prompt, prompt_type, model_id):
    system_prompt_required_syntax = required_syntax_map.get(prompt_type, {}).get('system_prompt', {}).get(model_id)
    user_prompt_required_syntax = required_syntax_map.get(prompt_type, {}).get('user_prompt', {}).get(model_id)

    for system_syntax in system_prompt_required_syntax:
        if f'{{{system_syntax}}}' not in system_prompt:
            return False

    for user_syntax in user_prompt_required_syntax:
        if f'{{{user_syntax}}}' not in user_prompt:
            return False

    return True


def find_missing_prompt_syntax(system_prompt, user_prompt, prompt_type, model_id):
    system_prompt_required_syntax = required_syntax_map.get(prompt_type, {}).get('system_prompt', {}).get(model_id)
    user_prompt_required_syntax = required_syntax_map.get(prompt_type, {}).get('user_prompt', {}).get(model_id)

    missing_system_prompt_syntax = []
    missing_user_prompt_syntax = []

    for system_syntax in system_prompt_required_syntax:
        if f'{{{system_syntax}}}' not in system_prompt:
            missing_system_prompt_syntax.append(f'{{{system_syntax}}}')

    for user_syntax in user_prompt_required_syntax:
        if f'{{{user_syntax}}}' not in user_prompt:
            missing_user_prompt_syntax.append(f'{{{user_syntax}}}')

    return missing_system_prompt_syntax, missing_user_prompt_syntax
