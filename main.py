import discord
import os
from dotenv import load_dotenv

import aiohttp
import io
import pypdf

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name = "hello", description = "Say hello to the bot")
async def hello(ctx):
    await ctx.respond("Hey!")

@bot.slash_command(name = "pdfmerge", description = "Merge two PDFs")
async def pdfmerge(ctx, a: discord.Option(description='Formatted 1'), b: discord.Option(description='Formatted 2')):
    await ctx.defer()

    a_splitted = a.split(':')
    a_message_id = int(a_splitted[0])
    a_attachment_index = int(a_splitted[1])

    b_splitted = b.split(':')
    b_message_id = int(b_splitted[0])
    b_attachment_index = int(b_splitted[1])

    channel = ctx.channel

    a_message = await channel.fetch_message(a_message_id)
    b_message = await channel.fetch_message(b_message_id)

    async with aiohttp.ClientSession() as a_session:
        a_attachment = a_message.attachments[a_attachment_index]
        async with a_session.get(a_attachment.url) as a_response:
            if a_response.status != 200:
                print('Response 1 status is not 200')
                return

            async with aiohttp.ClientSession() as b_session:
                b_attachment = b_message.attachments[b_attachment_index]
                async with b_session.get(b_attachment.url) as b_response:
                    if b_response.status != 200:
                        print('Response 2 status is not 200')
                        return

                    a_data = await a_response.read()
                    b_data = await b_response.read()

                    a_stream = io.BytesIO(a_data)
                    b_stream = io.BytesIO(b_data)

                    a_reader = pypdf.PdfReader(a_stream)
                    b_reader = pypdf.PdfReader(b_stream)

                    writer = pypdf.PdfWriter()

                    writer.append(a_reader)
                    writer.append(b_reader)

                    with io.BytesIO() as stream:
                        print(f'Writing PDF to stream...')
                        writer.write(stream)
                        stream.seek(0)

                        filename_noext, filename_ext = os.path.splitext(a_attachment.filename)

                        if filename_noext.endswith('-merged'):
                            filename_noext = filename_noext[:-7]

                        print(f'Creating File class...')
                        filename = f'{filename_noext}-merged.pdf'
                        file = discord.File(stream, filename)

                        print(f'Sending PDF to channel...')
                        await ctx.respond(f'```/pdfmerge {a} {b}\n```')
                        await channel.send(file=file, silent=True)

                        print('OK')

bot.run(os.getenv('TOKEN'))
