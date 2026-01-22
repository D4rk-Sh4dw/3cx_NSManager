FROM nginx:alpine

# Install openssl for cert generation
RUN apk add --no-cache openssl bash

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy config template and entrypoint
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY entrypoint.sh /docker-entrypoint.d/99-ssl-gen.sh

RUN chmod +x /docker-entrypoint.d/99-ssl-gen.sh
