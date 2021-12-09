
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functions import dateparser, timeparser, timeDifferenceInSec
import logging
import sqlite3
import re
from datetime import date, datetime, timedelta


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)



def start(bot, update):

    update.message.reply_text('Привет, введи /help для получения дополнительной информации')
    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username


    checkuser(chat_id, chat_usr)


def help(bot, update):

    update.message.reply_text('🔴 Добро пожаловать!! 🔴 \n'
                              'используй команды ниже, чтобы взаимодействовать со мной:\n\n'
                              ' 📅 Помощник в планировании дел 📅\n'
                              '/schedule   - показать дела в заданный день 📓 \n'
                              '/remember   - запланировать дело 📌 \n'
                              '/info      - показать информацию, относящуюся к делу\n'
                              '/forget    - удалить дело ❌ \n'
                              '/free          - удалить все дела (⚠Внимание⚠)\n\n')


def remember(bot, update, args, job_queue, chat_data):

    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username


    checkuser(chat_id, chat_usr)

    codu = getuser(chat_id)

    name = ""
    date = ""
    place = ""
    time = ""
    desc = ""
    if len(args) < 2:
        update.message.reply_text("Пожалуйста, не забудь, что я не знаю всю информацию\n"
                                  "Пожалуйста, отправь мне все данные, напиши: \n\n"
                                  "/remember <дело><дата><место><время><описание>\n\n"
                                  " пример: '/remember обед 12/10/2021 Казань_квартира_кухня 14:00 обед с семьёй'")
        return
    else:
        i = 0
        for par in args[0:]:
            i += 1
            matchObj = re.fullmatch(r'([^\s!/]+)', par, re.M | re.I)
            if matchObj:
                name += (matchObj.group()+" ")
                continue
            matchObj = re.match(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', par, re.M | re.I)
            if matchObj:
                date = matchObj.group()
                break

        for par in args[i:]:
            i += 1
            matchObj = re.fullmatch(r'([^\s!:]+)', par, re.M | re.I)
            if matchObj:
                place += (matchObj.group()+" ")
                continue
            matchObj = re.match(r'[0-9]{2}:[0-9]{2}', par, re.M | re.I)
            if matchObj:
                time = matchObj.group()
                break

        for par in args[i:]:
            desc += (re.match(r'([^\s]+)', par, re.M | re.I).group()+" ")

    if time == "":
        time = "08:00"

    if dateparser(date) != -1 and timeparser(time) != -1:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()

        c.execute("INSERT INTO todos (uid, name, date, place, time, descr) "
                  "VALUES(?,?,?,?,?,?)", (codu, name, date, place, time, desc))
        conn.commit()
        conn.close()

        due_datetime = datetime.combine(dateparser(date),
                                        timeparser(time))
        today_date = datetime.now()

        diff_in_sec = timeDifferenceInSec(due_datetime, today_date) - 5400
        set_timer(update, diff_in_sec, job_queue, chat_id, chat_data)

        update.message.reply_text("Понял! Не волнуйся, я запомню это для тебя 💪 \n")
    else:
        update.message.reply_text("❌ Эй, друг формат времени или даты неправильный \n"
                                  "Запомни, дата должна иметь вид : дд/мм/гггг \n"
                                  "и время должно быть в формате: чч:мм \n\n ")


def alarm(bot, job):

    bot.send_message(job.context, text='✔ Эй, друг, ты должен приступить к какому-то делу через полчаса... '
                                       'Проверь свои дела, если хочешь подробностей!')


def set_timer(update, args, job_queue, chat_id, chat_data):

    try:

        due = int(args)
        #if due < 0:
         #   update.message.reply_text('Извини, мы не можем вернуться в прошлое!')
          #  return


        job = job_queue.run_once(alarm, due, context=chat_id)
        chat_data['job'] = job
        update.message.reply_text('Напоминание для этого дела успешно установлено!')

    except (IndexError, ValueError):
        update.message.reply_text('Друг, у меня возникли проблемы при установке напоминания! '
                                  'Прошу удалить/ввести дело снова!')


def unset(bot, update, chat_data):

    if 'job' not in chat_data:

        return

    job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']




def info(bot, update, args):

    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username


    checkuser(chat_id, chat_usr)

    codu = getuser(chat_id)

    if len(args) == 0:
        update.message.reply_text("Друг, пожалуйста, введи номер дела, о котором хочешь знать подробнее!\n"
                                  "пример: /info <номер_дела>")
    else:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        print("SELECT * FROM todos WHERE uid="+str(codu)+" and tid="+str(args[0]))
        c.execute('SELECT * FROM todos WHERE uid=? and tid=?', (codu, args[0]))
        data = c.fetchone()
        if data[0] is not None:
            update.message.reply_text("🔻 Краткая информация для '"+data[2]+"'\n\n" +
                                      "Название дела: "+data[2]+"\n" +
                                      "📆 Состоится: "+data[3]+"\n" +
                                      "⏰ в: "+data[5] + "\n" +
                                      "🌍 в: "+str(data[4]).upper()+ "\n" +
                                      "📎 детали: "+str(data[6]) + "\n\n")
        conn.close()


def forget(bot, update, args, chat_data):

    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username


    checkuser(chat_id, chat_usr)

    codu = getuser(chat_id)

    if isinstance(args, list):

        if len(args) == 0:
            update.message.reply_text("Друг, пожалуйста, введи номер дела, которое хочешь удалить!"
                                      "/forget <номер_дела>")
        else:
            conn = sqlite3.connect('todo.db')
            c = conn.cursor()
            c.execute('DELETE FROM todos WHERE uid=? and tid=?', (codu, args[0]))
            conn.commit()
            conn.close()
            update.message.reply_text("Хорошо, я чувствую себя свободнее сейчас!👾")
        return

    else:
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        c.execute('DELETE FROM todos WHERE uid=? and tid=?', (codu, args))
        conn.commit()
        conn.close()

        unset(bot, update, chat_data)


def free(bot, update, chat_data):

    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username


    checkuser(chat_id, chat_usr)

    codu = getuser(chat_id)

    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos where uid=?', (codu,))
    data = c.fetchall()
    if len(data) != 0:
        for row in data:
            forget(bot, update, row[0], chat_data)

    update.message.reply_text("Друг, я ухожу в отпуск! Наконец я свободен... 😎")


def default(bot, update):

    update.message.reply_text("да... ты прав!")

def manage_command(bot, update):
    update.message.reply_text("Неизвестная команда. Нажми /help для получения подробностей")


def error(bot, update, error):

    logger.warning('Обновление "%s" вызвало ошибку "%s"', update, error)


def checkuser(chat_id, chat_usr):

    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user WHERE username=? or chat_id=?', (chat_usr, chat_id))
    data = c.fetchall()
    if data.pop(0)[0] == 0:
        print("new user found")
        c.execute('INSERT INTO user(username, chat_id) VALUES (?,?)', (chat_usr, chat_id))
    else:

        c.execute('UPDATE user SET username=?, chat_id=? WHERE chat_id=?', (chat_usr, chat_id, chat_id))

    conn.commit()
    conn.close()


def getuser(chat_id):

    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM user WHERE chat_id=? ', (chat_id,))
    data = c.fetchall()

    if len(data) != 0:
        cod = data.pop(0)[0]
    else:
        cod = -1

    conn.close()
    return cod


def print_appointment(row):
    temp = ""
    temp += ("Дело: " + str(row[2]) + "[код:" + str(row[0]) + "]\n")
    if row[3] != 0:
        temp += ("в: " + str(row[3]))
    if row[5] != 0:
        temp += (" " + str(row[5]))
    if row[4] != 0:
        temp += ("\nв: " + str(row[4]))
    return temp


def delete_old_schedule(bot, update):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos')
    data = c.fetchall()
    if len(data) != 0:
        actual_date = date.today()
        for row in data:

            if dateparser(row[3]) == "" or dateparser(row[3]) == -1:

                c.execute('DELETE FROM todos WHERE tid=?', (row[0],))


            if dateparser(row[3]) < actual_date:

                c.execute('DELETE FROM todos WHERE tid=?', (row[0],))
    conn.commit()
    conn.close()
    update.message.reply_text("База данных очищена успешно! 🙌")


def schedule(bot, update, args):

    chat_id = update.message.chat_id
    chat_usr = update.message.from_user.username


    checkuser(chat_id, chat_usr)


    codu = getuser(chat_id)
    if codu == -1:
        update.message.reply_text("Друг, думаю у меня проблема...\n"
                                  "я не могу сделать то, что ты просишь!\n")

    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM todos WHERE uid=?', (codu,))
    data = c.fetchall()
    if len(data) != 0:
        actual_date = date.today()
        appointments = ""
        if len(args) != 1:
            if len(args) == 0:

                update.message.reply_text("😵 Друг, твои дела на сегодня:\n\n")
                for row in data:
                    if dateparser(row[3]) != -1 and dateparser(row[3]) == actual_date:
                        appointments += ("📌 " + print_appointment(row)+"\n")
                update.message.reply_text(appointments+"\n")
            else:

                update.message.reply_text("👮 Друг, думаю ты написал что-то неправильно...\n\n")
        else:
            if args[0].find("/") != -1 or args[0].find("-") != -1:

                update.message.reply_text("😵 Друг, твои дела на " + args[0] + ":\n\n")
                for row in data:
                    if dateparser(row[3]) != -1 and dateparser(row[3]) == dateparser(args[0]):
                        appointments += ("📌 " + print_appointment(row) + "\n")
                   # else:
                    #    update.message.reply_text("😵 неправильный формат данных! Я не могу помочь тебе \n\n")
                update.message.reply_text(appointments + "\n")
            elif args[0] == "все":

                update.message.reply_text("😵 Друг, все твои запланированные дела:\n\n")
                for row in data:
                    appointments += ("📌 " + print_appointment(row) + "\n")
                update.message.reply_text(appointments + "\n")
            else:

                update.message.reply_text("😵 Друг, твои дела:\n\n")
                for row in data:
                    if dateparser(row[3]) != -1 and dateparser(row[3]) < (actual_date + timedelta(days=int(args[0]))):
                        appointments += ("📌 " + print_appointment(row) + "\n")
                update.message.reply_text(appointments + "\n")
        conn.close()

        update.message.reply_text("\nХочешь знать что-то ещё??\n"
                                  "Попробуй:\n\n"
                                  "  /schedule             - для показа всех дел на сегодня\n"
                                  "  /schedule <дд/мм/гггг>  - для показа дел в конкретный день\n"
                                  "  /schedule <# дней> - для показа дел на следующие #n дней\n"
                                  "  /schedule все         - для показа всех запланированных дел\n")
    else:
        update.message.reply_text("Друг, я не помню дел на сегодня! Так что расслабься 🎉 \n\n")


def own(bot, update):
    update.message.reply_text("_")


def main():

    updater = Updater("5070651489:AAFR7rtgBaSFmWXYPzqCOx-vjDK-iBPYMYk")


    dp = updater.dispatcher


    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))


    dp.add_handler(CommandHandler("remember", remember,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("forget", forget,
                                  pass_args=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("schedule", schedule,
                                  pass_args=True))
    dp.add_handler(CommandHandler("info", info,
                                  pass_args=True))
    dp.add_handler(CommandHandler("free", free, 
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("clean", delete_old_schedule))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset,
                                  pass_chat_data=True))


    dp.add_handler(CommandHandler("own", own))


    dp.add_handler(MessageHandler(Filters.text, default))
    dp.add_handler(MessageHandler(Filters.command, manage_command))


    dp.add_error_handler(error)


    dp.add_error_handler(error)


    updater.start_polling()


    updater.idle()

if __name__ == '__main__':
   main()

