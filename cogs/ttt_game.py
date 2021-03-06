import discord
from discord.ext import commands
from discord import File
from Functionalities.TicTacToe.TTTImager import TTTImager
import Functionalities.TicTacToe.tictactoe as ttt
from Functionalities.TicTacToe.tictactoe import EMPTY, X, O
from exceptions import CustomException
import time
import threading
import logging
import functools

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GameManager:

    TERMINATE_TIMEOUT = 600

    def __init__(self):
        self.guild_to_game_map = dict()

    def start_game_with_ai(self, ctx):
        self._really_start_game(ctx, with_ai = True)

    def start_game(self, ctx):
        self._really_start_game(ctx, with_ai = False)

    def _really_start_game(self, ctx, with_ai=False):
        if with_ai:
            self.guild_to_game_map[ctx.guild.id] = {
                "player1": {
                    "id": ctx.author.id,
                    "move": EMPTY
                },
                "player2": None,
                "board": ttt.initial_state(),
                "against_ai": True,
                "inprogress": False,
                "timeout_counter": 0
            }
        else:
            self.guild_to_game_map[ctx.guild.id] = {
                "player1": {
                    "id": ctx.author.id,
                    "move": EMPTY
                },
                "player2": {
                    "id": ctx.message.mentions[0].id,
                    "move": EMPTY
                },
                "board": ttt.initial_state(),
                "against_ai": False,
                "inprogress": False,
                "timeout_counter": 0
            }

    def _timeout(self, ctx, timeout=TERMINATE_TIMEOUT):
        guild_id = ctx.guild.id
        while True:
            if guild_id in self.guild_to_game_map:
                game_map = self.guild_to_game_map[guild_id]
                if game_map["timeout_counter"] == timeout:
                    break
                time.sleep(1.0)
                game_map["timeout_counter"] += 1
            else:
                break
        self.delete_game(guild_id)
        logger.warning("Timeout for ttt reached")

    def game_exists(self, guild_id):
        return guild_id in self.guild_to_game_map

    def restart_timeout(self, ctx):
        self.guild_to_game_map[ctx.guild.id]["timeout_counter"] = 0

    def start_timeout(self, ctx):
        t = threading.Thread(target=self._timeout, args=(ctx,))
        t.setDaemon(True)
        t.start()

    def get_player_one(self, guild_id):
        return self.guild_to_game_map[guild_id]["player1"]

    def get_player_two(self, guild_id):
        return self.guild_to_game_map[guild_id]["player2"]

    def get_player_by_id(self, guild_id, player_id):
        game_map = self.guild_to_game_map[guild_id]
        if game_map["player1"]["id"] == player_id:
            return game_map["player1"]
        elif game_map["player2"]["id"] == player_id:
            return game_map["player2"]
        return None
    
    def is_against_ai(self, guild_id):
        return self.guild_to_game_map[guild_id]["against_ai"]

    def is_in_progress(self, guild_id):
        return self.guild_to_game_map[guild_id]["inprogress"]

    def set_in_progress(self, guild_id):
        self.guild_to_game_map[guild_id]["inprogress"] = True

    def set_player_one_move(self, guild_id, move):
        self.guild_to_game_map[guild_id]["player1"]["move"] = move

    def set_player_two_move(self, guild_id, move):
        self.guild_to_game_map[guild_id]["player2"]["move"] = move

    def get_ttt_board(self, guild_id):
        return self.guild_to_game_map[guild_id]["board"]

    def set_ttt_board(self, guild_id, new_board):
        self.guild_to_game_map[guild_id]["board"] = new_board

    def delete_game(self, guild_id):
        try:
            del self.guild_to_game_map[guild_id]
        except KeyError:
            pass


class tttgame(commands.Cog):
    '''Tic tac toe
    '''

    MOVE_TO_COORD_MAP = {
            1: (0,0),
            2: (0,1),
            3: (0,2),
            4: (1,0),
            5: (1,1),
            6: (1,2),
            7: (2,0),
            8: (2,1),
            9: (2,2)
        }

    def __init__(self, client):
        self.client = client
        self.loop = self.client.loop
        self.game_manager = GameManager()
    
    @commands.command(name="challenge")
    async def challenge(self, ctx):
        '''Challenge someone to play tic tac toe with `-challenge [tag]`
         Use only `-challenge` to play against AI
        '''
        if not self.game_manager.game_exists(ctx.guild.id):
            if len(ctx.message.mentions) == 1:
                self.game_manager.start_game(ctx)
            else:
                self.game_manager.start_game_with_ai(ctx)
            self.game_manager.start_timeout(ctx)
            await ctx.send(f"Choose X or O {ctx.author.mention} by typing `-symbol X` or `-symbol O`")
        else:
            await ctx.send("There is a game in progress")

    async def _start_ttt_game(self, ctx):
        if not self.game_manager.is_against_ai(ctx.guild.id):
            player2 = self.game_manager.get_player_two(ctx.guild.id)
            oponent = ctx.guild.get_member(player2["id"])
            await ctx.send(f"Waiting for {oponent.mention} to accept with `-accept`")
        else:
            await ctx.send("Starting game...")
            await ctx.send(file=File(TTTImager(ctx.guild.id).create_initial_board()))
            await self._process_next_turn(ctx)

    @commands.command(name="accept")
    async def accept_game(self, ctx):
        '''Command to accept when challenged to play tic tac toe
        '''
        if self.game_manager.game_exists(ctx.guild.id):
            player2 = self.game_manager.get_player_two(ctx.guild.id)
            if player2["id"] == ctx.author.id:
                await ctx.send("Starting game")
                await ctx.send(file=File(TTTImager(ctx.guild.id).create_initial_board()))
                await self._process_next_turn(ctx)
                self.game_manager.restart_timeout(ctx)

    async def _is_game_ended(self, ctx, player1, player2, board):
        if ttt.terminal(board):
            winner = ttt.winner(board)
            if not winner:
                await ctx.send("Tie")
            elif player1["move"] == winner:
                member = ctx.guild.get_member(player1["id"])
                await ctx.send(f"{member.mention} wins")
            elif player2:
                member = ctx.guild.get_member(player2["id"])
                await ctx.send(f"{member.mention} wins")
            else:
                await ctx.send("I won ctm")
            self.game_manager.delete_game(ctx.guild.id)
            return True
        return False

    async def _process_next_turn(self, ctx):
        board = self.game_manager.get_ttt_board(ctx.guild.id)
        player1 = self.game_manager.get_player_one(ctx.guild.id)
        player2 = self.game_manager.get_player_two(ctx.guild.id)
        if await self._is_game_ended(ctx, player1, player2, board):
            return
        self.game_manager.set_in_progress(ctx.guild.id)
        player_turn = ttt.player(board)
        if player_turn == player1["move"]:
            member = ctx.guild.get_member(player1["id"])
            await ctx.send(f"It is your turn {member.mention}, play with `-m [1-9]`")
        else:
            if self.game_manager.is_against_ai(ctx.guild.id):
                await ctx.send("Thinking about my next move....")
                next_action = await self.loop.run_in_executor(None, functools.partial(ttt.minimax, board))
                new_board = ttt.result(board, next_action)
                self.game_manager.set_ttt_board(ctx.guild.id, new_board)
                await ctx.send(file=File(TTTImager(ctx.guild.id).create_dirty_board(new_board)))
                await self._process_next_turn(ctx)
            else:
                member = ctx.guild.get_member(player2["id"])
                await ctx.send(f"It is {member.mention}'s turn, play with `-m [1-9]`")

    @commands.command(name="move", aliases=["m"])
    async def play_move(self, ctx, move:int):
        '''Command to make a move with `X` or ʻO` in tic tac toe
        '''
        if not move > 0 and not move < 10:
            return
        if self.game_manager.game_exists(ctx.guild.id):
            board = self.game_manager.get_ttt_board(ctx.guild.id)
            player = self.game_manager.get_player_by_id(ctx.guild.id, ctx.author.id)
            player_turn = ttt.player(board)
            if player:
                if player["move"] != player_turn:
                    return await ctx.send("Not your turn")
                await self._process_move(ctx, move)
                self.game_manager.restart_timeout(ctx)

    async def _process_move(self, ctx, move, coords_map=MOVE_TO_COORD_MAP):
        try:
            board = self.game_manager.get_ttt_board(ctx.guild.id)
            action = coords_map[move]
            new_board = ttt.result(board, action)
            self.game_manager.set_ttt_board(ctx.guild.id, new_board)
            await ctx.send(file=File(TTTImager(ctx.guild.id).create_dirty_board(new_board)))
            await self._process_next_turn(ctx)
        except CustomException.InvalidTTTMoveException:
            await ctx.send("That movement is not valid")

    @commands.command(name="symbol")
    async def symbol_choose(self, ctx, symbol:str):
        '''Command to choose `X` or `O` after starting a game
        '''
        move = symbol.upper()
        if move != X and move != O:
            return
        if self.game_manager.game_exists(ctx.guild.id):
            if self._is_symbol_choose_valid(ctx):
                self.game_manager.set_player_one_move(ctx.guild.id, move)
                if not self.game_manager.is_against_ai(ctx.guild.id):
                    p2_move = X if move == O else O
                    self.game_manager.set_player_two_move(ctx.guild.id, p2_move)
                await self._start_ttt_game(ctx)
                self.game_manager.restart_timeout(ctx)

    @commands.command(name="quit")
    async def stop_game(self, ctx):
        '''Ends the game
        '''
        if self.game_manager.game_exists(ctx.guild.id):
            player = self.game_manager.get_player_by_id(ctx.guild.id, ctx.author.id)
            if player:
                self.game_manager.delete_game(ctx.guild.id)
                await ctx.send("bye bye")

    def _is_symbol_choose_valid(self, ctx):
        if not self.game_manager.game_exists(ctx.guild.id):
            return False
        player1 = self.game_manager.get_player_one(ctx.guild.id)
        return ctx.author.id == player1["id"] and not self.game_manager.is_in_progress(ctx.guild.id)

def setup(client):
    client.add_cog(tttgame(client))