import discord.ext.commands as commands

def is_owner():
    def predicate(ctx):
        return ctx.message.author.id == 279796600308498434
    return commands.check(predicate)

