FROM cvdnc_img_base

WORKDIR /app

COPY . .
RUN chmod 777 setup.sh

EXPOSE 5005
CMD ["cvwrapperstart"]