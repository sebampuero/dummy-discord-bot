import discord
from discord.ext import commands
from discord import File
from ttt_imager import Imager
import tictactoe as ttt
from tictactoe import EMPTY, X, O
from exceptions import CustomException
import time
import threading
import logging

class tttgame(commands.Cog):
    '''Para juegos
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

    TERMINATE_TIMEOUT = 600

    def __init__(self, client):
        self.client = client
        self.guild_to_game_map = dict()

    def _timeout(self, ctx, timeout=TERMINATE_TIMEOUT):
        game_map = self.guild_to_game_map[ctx.guild.id]
        try:
            while game_map["timeout_counter"] != timeout:
                time.sleep(1.0)
                game_map["timeout_counter"] += 1
            del self.guild_to_game_map[ctx.guild.id]
            logging.warning("Timeout for ttt reached")
        except:
            pass

    def _restart_timeout(self, ctx):
        self.guild_to_game_map[ctx.guild.id]["timeout_counter"] = 0

    async def _start_timeout(self, ctx):
        t = threading.Thread(target=self._timeout, args=(ctx,))
        t.setDaemon(True)
        t.start()
    
    @commands.command(name="challenge")
    async def challenge(self, ctx):
        if ctx.guild.id not in self.guild_to_game_map:
            if len(ctx.message.mentions) == 1:
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
            else:
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
            await self._start_timeout(ctx)
            await ctx.send(f"Escoge tu simbolo X u O {ctx.author.mention} escrbiendo `-symbol X` or `-symbol O`")
        else:
            await ctx.send("Ya hay un juego en progreso.")

    async def _start_ttt_game(self, ctx):
        game_map = self.guild_to_game_map[ctx.guild.id]
        if not game_map["against_ai"]:
            oponent = ctx.guild.get_member(game_map["player2"]["id"])
            await ctx.send(f"Esperando a que {oponent.mention} acepte con `-accept`")
        else:
            await ctx.send("Iniciando el juego...")
            await ctx.send(file=File(Imager(ctx.guild.id).create_initial_board()))
            await self._process_next_turn(ctx)

    @commands.command(name="accept")
    async def accept_game(self, ctx):
        game_map = self.guild_to_game_map
        if ctx.guild.id in game_map:
            if ctx.author.id == game_map[ctx.guild.id]["player2"]["id"]:
                await ctx.send("Iniciando el juego...")
                await ctx.send(file=File(Imager(ctx.guild.id).create_initial_board()))
                await self._process_next_turn(ctx)
                self._restart_timeout(ctx)

    async def _process_next_turn(self, ctx):
        game_map = self.guild_to_game_map[ctx.guild.id]
        if ttt.terminal(game_map["board"]):
            winner = ttt.winner(game_map["board"])
            if not winner:
                await ctx.send("Empate")
            elif game_map["player1"]["move"] == winner:
                member = ctx.guild.get_member(game_map["player1"]["id"])
                await ctx.send(f"Gana {member.mention}")
            elif game_map["player2"]:
                member = ctx.guild.get_member(game_map["player2"]["id"])
                await ctx.send(f"Gana {member.mention}")
            else:
                await ctx.send("Te gane ctm")
            del self.guild_to_game_map[ctx.guild.id]
            return
        game_map["inprogress"] = True
        player_turn = ttt.player(game_map["board"])
        if player_turn == game_map["player1"]["move"]:
            member = ctx.guild.get_member(game_map["player1"]["id"])
            await ctx.send(f"Es tu turno {member.mention}, juega con `-move [1-9]`")
        else:
            if game_map["against_ai"]:
                await ctx.send("Craneando mi siguiente movimiento...")
                next_action = ttt.minimax(game_map["board"])
                new_board = ttt.result(game_map["board"], next_action)
                game_map["board"] = new_board
                await ctx.send(file=File(Imager(ctx.guild.id).create_dirty_board(new_board)))
                await self._process_next_turn(ctx)
            else:
                member = ctx.guild.get_member(game_map["player2"]["id"])
                await ctx.send(f"Turno de {member.mention}, juega con `-move [1-9]`")

    @commands.command(name="move")
    async def play_move(self, ctx, move:int):
        game_map = self.guild_to_game_map
        if not move > 0 and not move < 10:
            return
        if ctx.guild.id in game_map:
            game_map = game_map[ctx.guild.id]
            player_turn = ttt.player(game_map["board"])
            if game_map["player1"]["id"] == ctx.author.id:
                if game_map["player1"]["move"] == player_turn:
                    await self._process_move(ctx, move)
                    self._restart_timeout(ctx)
                else:
                    await ctx.send("No es tu turno")
            elif game_map["player2"]["id"] == ctx.author.id:
                if game_map["player2"]["move"] == player_turn:
                    await self._process_move(ctx, move)
                    self._restart_timeout(ctx)
                else:
                    await ctx.send("No es tu turno")

    async def _process_move(self, ctx, move, coords_map=MOVE_TO_COORD_MAP):
        try:
            action = coords_map[move]
            game_map = self.guild_to_game_map[ctx.guild.id]
            new_board = ttt.result(game_map["board"], action)
            game_map["board"] = new_board
            await ctx.send(file=File(Imager(ctx.guild.id).create_dirty_board(new_board)))
            await self._process_next_turn(ctx)
        except CustomException.InvalidTTTMoveException:
            await ctx.send("Ese movimiento no es valido")

    @commands.command(name="symbol")
    async def move_choose(self, ctx, symbol:str):
        move = symbol.upper()
        if move != X and move != O:
            return
        game_map = self.guild_to_game_map
        if ctx.guild.id in game_map:
            if self._is_move_choose_valid(ctx, game_map):
                game_map[ctx.guild.id]["player1"]["move"] = move
                if not game_map[ctx.guild.id]["against_ai"]:
                    game_map[ctx.guild.id]["player2"]["move"] = X if move == O else O
                await self._start_ttt_game(ctx)
                self._restart_timeout(ctx)

    @commands.command(name="quit")
    async def stop_game(self, ctx):
        game_map = self.guild_to_game_map
        if ctx.guild.id in game_map:
            if ctx.author.id == game_map[ctx.guild.id]["player1"]["id"] or \
               ctx.author.id == game_map[ctx.guild.id]["player2"]["id"]:
                del game_map[ctx.guild.id]
                await ctx.send("bye bye")

    def _is_move_choose_valid(self, ctx, game_map):
        game_map = self.guild_to_game_map
        if ctx.guild.id not in game_map:
            return False
        return ctx.author.id == game_map[ctx.guild.id]["player1"]["id"] and not game_map[ctx.guild.id]["inprogress"]

def setup(client):
    client.add_cog(tttgame(client))