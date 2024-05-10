FROM public.ecr.aws/docker/library/node:18.20.0 AS builder
COPY . /tmp/frontend/
RUN cd /tmp/frontend/ && npm ci && npm run build

FROM public.ecr.aws/docker/library/nginx:1.23-alpine
COPY --from=builder /tmp/frontend/build/ /usr/share/nginx/public/
COPY nginx-config/ /etc/nginx/
EXPOSE 8800
CMD ["nginx", "-g", "daemon off;"]

# run on linux ec2/lambda/ecs(amd64)
# docker buildx build --platform linux/amd64 --network host -t my_tag.

# run on lambda/macOS(arm64)
# docker buildx build --platform linux/arm64 --network host -t my_tag.
