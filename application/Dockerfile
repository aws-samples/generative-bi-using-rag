FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

COPY requirements.txt /app/

ARG AWS_REGION
ENV AWS_REGION=${AWS_REGION}

# Print the AWS_REGION for verification
RUN echo "Current AWS Region: $AWS_REGION"

# Install dependencies using the appropriate PyPI source based on AWS region
RUN if [ "$AWS_REGION" = "cn-north-1" ] || [ "$AWS_REGION" = "cn-northwest-1" ]; then \
        pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple; \
    else \
        pip3 install -r requirements.txt; \
    fi

COPY . /app/

# set streamlit config via env vars
ENV STREAMLIT_SERVER_ENABLE_STATIC_SERVING=false
ENV STREAMLIT_LOGGER_LEVEL="info"
ENV STREAMLIT_CLIENT_TOOLBAR_MODE="viewer"
ENV STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_THEME_BASE="light"

EXPOSE 8501

USER appuser

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Index.py", "--server.port=8501", "--server.address=0.0.0.0"]
