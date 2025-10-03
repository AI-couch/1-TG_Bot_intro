import random

# число попыток угадать
guess_made = 0
guess = 0

number = random.randint(1, 30)
print ('я загадал число между 1 и 30')


while guess != number:
   
    # получаем число от пользователя
    guess = int(input('Угадывай число: '))
    guess_made += 1

    if guess < number:
        print ('нет, надо больше')

    if guess > number:
        print ('нет уж, давай поменьше')

    if guess == number:
        break

if guess == number:
    print ('  ')
    print ('  Угадал !!')
    print (' Ты использовал {0} попыток! Молодец'.format(guess_made))
    exit = int(input('Спасибо за игру '))
