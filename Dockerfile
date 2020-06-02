FROM python:3.6-slim

RUN apt-get update
Run apt-get install -y apt-utils gcc apt-utils python3-psycopg2 libpq-dev nginx python-dev git nodejs npm

RUN mkdir -p /ip_vlan_keeper

WORKDIR /ip_vlan_keeper

ADD . /ip_vlan_keeper

RUN pip install --trusted-host pypi.python.org -r requirements.txt

RUN npm install -g npm
RUN git clone https://github.com/Alexander35/ip_vlan_keeper_frontend.git
RUN rm -rf public
RUN mkdir public

RUN pip install uwsgi
RUN echo yes | python manage.py collectstatic

RUN usermod -a -G www-data root

EXPOSE 8808
EXPOSE 80

ENTRYPOINT  cd ip_vlan_keeper_frontend && npm install && npm run build && mv build/* ../public && cd .. && ln -s /ip_vlan_keeper/ip_vlan_keeper_nginx.conf /etc/nginx/sites-enabled/ && rm -rf /etc/nginx/sites-enabled/default && /etc/init.d/nginx start && python manage.py makemigrations --noinput && python -u manage.py migrate --noinput && python -u manage.py createfirstuser
CMD uwsgi --ini ip_vlan_keeper_uwsgi.ini --daemonize /ip_vlan_keeper/uwsgi.log
