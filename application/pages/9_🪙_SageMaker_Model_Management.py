import json
import logging
import boto3
import streamlit as st
from dotenv import load_dotenv

from nlq.business.model import ModelManagement
from nlq.business.profile import ProfileManagement
from utils.navigation import make_sidebar

logger = logging.getLogger(__name__)


def new_connection_clicked():
    st.session_state.new_sagemaker_mode = True
    st.session_state.update_sagemaker_mode = False
    st.session_state.current_model = None


def model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format):
    connect_flag = False
    connect_info = "-1"
    try:
        if sagemaker_name.startswith("sagemaker."):
            sagemaker_name = sagemaker_name[10:]
        system_prompt = "You are a human friendly conversation assistant."
        user_prompt = "Hello, who are you"
        prompt = prompt_template.replace("SYSTEM_PROMPT", system_prompt).replace("USER_PROMPT", user_prompt)
        input_payload = json.loads(input_payload)
        input_payload_text = json.dumps(input_payload)
        input_payload_text = input_payload_text.replace("\"INPUT\"", json.dumps(prompt))
        sagemaker_client = boto3.client(service_name='sagemaker-runtime', region_name=sagemaker_region)
        response = sagemaker_client.invoke_endpoint(
            EndpointName=sagemaker_name,
            Body=input_payload_text,
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
        connect_flag, connect_info = model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload,
                                                   output_format)
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

    if "samaker_model" not in st.session_state:
        st.session_state.samaker_model = []

    with st.sidebar:
        st.title("SageMaker Model Management")
        st.selectbox("SageMaker Model", [],
                     index=None,
                     placeholder="Please SageMaker Model...", key='current_sagemaker_name')
        if st.session_state.current_sagemaker_name:
            st.session_state.current_model = ModelManagement.get_model_by_id(st.session_state.current_sagemaker_name)
            st.session_state.update_sagemaker_mode = True
            st.session_state.new_sagemaker_mode = False

        st.button('Create New SageMaker Model', on_click=new_connection_clicked)

    if st.session_state.new_sagemaker_mode:
        st.subheader("New SageMaker Model")
        sagemaker_name = st.text_input("SageMaker Endpoint Name")
        sagemaker_region = st.text_input("SageMaker Endpoint Region")
        prompt_template = st.text_area("Prompt Template",
                                       placeholder="Enter prompt template, need contain SYSTEM_PROMPT Placeholder and USER_PROMPT Placeholder. \n For Example: SYSTEM_PROMPT<|im_start|>user\nUSER_PROMPT<|im_end|>\n<|im_start|>assistant\n",
                                       height=200,
                                       help="Enter prompt template, need contain SYSTEM_PROMPT Placeholder and USER_PROMPT Placeholder")
        example_input = {"inputs": "INPUT", "parameters": {"max_new_tokens": 256}}
        input_payload = st.text_area("Mode Input Payload",
                                     placeholder="Enter input payload in JSON dumps str, The input text use INPUT Placeholder. For Example: " + json.dumps(
                                         example_input),
                                     height=200,
                                     help="Enter input payload in JSON dumps str, The input text use INPUT Placeholder")
        output_format = st.text_area("Model Output Format",
                                     placeholder="Enter output format, The output value name is response. For Example: response[0]['generated_text']",
                                     height=100,
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
                ModelManagement.add_model(model_id="sagemaker." + sagemaker_name, model_region=sagemaker_region,
                                          prompt_template=prompt_template, input_payload=input_payload,
                                          output_format=output_format)
                st.success(f"{sagemaker_name} added successfully!")
                st.session_state.samaker_model.append("sagemaker." + sagemaker_name)
                st.session_state.new_connection_mode = False

                with st.spinner('Update Prompt...'):
                    all_profiles = ProfileManagement.get_all_profiles_with_info()
                    for item in all_profiles:
                        profile_name = item
                        profile_value = all_profiles[profile_name]
                        profile_prompt_map = profile_value["prompt_map"]
                        update_prompt_map = {}
                        for each_process in profile_prompt_map:
                            update_prompt_map[each_process] = profile_prompt_map[each_process]
                            update_prompt_map[each_process]["system_prompt"][sagemaker_name] = profile_prompt_map[each_process]["system_prompt"]["sonnet-20240229v1-0"]
                            update_prompt_map[each_process]["user_prompt"][sagemaker_name] = profile_prompt_map[each_process]["user_prompt"]["sonnet-20240229v1-0"]
                        ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                    st.success("Prompt added successfully!")


    elif st.session_state.update_sagemaker_mode:
        st.subheader("Update SageMaker Connection")
        current_model = st.session_state.current_model
        sagemaker_name = st.text_input("SageMaker Endpoint Name", current_model.model_id, disabled=True)
        sagemaker_region = st.text_input("SageMaker Endpoint Region", current_model.model_region, disabled=True)
        prompt_template = st.text_area("Prompt Template", current_model.prompt_template, height=200)
        input_payload = st.text_area("Mode Input Payload", current_model.input_payload, height=200)
        output_format = st.text_area("Model Output Format", current_model.output_format, height=100)
        test_model_connect(sagemaker_name, sagemaker_region, prompt_template, input_payload, output_format)
        if st.button('Update Model Connection', type='primary'):
            ModelManagement.update_model(model_id=sagemaker_name, model_region=sagemaker_region,
                                         prompt_template=prompt_template, input_payload=input_payload,
                                         output_format=output_format)
            st.success(f"{sagemaker_name} updated successfully!")

        if st.button('Delete Model Connection'):
            ModelManagement.delete_model(sagemaker_name)
            st.success(f"{sagemaker_name} deleted successfully!")
            if sagemaker_name in st.session_state.samaker_model:
                st.session_state.samaker_model.remove(sagemaker_name)
            st.session_state.current_model = None
            with st.spinner('Delete Prompt...'):
                all_profiles = ProfileManagement.get_all_profiles_with_info()
                if sagemaker_name.startswith("sagemaker."):
                    sagemaker_name = sagemaker_name[10:]
                for item in all_profiles:
                    profile_name = item
                    profile_value = all_profiles[profile_name]
                    profile_prompt_map = profile_value["prompt_map"]
                    update_prompt_map = {}
                    for each_process in profile_prompt_map:
                        update_prompt_map[each_process] = profile_prompt_map[each_process]
                        if sagemaker_name in update_prompt_map[each_process]["system_prompt"]:
                            del update_prompt_map[each_process]["system_prompt"][sagemaker_name]
                        if sagemaker_name in update_prompt_map[each_process]["user_prompt"]:
                            del update_prompt_map[each_process]["user_prompt"][sagemaker_name]
                    ProfileManagement.update_prompt_map(profile_name, update_prompt_map)
                st.success("Prompt added successfully!")


        st.session_state.update_sagemaker_mode = False

    else:
        st.subheader("SageMaker Model Management")
        st.info('Please select model in the left sidebar.')


if __name__ == '__main__':
    main()
