_Примечание_:
Понятия не имею, как это нормально запускать и разрабатывать на винде.
В целом, можно просто миграции ручками накатывать на базу, а запускать также.
## Как мы работаем
0. Не рекомендую создавать папку _data в корне. Туда потом докер швырнет БД.
1. Eсли мы хотим запустить без докера в pycharm:<br>
а. Создайте БД (здесь используется постгрес). Для теста создайте пользователя vims с паролем vims. Все это на БД vims
в схеме e_code<br>
Везде в настройках указан порт 15432 (а не родной 5432)<br>
б. Установите dbmate:
https://github.com/amacneil/dbmate#installation
*если у вас винда - накатывайте миграции из папки vims_code/db/migrations ручками<br>
При этом dbmate смотрит на .env файл, а точнее на переменную среды DATABASE_URL<br>
в. make migrate - мигрирует все что есть<br>
г. Во время запуска не забудьте прописать в переменные среды 
PG_HOST=postgresql+asyncpg://vims:vims@localhost:15432/vims
д. Запускаем файл __main__.py в vims_code. Я еще ставлю корень в WORKING_DIRECTORY в настройках запуска.
2. Чтобы поднять на серваке дев-версию (ВНИМАНИЕ! ТАМ ЕСТЬ ОТКРЫТЫЕ ПОРТЫ! ХОТИТЕ ЧТО-ТО БОЕВОЕ - СДЕЛАЙТЕ ОТДЕЛЬНЫЙ 
docker-compose файл с закрытым портом и нормальными паролями) **make docker_dev**. У вас развернется БД и сервер движка
3. Просто запустить можно банальным make run

## Создание новой миграции
dbmate -d vims_code/db/migrations/ new "название миграции"

## Migrate

dbmate -d vims_code/db/migrations/ up

or

make migrate


## Что дальше

1. В ближайшее время я реализую (но только на бэке) идею "под-уровней" - это уровни, которые стартуют внутри, простите,
уровня, при срабатывании условий. Фактически, это будет пропатченный блок информации, который сможет принимать коды и жить своей жизнью (слиться,
закрыться, выполнить событие при прохождении-сливе, выдавать подсказки)
2. Написать более подробную документацию
## Клиентская морда
Выложу завтра