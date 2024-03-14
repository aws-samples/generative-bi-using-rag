import streamlit as st
import pandas as pd
from nlq.business.connection import ConnectionManagement
from utils.apis import query_from_sql_pd


class NLQChain:

    def __init__(self, profile):
        self.question = ''
        self.profile = profile
        self.retrieve_samples = []
        self.generated_sql_response = ''
        self.executed_result_df: pd.DataFrame | None = None
        self.visualization_config_change: bool = False

    def set_question(self, question):
        if self.question != question:
            self.retrieve_samples = []
            self.generated_sql_response = ''
            self.executed_result_df = None
        self.question = question

    def get_question(self):
        return self.question

    def get_profile(self):
        return self.profile

    def get_retrieve_samples(self):
        return self.retrieve_samples

    def set_retrieve_samples(self, retrieve_samples):
        self.retrieve_samples = retrieve_samples

    def set_generated_sql_response(self, sql_response):
        self.generated_sql_response = sql_response

    def get_generated_sql_response(self):
        return self.generated_sql_response

    def get_generated_sql(self):
        try:
            return self.generated_sql_response.split('```sql')[1].split('```')[0].replace('\n', ' ', 1).strip()
        except IndexError:
            raise Exception("No SQL found in the LLM's response")

    def get_generated_sql_explain(self):
        return self.generated_sql_response.split('```')[-1]

    def set_executed_result_df(self, df):
        self.executed_result_df = df

    def get_executed_result_df(self, force_execute_query=True):
        if self.executed_result_df is None and force_execute_query:
            db_url = st.session_state['profiles'][self.profile]['db_url']
            if not db_url:
                conn_name = st.session_state['profiles'][self.profile]['conn_name']
                db_url = ConnectionManagement.get_db_url_by_name(conn_name)
            self.executed_result_df = query_from_sql_pd(
                p_db_url=db_url,
                query=self.get_generated_sql())

        return self.executed_result_df

    def set_visualization_config_change(self, change_value=True):
        self.visualization_config_change = change_value

    def is_visualization_config_changed(self):
        return self.visualization_config_change

