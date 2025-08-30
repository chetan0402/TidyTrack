FROM nginx:latest
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./html /usr/share/nginx/html
EXPOSE 5001
CMD ["nginx", "-g", "daemon off;"]