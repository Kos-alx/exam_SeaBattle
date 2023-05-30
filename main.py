"""
За основу взят пример из вебинара, в который были добавлены некоторые изменения:
1. Теперь компьютер не бьет в те места, в которые он уже бил, или в те, которые граничат с подбитыми им кораблями.
2. Если компьютер ранит корабль, то следующий его ход будет уже не случайным, он будет метить в соседние клетки, чтобы
добить раненного.
3. Все изменения закомментированы
"""

from random import randint


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"({self.x}, {self.y})"


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку"


class BoardWrongShipException(BoardException):
    pass


class Ship:
    def __init__(self, bow, l, o):
        self.bow = bow
        self.l = l
        self.o = o
        self.lives = l

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i

            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))

        return ship_dots

    def shooten(self, shot):
        return shot in self.dots


class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid

        self.count = 0

        self.field = [["O"] * size for _ in range(size)]

        self.busy = []
        self.ships = []

        self.wound = False  # эта переменная становится True, когда корабль ранен

    def add_ship(self, ship):

        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)

        self.ships.append(ship)
        self.contour(ship)

    def contour(self, ship, verb=False):
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not (self.out(cur)) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "."
                    self.busy.append(cur)

    def __str__(self):
        res = ""
        res += "  | 1 | 2 | 3 | 4 | 5 | 6 |"
        for i, row in enumerate(self.field):
            res += f"\n{i + 1} | " + " | ".join(row) + " |"

        if self.hid:
            res = res.replace("■", "O")
        return res

    def out(self, d):
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def shot(self, d):
        if self.out(d):
            raise BoardOutException()

        if d in self.busy:
            raise BoardUsedException()

        self.busy.append(d)

        for ship in self.ships:
            if d in ship.dots:
                ship.lives -= 1
                self.field[d.x][d.y] = "X"
                if ship.lives == 0:
                    self.wound = False  # если корабль уничтожен, значит он уже не ранен
                    self.count += 1
                    self.contour(ship, verb=True)
                    print("Корабль уничтожен!")

                    if ship in g.us.board.ships:  # идет проверка, что уничтожен корабль именно игрока
                        g.ai.last_dot = None  # забываем последний удар по кораблю, так как он уничтожен
                        g.ai.horizon = None  # забываем направление корабля, если, вдруг, его испльзовали.
                    return False
                else:
                    print("Корабль ранен!")
                    self.wound = True  # дает понять компьютеру, что корабль ранен

                    if ship in g.us.board.ships:  # проверяем что ранен корабль именно у игрока
                        g.ai.last_dot = None  # забываем последний выстрел, так как обновим его позже.
                        if ship.l == 3 and ship.lives < 2:  # проверяем, что раненный корабль трехпалубный
                            g.ai.horizon = ship.o  # если да, то компьютер понимает, горизонтальный он или вертикальный
                    return True

        self.field[d.x][d.y] = "."
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy


    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    '''
    Основные изменения были внесены именно в этот класс
    '''
    def __init__(self, board, enemy):  # переопределяем инициализацию наследного класса
        super().__init__(board, enemy)
        self.last_dot = None  # сюда запишем последнюю точку, если корабль ранят
        self.horizon = None  # сюда запишем направление корабля, если дважды раним трехпалубный

    def ask(self):

        if g.us.board.wound:  # компьютер ранил корабль
            if self.horizon == 1:  # компьютер дважды ранил горизонтальный трехпалубник
                look_for = [(0, 1), (0, -1), (0, 2)] # будет бить по горизонтали
            elif self.horizon == 0:  # компьютер дважды ранил вертикальный трехпалубник
                look_for = [(1, 0), (-1, 0), (2, 0)]  # будет бить по вертикали
            else:
                look_for = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # будет бить рядом с клеткой единожды раненого корабля

            # если корабль ранен и последняя точка не сохранена, то сохраняем ее.
            # если точка сохранена, то не меняем ее.
            # это важный момент!
            # если после ранения компьютер промазал, ориентиром для следующего удара останется точка ранения
            if self.last_dot is None:
                self.last_dot = g.us.board.busy[-1]

            for delta_coord in look_for:
                #  пробегаем по списку look_for, и изменяем точку ранения корабля на ту, что рядом
                d = Dot((self.last_dot.x + delta_coord[0]), (self.last_dot.y + delta_coord[1]))
                if g.us.board.out(d) or d in g.us.board.busy:
                    continue  # если точка вне поля или бить по ней нельзя, двигаемся дальше
                else:
                    print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
                    return d

        d = Dot(randint(0, 5), randint(0, 5))
        while d in g.us.board.busy:  # если в выбранную точку бить нельзя, формируем новую.
            d = Dot(randint(0, 5), randint(0, 5))
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d


class User(Player):
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()

            if len(cords) != 2:
                print(" Введите 2 координаты! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)

            return Dot(x - 1, y - 1)



class Game:
    def __init__(self, size=6):
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = True

        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def random_board(self):
        board = None
        while board is None:
            board = self.random_place()
        return board

    def random_place(self):
        lens = [3, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size)
        attempts = 0
        for l in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def greet(self):
        print("--------------------")
        print("  Приветствуем вас  ")
        print("       в игре       ")
        print("     морской бой    ")
        print("--------------------")
        print("  формат ввода: x y ")
        print("  x - номер строки  ")
        print("  y - номер столбца ")

    def loop(self):
        num = 0
        while True:
            print("-" * 20)
            print("Доска пользователя:")
            print(self.us.board)
            print("-" * 20)
            print("Доска компьютера:")
            print(self.ai.board)
            if num % 2 == 0:
                print("-" * 20)
                print("Ходит пользователь!")
                repeat = self.us.move()
            else:
                print("-" * 20)
                print("Ходит компьютер!")
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.count == 7:
                print("-" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.count == 7:
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    def start(self):
        self.greet()
        self.loop()


g = Game()
g.start()
