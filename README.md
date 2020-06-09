
# Как развернуть ip_vlan_keeper на сервере
Рекомендуется использовать на сервере и на контрольном хосте Debian 10

## Установить на сервере (выполняется один раз при смене сервера) 

### 1. postgresql

Установливаем
``` sudo apt-get install postgresql ```

Создаём пользователя  ip_vlan_keeper и БД ip_vlan_keeper
``` sudo su postgres ```
``` psql ```
``` CREATE USER ip_vlan_keeper; ```
``` CREATE DATABASE ip_vlan_keeper; ```
``` GRANT ALL ON DATABASE ip_vlan_keeper TO ip_vlan_keeper; ```

Разрешаем устанавливать соединение с базой от любого адреса для контейнера 
В файле
``` /etc/postgresql/11/main/postgresql.conf ```
Устанваливаем 
``` listen_addresses = '*' ```

В файле
``` /etc/postgresql/11/main/pg_hba.conf ```
Добавляем строчку 
``` host    all		all		172.17.0.0/16		md5 ```

Перезапускаем postgresql
``` sudo systemctl restart postgresql ```

### 2. docker
смотри актульную информацию на https://docs.docker.com/engine/install/
```
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

Разрешить запускаться от простого пользователя
``` usermod -a -G docker $USER ```
потом убеждаемся что группа добавилась
``` groups ```
если нет. то прсото обновляем переменные окружения или перезаходим на сервер.

### 3. git
```sudo apt-get install git ```

### 4. rsync
``` sudo apt-get install rsync ```

### 5. sshpass
``` sudo apt-get install sshpass ```

## Установить на контрольном хосте (машина с которой планируется разворачивание ПО)
### 1. ansible
``` sudo apt-get install ansible ```

### 2. sshpass
``` sudo apt-get install sshpass ```

## Пеерд разворачиванием
1. Устанавливаем на контрольный хост git
```sudo apt-get install git ```

2. Клонируем этот репозитарий на контрольный хост
``` git clone https://github.com/Alexander35/ip_vlan_keeper.git ```

3. переходим в папку проекта
``` cd ip_vlan_keeper ```

4. Находим в этом репозитарии в корневом катологе файл .inventory.yml и переименовываем .inventory.yml в inventory.yml. Исправляем значение ansible_host на айпи адрес сервера,  ansible_user - логин пользователя на сервере, ansible_password - пароль от сервера . Эти данные нужны для подключения по ssh.
```
ip_vlan_keeper_server:
  hosts:
      server1:
        ansible_connection: ssh
        ansible_host: "SERVER_IP"
        ansible_user: "SERVER_USER"
        ansible_password: "SERVER_USER_PASSWORD"
```

5. Переименовываем .playbook.yml в playbook.yml. В файле .playbook.yml меняем значение переменной clone_to на каталог, где будет временно размещаться репозитарий проекта на сервере или оставить без изменений. У пользователя из предыдущего пункта должны быть все права на этот каталог.
```
--- 
  - name: Deploy
    connection: ssh
    gather_facts: false
    hosts: all
    vars:
      clone_to: "/tmp/ip_vlan_keeper_repo/"
      git_url: "https://github.com/Alexander35/ip_vlan_keeper.git"
      ip_vlan_keeper_host_address: "{{ansible_host}}"
      ip_vlan_keeper_db_name: "ip_vlan_keeper"
      ip_vlan_keeper_db_user_name: "ip_vlan_keeper"
      ip_vlan_keeper_db_password: "ip_vlan_keeper"
      ip_vlan_keeper_admin_name: "admin"
      ip_vlan_keeper_admin_email: "ad@m.in"
      ip_vlan_keeper_admin_password: "admin"


  
    tasks:
      - git:
          repo: "{{ git_url }}"
          dest: "{{ clone_to }}"
          update: yes

      - name: build image
        command: docker build --tag ip_vlan_keeper {{clone_to}}

      - block:
        - name: stop container
          command: docker stop ip_v_k

        - name: rm container
          command: docker rm ip_v_k

        ignore_errors: yes

      - name: run image
        command: >
          docker run -d -e IP_VLAN_KEEPER_HOST_ADDRESS={{ip_vlan_keeper_host_address}}
          -e IP_VLAN_KEEPER_DB_NAME={{ip_vlan_keeper_db_name}}
          -e IP_VLAN_KEEPER_DB_USER_NAME={{ip_vlan_keeper_db_user_name}}
          -e IP_VLAN_KEEPER_DB_PASSWORD={{ip_vlan_keeper_db_password}}
          -e IP_VLAN_KEEPER_ADMIN_NAME={{ip_vlan_keeper_admin_name}}
          -e IP_VLAN_KEEPER_ADMIN_EMAIL={{ip_vlan_keeper_admin_email}}
          -e IP_VLAN_KEEPER_ADMIN_PASSWORD={{ip_vlan_keeper_admin_password}}
          --publish 8808:8808 --publish 80:80 --name ip_v_k  ip_vlan_keeper
```

## Разворачивание
1. Установить ansible на хосте, с которого предполагается деплой.
за подробной информацией https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html

```
sudo add-apt-repository "deb http://ppa.launchpad.net/ansible/ansible/ubuntu trusty main"
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
sudo apt update
sudo apt install ansible
```

При помощи ansible разворачиваем проект на сервере
``` ansible-playbook -i inventory.yml -vvvv playbook.yml ```
inventory.yml и playbook.yml - это файлы, описанные выше

## Бэкап БД
Записываем задания для бэкапа в cron на сервере
``` crontab -e ```

``` 23 23  */10  *  *  echo SERVER_USER_PASSWORD | sudo -S -u postgres pg_dump ip_vlan_keeper > /backup/folder/server/ip_vlan_keeper_"$(date)".sql && sshpass -p "VAULT_USER_PASSWORD" rsync -avz --remove-source-files /backup/folder/server/ VAULT_USER@VAULT_IP:/backup/folder/vault ```

Чтобы удалить лишние файлы в хранилище рекомендуется в крон на хранилище добавить 
```  23 23  21  *  *   find /backup/folder/vault -type f -not -name '*20*' -delete ```
```  23 23  11  *  *   find /backup/folder/vault -type f -not -name '*10*' -delete ```

## Восстановление БД
Чтобы восстановить БД из бэкапа. нужно закачать один файл с бэкапом с хранилища обратно на сервер
Затем заходим в postgres, удаляем базу и создаём снова пустую
``` sudo su postgres ```
``` psql ```
``` DROP DATABASE ip_vlan_keeper; ```
``` CREATE DATABASE ip_vlan_keeper; ```
``` GRANT ALL ON DATABASE ip_vlan_keeper TO ip_vlan_keeper; ```

Записываем в базу данные из бэкапа
``` echo SERVER_USER_PASSWORD | sudo -S -u postgres psql ip_vlan_keeper < "BACKUP_FILE.sql" ```

### Любые вопросы alexander.ivanov.35@gmail.com
