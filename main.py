import datetime

import pygame
import neat
import os
import random
pygame.font.init()

# Screen info
WINDOW_WIDTH = 480
WINDOW_HEIGTH = 640

# Stats
GEN_NUM = 0
MAX_SCORE = 0

# Images source folder
SRC_FOLDER = "imgs"

# Get the images
BIRD_IMGS = []
for i in range(1, 4):
    BIRD_IMGS.append(pygame.transform.scale2x(pygame.image.load(os.path.join(SRC_FOLDER, f"karkar.png"))))
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(SRC_FOLDER, "pip.png")))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join(SRC_FOLDER, "background.png")),
                                (WINDOW_WIDTH, WINDOW_HEIGTH))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(SRC_FOLDER, "base.png")))

# Font info
STAT_FONT = pygame.font.SysFont("comicsans", 50)
SCORE_FONT_COLOR = (255, 255, 255)
GENERATION_FONT_COLOR = (255, 0, 0)
BIRD_COUNT_FONT_COLOR = (0, 255, 0)


def blitRotateCenter(surface, image, topleft, angle):
    """
    Rotate a surface and blit it to the window
    :param topleft: the top left position of the image
    :param surface: the surface to blit to
    :param image: the image surface to rotate
    :param angle: a float value for angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

    surface.blit(rotated_image, new_rect.topleft)


class Bird:
    """
    Bird class representing THE BIRD
    """
    MAX_ROTATION = 25
    IMGS = BIRD_IMGS
    ROT_VEL = 20
    ANIMATION_TIME = 10

    def __init__(self, x, y):
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # degrees to tilt
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        make the bird jump
        :return: None
        """
        self.vel = -10
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        make the bird move
        :return: None
        """
        self.tick_count += 1

        # for downward acceleration
        place = self.vel * self.tick_count + (0.5 * 3 * (self.tick_count ** 2)) # calculate place

        # terminal velocity
        if place >= 16:
            place = (place / abs(place)) * 16

        if place < 0:
            place -= 2

        self.y = self.y + place

        if place < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, window):
        """
        draw the bird
        :param window: pygame window or surface
        :return: None
        """
        self.img_count += 1

        # For animation of bird, loop through three images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # so when bird is nose diving it isn't flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # tilt the bird
        blitRotateCenter(window, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        gets the mask for the current image of the bird
        :return: None
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    Represents pipes in the game
    """
    GAP = 200
    VEL = 5

    def __init__(self, x):
        """
        Initialize the object
        :param x: x coordinate of the pipe
        """
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0

        # get the flipped pipe
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIP_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        """
        Set pipe height
        :return: None
        """
        self.height = random.randrange(40, 400)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Moves the pipe
        :return: None
        """
        self.x -= self.VEL

    def draw(self, window):
        """
        Draws the pipe
        :param window: window object
        :return:
        """
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIP_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        """
        Checks if pipe is colliding with the bird
        :param bird:
        :return:
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIP_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset) # otherwise it returns None
        top_point = bird_mask.overlap(top_mask, top_offset)

        if top_point or bottom_point:
            return True
        return False


class Base:
    """
    Represents base in the game
    """
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        """
        Initialize the object
        :param y: y coordinate of the base
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Moves the base left
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, window):
        """
        Draws the base
        :param window: window object
        :return: None
        """
        window.blit(self.IMG, (self.x1, self.y))
        window.blit(self.IMG, (self.x2, self.y))


def draw_window(window, birds, pipes, base, score, generation, num_birds):
    """
    Draws main window
    :param num_birds: number of birds alive
    :param generation: number of generation
    :param window: window object
    :param birds: List with bird objects
    :param pipes: pipe objects list
    :param base: base object
    :param score: user score
    :return: None
    """
    window.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(window)

    # Draw the text
    text = STAT_FONT.render("Score: " + str(score), 1, SCORE_FONT_COLOR)
    window.blit(text, ((WINDOW_WIDTH - 10 - text.get_width()), 10))

    text = STAT_FONT.render("Gen: " + str(generation), 1, GENERATION_FONT_COLOR)
    window.blit(text, (10, 10))
    text = STAT_FONT.render("Live birds: " + str(num_birds), 1, BIRD_COUNT_FONT_COLOR)
    window.blit(text, (10, 70))

    base.draw(window)

    # draw the birds
    for bird in birds:
        bird.draw(window)
    pygame.display.update()


def main(genomes, config):
    global GEN_NUM, MAX_SCORE

    nets = []
    gens = []
    birds = []

    # get the genomes
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        gens.append(g)

    # some constants
    PIPE_GAP = 600
    BASE_Y = WINDOW_HEIGTH - 70

    # all the objects
    base = Base(BASE_Y)
    pipes = [Pipe(PIPE_GAP)]

    # window and clock
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGTH))
    clock = pygame.time.Clock()

    # game hardness
    pipe_vel_cnt = 0
    pipe_vel = 5
    HARDNESS = 3
    user_score = 0

    # main loop
    run_frag = True
    while run_frag:
        clock.tick(60)

        # stop condition
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_frag = False
                pygame.quit()
                quit()

        # decide, which pipe to use
        pipe_index = 0
        if len(birds) > 0:
            if len(pipes) > 0 and birds[0].x > (pipes[0].x + pipes[0].PIPE_TOP.get_width()):
                pipe_index = 1
        else:
            run_frag = False
            break

        # move th birds
        for i, bird in enumerate(birds):
            bird.move()
            gens[i].fitness += 0.1

            # get the NN output
            output = nets[i].activate((bird.y, abs(bird.y - pipes[pipe_index].height),
                                       abs(bird.y - pipes[pipe_index].bottom)))


            # check, whether to jump of not
            if output[0] > 0.5:
                bird.jump()


        add_pipe = False
        remove_pipes = []
        for pipe in pipes:
            # delete birds if they collide with pipes
            for i, bird in enumerate(birds):
                if pipe.collide(bird):
                    gens[i].fitness -= 1
                    birds.pop(i)
                    nets.pop(i)
                    gens.pop(i)
                # if bird passed the pipe, draw a new one
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            # send pipe to deletion if needed
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove_pipes.append(pipe)

            pipe.move()

        # add a pipe
        if add_pipe:
            # increase the score and the fitness
            user_score += 1
            if user_score > MAX_SCORE:
                MAX_SCORE = user_score
            for g in gens:
                g.fitness += 5

            # create a new pipe
            new_pipe = Pipe(PIPE_GAP)
            new_pipe.VEL = pipe_vel
            pipes.append(new_pipe)

            # # increase the speed every "HARDNESS" pipes
            # pipe_vel_cnt += 1
            # if pipe_vel_cnt % HARDNESS == 0:
            #     pipe_vel += 1
            # if pipe_vel > 8:
            #     pipe_vel = 8
            # print("Speed: ", pipe_vel)

        # remove the pipes pending for deletion
        for r_pipe in remove_pipes:
            pipes.remove(r_pipe)

        # delete the bird if it touches the base of the sky
        for i, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= BASE_Y or bird.y < 0:
                birds.pop(i)
                nets.pop(i)
                gens.pop(i)

        base.move()
        draw_window(window, birds, pipes, base, user_score, GEN_NUM, len(birds))
    GEN_NUM += 1


def run(config_file_path):
    """
    Main function for NEAT-NN
    :param config_file_path: path to a config file
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file_path)

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    statistics = neat.StatisticsReporter()
    population.add_reporter(statistics)

    try:
        winner = population.run(main, 100)
    except pygame.error as e:
        pass
    with open("results.txt", "a+") as results_file:
        results_file.write(f"Date: {datetime.datetime.now().ctime()} \n")
        results_file.write(f"Generations: {GEN_NUM}\n")
        results_file.write(f"Max score: {MAX_SCORE}\n")
        results_file.write(f"\n")


if __name__ == '__main__':
    # get the path to a config file
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")

    # run the NN and th game
    run(config_path)

