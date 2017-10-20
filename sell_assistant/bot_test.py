from bot import Bot


if __name__ == '__main__':
    bot = Bot('../cfgs/huarui')
    state, sentence = bot.start()
    print(state, sentence)

    while True:
        user_input = input('user input: ')
        if user_input == 'q':
            break
        state, sentence = bot.answer(user_input)
        print(state, sentence)
        if '结束' in state:
            print(bot.get_label())
            break
