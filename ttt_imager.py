from PIL import Image, ImageFont, ImageDraw
import tictactoe as ttt
from tictactoe import EMPTY, X, O
import copy

class Imager:

    IMG_WIDTH = 150
    IMG_HEIGHT = 150
    FONT = ImageFont.truetype('OpenSans-Regular.ttf', size=15)
    COLOR_MOVE = 'rgb(0,0,0)'
    COLOR_EMPTY = 'rgb(255,0,0)'

    def __init__(self, guild_id):
        self.guild_id = guild_id

    def create_initial_board(self, color=COLOR_MOVE, font=FONT):
        """
        Creates a board that contains each field identifier (1-9). Returns the filename of the saved board image
        """
        im = self.create_blank_board()
        draw = ImageDraw.Draw(im)
        sep = int(im.width / 3 - (im.width / 3) / 2)
        x_point = sep
        y_point = sep
        for i in range(1, 10):
            if i == 4 or i == 7:
                y_point = y_point + sep * 2
                x_point = sep
            draw.text((x_point,y_point), str(i), fill=color, font=font)
            x_point = x_point + sep * 2
        return self.saved_image_as_filename(im)

    def create_blank_board(self, width = IMG_WIDTH, height = IMG_HEIGHT):
        """
        Creates a blank board containing only the fields borders. Returns an Image object.
        """
        im= Image.new("RGB", (width, height), "#FFFFFF")
        pixels = im.load()
        for i in range(0, height):
            for j in range(0, width):
                if j == int(width / 3) or j == int(width * 2 / 3) or i == int(height / 3) or i == int(height * 2 / 3):
                            pixels[i,j] = 0
        return im

    def create_dirty_board(self, board, color_move=COLOR_MOVE, color_empty=COLOR_EMPTY, font=FONT):
        """
        Creates a dirty board. Empty spaces are represented as numbers 1-9. Returns the filename of the saved board image
        """
        tmp_board = copy.deepcopy(board)
        tmp_board = [j for sub in tmp_board for j in sub]
        im = self.create_blank_board()
        draw = ImageDraw.Draw(im)
        sep = int(im.width / 3 - (im.width / 3) / 2)
        x_point = sep
        y_point = sep
        for i in range(0, len(tmp_board)):
            if tmp_board[i]:
                draw.text((x_point,y_point), tmp_board[i], fill=color_move, font=font)
            else:
                draw.text((x_point,y_point), str(i+1), fill=color_empty, font=font)
            if i == 2 or i == 5:
                y_point = y_point + sep * 2
                x_point = sep
            else:
                x_point = x_point + sep * 2
        return self.saved_image_as_filename(im)

    def saved_image_as_filename(self, image):
        filename = f"./assets/ttboard/board{self.guild_id}.png"
        image.save(filename, format="PNG")
        return filename


