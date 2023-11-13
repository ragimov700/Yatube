<h1 align="center">Yatube</h1>

**Yatube** — Социальная сеть для публикации постов и картинок. Проект построен на классической MVT архитектуре Django. Предусмотрена пагинация страниц и кэширование, верификация и регистрация данных, работа с пользователями, возможность прикреплять изображения к публикуемым постам. Написаны тесты для проверки сервиса.

---

### Технологии
![Python](https://img.shields.io/badge/Python-%23254F72?style=flat-square&logo=python&logoColor=yellow&labelColor=254f72)
![Django](https://img.shields.io/badge/Django-0C4B33?style=flat-square&logo=django&logoColor=white&labelColor=0C4B33)
![Bootstrap](https://img.shields.io/badge/Bootstrap-712CF9?style=flat-square&logo=bootstrap&logoColor=white&labelColor=712CF9)

### Инструкции по установке:

#### 1. Клонируйте репозиторий

```
git clone git@github.com:ragimov700/Yatube.git
```

#### 2. Создайте и активируйте виртуальное окружение

```
python -m venv venv
source venv/bin/activate
```

#### 3. Установите зависимости

```
pip install -r requirements.txt
```

#### 4. Примените миграции и запустите проект

```
python yatube/manage.py migrate
python yatube/manage.py runserver
```
После чего проект будет доступен по адресу http://localhost:8000/

---
<h5 align="center">Автор проекта: <a href="https://github.com/ragimov700">Sherif Ragimov</a></h5>
