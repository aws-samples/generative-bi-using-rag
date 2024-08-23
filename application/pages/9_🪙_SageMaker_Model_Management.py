import json

import boto3
import logger
import streamlit as st

from dotenv import load_dotenv
from nlq.business.connection import ConnectionManagement
from nlq.data_access.dynamo_model import ModelConfigEntity, ModelConfigDao
from utils.navigation import make_sidebar


def new_connection_clicked():
    st.session_state.new_connection_mode = True
    st.session_state.update_connection_mode = False
    st.session_state.current_conn_name = None


def model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    connect_flag = False
    connect_info = "-1"
    try:
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        prompt = prompt_template.replace("SYSTEM_PROMPT", system_prompt).replace("USER_PROMPT", user_prompt)
        input_payload_text = json.dumps(input_payload)
        input_payload_text = input_payload_text.replace("INPUT", prompt)
        input_payload = json.loads(input_payload_text)
        sagemaker_client = boto3.client(service_name='sagemaker-runtime', region_name=sagemaker_region)
        response = sagemaker_client.invoke_endpoint(
            EndpointName=sagemaker_name,
            Body=input_payload,
            ContentType="application/json",
        )
        response = json.loads(response.get('Body').read())
        answer = eval(output_format)
        connect_info = answer
        connect_flag = True
    except Exception as e:
        logger.error("Failed to connect: {}".format(e))
        connect_info = str(e)
    return connect_flag, connect_info


def test_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    if st.button('Model Connection Test'):
        if sagemaker_name == '':
            st.error("SageMaker Endpoint is required!")
        elif sagemaker_region == '':
            st.error("SageMaker region is required!")
        elif input_payload == '':
            st.error("Input payload is required!")
        elif output_format == '':
            st.error("Output format is required!")
        connect_flag, connect_info = model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format)
        if connect_flag:
            st.success(f"Connected successfully!")
        else:
            st.error(f"Failed to connect!")
        st.write(connect_info)


def main():
    load_dotenv()

    st.set_page_config(page_title="SageMaker Model Management")
    make_sidebar()

    if 'new_sagemaker_mode' not in st.session_state:
        st.session_state['new_sagemaker_mode'] = False

    if 'update_sagemaker_mode' not in st.session_state:
        st.session_state['update_sagemaker_mode'] = False

    if 'current_model' not in st.session_state:
        st.session_state['current_model'] = None

    with st.sidebar:
        st.title("SageMaker Model Management")
        st.selectbox("SageMaker Model", [],
                     index=None,
                     placeholder="Please SageMaker Model...", key='current_sagemaker_name')
        if st.session_state.current_conn_name:
            st.session_state.current_connection = ConnectionManagement.get_conn_config_by_name(
                st.session_state.current_conn_name)
            st.session_state.update_connection_mode = True
            st.session_state.new_connection_mode = False

        st.button('Create New SageMaker Model', on_click=new_connection_clicked)

    if st.session_state.new_connection_mode:
        st.subheader("New SageMaker Model")
        sagemaker_name = st.text_input("SageMaker Endpoint Name")
        sagemaker_region = st.text_input("SageMaker Endpoint Region")
        prompt_template = st.text_area("Prompt Template", height=200, help="Enter prompt template, need contain SYSTEM_PROMPT Placeholder and USER_PROMPT Placeholder")
        input_payload = st.text_area("Mode Input Payload", height=200, help="Enter input payload in JSON format, The input text use INPUT Placeholder")
        output_format = st.text_input("Model Output Format", height=100,
                                      help="Enter output format, The output value name is response")

        test_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format)

        if st.button('Add Connection', type='primary'):
            if sagemaker_name == '':
                st.error("SageMaker name is required!")
            elif sagemaker_region == '':
                st.error("SageMaker region is required!")
            elif input_payload == '':
                st.error("Input payload is required!")
            elif output_format == '':
                st.error("Output format is required!")
            else:
                model_entity = ModelConfigEntity(model_id="sagemaker." + sagemaker_name, model_region = sagemaker_region, prompt_template=prompt_template, input_payload=input_payload, output_format=output_format)
                ModelConfigDao.add(model_entity)
                st.success(f"{sagemaker_name} added successfully!")
                st.session_state.new_connection_mode = False

    elif st.session_state.update_connection_mode:
        # st.subheader("Update Database Connection")
        # current_conn = st.session_state.current_connection
        # connection_name = st.text_input("Database Connection Name", current_conn.conn_name, disabled=True)
        # db_type = st.selectbox("Database type", db_type_mapping.values(), index=index_of_db_type(current_conn.db_type),
        #                        disabled=True)  # Add more options as needed
        # db_type = db_type.lower()  # Convert to lowercase for matching with db_mapping keys
        # host = st.text_input("Enter host", current_conn.db_host)
        # port = st.text_input("Enter port", current_conn.db_port)
        # user = st.text_input("Enter username", current_conn.db_user)
        # password = st.text_input("Enter password", type="password", value=current_conn.db_pwd)
        # db_name = st.text_input("Enter database name", current_conn.db_name)
        # comment = st.text_input("Enter comment", current_conn.comment)
        #
        # test_connection_view(db_type, user, password, host, port, db_name)
        #
        # if st.button('Update Connection', type='primary'):
        #     ConnectionManagement.update_connection(connection_name, db_type, host, port, user, password, db_name,
        #                                            comment)
        #     st.success(f"{connection_name} updated successfully!")
        #
        # if st.button('Delete Connection'):
        #     ConnectionManagement.delete_connection(connection_name)
        #     st.success(f"{connection_name} deleted successfully!")
        #     st.session_state.current_connection = None

        st.session_state.update_connection_mode = False

    else:
        st.subheader("SageMaker Model Management")
        st.info('Please select model in the left sidebar.')


if __name__ == '__main__':
    main()
