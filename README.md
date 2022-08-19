# SmartApp Framework

**SmartApp Framework** - это Python-фреймворк, который позволяет создавать смартапы для виртуальных ассистентов Салют. 


## Оглавление
   * [Конфигурация](#Конфигурация)
     * [Фреймворк и смартапы](#Фреймворк)
     * [Инструменты фреймворка](#Инструменты)
     * [Рекомендованные требования](#Рекомендованные)
   * [Настройка фреймворка](#Настройка)
     * [Обновление фреймворка](#Обновление)
     * [Установка фреймворка](#Установка)
     * [Создание проекта](#Создание)
     * [Тестирование онлайн](#Тестирование) 
     * [Тестирование офлайн](#Тестирование)    
   * [Документация](#Документация)
   * [Обратная связь](#Обратная)

____

# Конфигурация

## Фреймворк и смартапы

Смартап - это приложение для виртуального ассистента Салют. С помощью смартапов пользователи могут вызвать такси, узнать погоду, управлять устройствами умного дома, записаться в салон красоты и совершить прочие действия, которые можно доверить ассистенту. 

Виртуальный ассистент понимает текущие намерения пользователя и для каждой его реплики подбирает соответствующий запрос на выполнение ([интент](#TODO: вставить ссылку)). Поведение смартапа для различных интентов описывается с помощью сценариев. Интенты и сценарии связываются через смартапы, написанные на SmartApp Framework. 


## Инструменты фреймворка

Фреймворк содержит следующие инструменты:

* инструменты для создания сценариев;
* решения для автоматического тестирования;
* демо-приложение для просмотра примеров реализации; 
* готовые механизмы для слот-филлинга и извлечения сущностей из текста. 


## Рекомендованные требования

* Linux, Mac OS или Windows (необходима установка [Conda](https://docs.conda.io/en/latest/)).
* 512 МБ свободной памяти.
* Python 3.6.8 - 3.9.6.

____



# Настройка фреймворка

## Обновление фреймворка

Для перехода на новую версию фреймворка выполните в терминале следующие команды:

```bash
python3 -m pip uninstall -y smart-app-framework
python3 -m pip install git+https://github.com/salute-developers/smart_app_framework@main
```

При переходе на версию фреймворка >=1.0.7.rc4 со старым смартапом необходимо в директории смартапа из файла ```static/.text_normalizer_resources/static_workdata.json``` удалить строки 'Ё на Е'.

## Установка фреймворка

Для установки фреймворка выполните в терминале следующую команду:

```bash
python3 -m pip install git+https://github.com/salute-developers/smart_app_framework@main
```

## Создание проекта

Для создания проекта выполните в терминале следующую команду:
```bash
python3 -m smart_kit create_app <YOUR_APP_NAME>
```
После этого в текущей директории появится каталог с проектом. Он уже содержит в себе всё необходимое для запуска минимального приложения, включая базовый сценарий hello_scenario. Описание сценариев и форм можно найти в <YOUR_APP_NAME>/static/references/.


## Тестирование онлайн

Для тестирования онлайн вам понадобится мобильное приложение Салют или собственное устройство, на котором будет запускаться смартап. Для такого тестирования:

1. Запустите в терминале dev сервер:

```bash
python3 manage.py run_app
```

2. Передайте в интернет порт. Для этого потребуется внешний IP-адрес. Если у вас его нет, воспользуйтесь специальными сервисами (например, Ngrok).
3. Зарегистрируйтесь в кабинете разработчика - [SmartApp Studio](#TODO: вставить ссылку).
4. Создайте в [SmartApp Studio](#TODO: вставить ссылку) свой смартап. 
5. Перейдите в настройки смартапа и укажите в поле "Настройки вебхука" адрес вашего сервера. Сохраните изменения.
6. Запустите свой смартап с помощью фразы "Запусти <имя приложения>". 

В терминале должны появиться записи о входящем сообщении, а ассистент ответит приветствием согласно сценарию hello_scenario.


## Тестирование офлайн

Ниже представлен пример команды для терминала при тестировании офлайн и пример ответа, который выводится на экране: 
```console
localhost:~$ python <YOUR_APP_NAME>/manage.py local_testing
Текущий сценарий: hello_scenario
Привет! Введите help или ? для вызова списка команд.
> set intent run_app // смена интента на другой. По умолчанию имя сценария совпадает с именем интента
intent = run_app
> Привет
pronounceText: Как тебя зовут?
```


____



# Документация

Вы можете ознакомиться с подробной документацией по работе со SmartApp Framework в [справочнике разработчика](#TODO: вставить ссылку).

# Разработка

## Запуск тестов

Для тестов используется `unittests`.
Тесты находятся в директории `tests`

```shell
python -m unittest discover -s tests -v
```

# Обратная связь

C вопросами и предложениями пишите нам по адресу [#TODO: вставить почту] или вступайте в 
наш Telegram канал - [SmartMarket Community](https://t.me/smartmarket_community). 
