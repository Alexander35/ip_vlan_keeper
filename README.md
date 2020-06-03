
# Как развернуть ip_vlan_keeper на сервере

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
``` sudo apt-get install docker ``` 

Разрешить запускаться от простого пользователя
``` usermod -a -G docker $USER ```

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

1. Находим в этом репозитарии в корневом катологе файл inventory.yml и исправляем значение ansible_host на айпи адрес сервера,  ansible_user - логин пользователя на сервере, ansible_password - пароль от сервера . Эти данные нужны для подключения по ssh 
``` ip_vlan_keeper_server:
  hosts:
      server1:
        ansible_connection: ssh
        ansible_host: "IP_OF_THE_SERVER"
        ansible_user: "SERVER_USER"
        ansible_password: "SERVER_USER_PASSWORD"
```

2. В файле playbook.yml меняем значение переменной clone_to на каталог, где будет временно размещаться репозитарий проекта на сервере. У пользователя из предыдущего пункта должны быть все права на этот каталог.
```
--- 
  - name: Deploy
    connection: ssh
    gather_facts: false
    hosts: all
    vars:
      clone_to: FOLDER_WITH_OUR_REPO_ON_THE_SERVER
      git_url: https://github.com/Alexander35/ip_vlan_keeper.git
  
    tasks:
      - git:
          repo: https://github.com/Alexander35/ip_vlan_keeper.git
          dest: "{{ clone_to }}"
          update: yes

      - block:
        - name: stop container
          command: docker stop ip_v_k

        - name: rm container
          command: docker rm ip_v_k

        ignore_errors: yes

      - name: build image
        command: docker build --tag ip_vlan_keeper {{clone_to}}

      - name: run image
        command: docker run -d  --publish 8808:8808 --publish 80:80 --name ip_v_k  ip_vlan_keeper
```

## Разворачивание
При помощи ansible разворачиваем проект на сервере
``` ansible-playbook -i inventory.yml -vvvv playbook.yml ```
inventory.yml и playbook.yml - это файлы, описанные выше

## Бэкап БД
Записываем задания для бэкапа в cron на сервере
``` crontab -e ```

``` 23 23  */10  *  *  echo SERVER_USER_PASSWORD | sudo -S -u postgres pg_dump ip_vlan_keeper > /backup/folder/server/ip_vlan_keeper_"$(date)".sql && sshpass -p "VAULT_USER_PASSWORD" rsync -avz --remove-source-files /backup/folder/server/ VAULT_USER@VAULT_IP:/backup/folder/vault```

Чтобы удалить лишние файлы в хранилище рекомендуется в крон на хранилище добавить 
```  23 23  21  *  *   find . -type f -not -name '*20*' -delete```

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
