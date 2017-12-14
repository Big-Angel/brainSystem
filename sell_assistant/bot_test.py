from bot import Bot


if __name__ == '__main__':
    bot1 = Bot('../cfgs/tricks/huarui')
    bo2 = Bot('../cfgs/tricks/huarui')
    state, sentence = bot1.start()
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
