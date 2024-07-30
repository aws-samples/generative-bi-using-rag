FROM public.ecr.aws/docker/library/node:18.17.0 AS builder
WORKDIR /frontend
COPY package*.json ./
RUN npm install  --registry=https://registry.npmmirror.com
COPY . .
RUN npm run build

FROM public.ecr.aws/docker/library/nginx:1.23-alpine
COPY --from=builder /frontend/dist/ /usr/share/nginx/html/

COPY ./nginx.template /etc/nginx/conf.d

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# run on linux ec2/lambda/ecs(amd64)
# docker buildx build --platform linux/amd64 --network host -t my_tag .

# run on lambda/macOS(arm64)
# docker buildx build --platform linux/arm64 --network host -t my_tag .
