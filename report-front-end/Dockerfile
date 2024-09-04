FROM public.ecr.aws/docker/library/node:18.17.0 AS builder
WORKDIR /frontend
COPY package*.json ./
COPY . .
COPY .env /frontend/.env


ARG AWS_REGION

RUN echo "Current AWS Region: $AWS_REGION"

RUN if [ "$AWS_REGION" = "cn-north-1" ] || [ "$AWS_REGION" = "cn-northwest-1" ]; then \
        sed -i "s/PLACEHOLDER_VITE_LOGIN_TYPE/None/g" .env && \
        npm config set registry https://registry.npmmirror.com && \
        npm install; \
    else \
        sed -i "s/PLACEHOLDER_VITE_LOGIN_TYPE/Cognito/g" .env && \
        npm install; \
    fi

RUN npm run build

FROM public.ecr.aws/docker/library/nginx:1.23-alpine
COPY --from=builder /frontend/dist/ /usr/share/nginx/html/
COPY --from=builder /frontend/.env /.env

COPY docker-entry.sh /docker-entry.sh
RUN chmod +x /docker-entry.sh

EXPOSE 80
ENTRYPOINT ["/docker-entry.sh"]
CMD ["nginx", "-g", "daemon off;"]

# run on linux ec2/lambda/ecs(amd64)
# docker buildx build --platform linux/amd64 --network host -t my_tag .

# run on lambda/macOS(arm64)
# docker buildx build --platform linux/arm64 --network host -t my_tag .