from __future__ import unicode_literals
import youtube_dl
import os
import discord
from discord.ext import commands
from discord.ext import tasks
import nest_asyncio
import asyncio
from youtubesearchpython import VideosSearch
nest_asyncio.apply()

apikey = input('insert your API key:')

ydl_opts = {
    'outtmpl': 'audio.mp3',
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

def download(url):
  if os.path.isfile('audio.mp3'):
    os.remove('audio.mp3')
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download([url])

urls = []
vc = None
user = None
ctx_ = None

bot = commands.Bot(command_prefix='!')

def nextSong():
  global urls
  global vc
  asyncio.run( streamMusic(urls[-1]) )
  urls.pop()

def makeUrl(words):
  if len(words) == 1 and words[0].startswith('http'):
    return words[0]
  else:
    query = ''
    for word in words: query += word + ' '
    query = query[:-1]
    videosSearch = VideosSearch(query, limit=1).result()
    return videosSearch['result'][0]['link']

async def streamMusic(url):
  global vc
  global ctx_
  #end if player is not in voice chat 
  user = ctx_.author
  if user.voice is None: return
  voice_channel = user.voice.channel
  # grab user's voice channel
  channel = voice_channel.name
  #download Youtube Video and convert it in .mp3
  download(url)
  # create StreamPlayer
  try:
    vc = await voice_channel.connect()
  except:
    print('bot already connected!')
  await ctx_.channel.send('Now playing: ' + url)
  vc.play(discord.FFmpegPCMAudio('audio.mp3'))
  vc.source = discord.PCMVolumeTransformer(vc.source)

@bot.command(name='play', description='Play a video from Youtube', pass_context=True)
async def play(ctx, *args):
  global urls
  global ctx_
  global vc
  if len(args) == 0: return
  url = makeUrl(args)
  ctx_ = ctx
  urls.append(url)
  if vc.is_playing():
    await ctx.channel.send('Added to list: ' + url)

@bot.command(name='leave')
async def leave(ctx): 
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send('Bot left')

@bot.command(name='list')
async def list(ctx): 
  global urls
  await ctx.channel.send(urls)

@bot.command(name='skip')
async def skip(ctx): 
  global vc
  vc.stop()
  await ctx.channel.send('Song skipped!')
  nextSong()

@tasks.loop(seconds = 2) # repeat after every 10 seconds
async def CheckCurrentSong():
  global urls
  global vc
  if vc is None or vc.is_playing() is not True:
    if len(urls) is not 0:
      nextSong()

@bot.event
async def on_ready():
    CheckCurrentSong.start()
    print("Ready!")

bot.run(apikey)
