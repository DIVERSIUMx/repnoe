# Установка
Для установмки требуется `git` а так же `python` версии **3.11**.


### Клонируйте репозиторий

```
git clone https://github.com/DIVERSIUMx/repnoe
cd repnoe
```

### Создайте виртуальное окружение (рекомендуется)

linux:
```
python -m venv .venv
source .venv/bin/activate
```

windows:
```
python -m venv .venv
.venv\Scripts\activate.bat
```

windows (powershell):
```
python -m venv .venv
.venv\Scripts\activate.ps1
```

### Установите зависимости

```
pip install -r requirements.txt
```

### Запустите сервер

```
python main.py
```
