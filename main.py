import discord
from discord import app_commands
from discord.ext import commands
from discord import Interaction
import requests
import matplotlib.pyplot as plt
from io import BytesIO
import os
from dotenv import load_dotenv
from datetime import datetime # TODO: Implement Later
import yfinance as yf

#env variables
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
STOCKNEWS_ENDPOINT = os.getenv('STOCKNEWS_ENDPOINT')
LATESTNEWS_ENDPOINT = os.getenv('LATESTNEWS_ENDPOINT')
STOCKNEWS_APIKEY = os.getenv('STOCKNEWS_APIKEY')

# Initialize the Bot
bot = commands.Bot(command_prefix=".", intents= discord.Intents.all())

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="THE MARKET"),
                                  status=discord.Status.online)
    print(f"{bot.user.name} is logged in.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


# code below is used as example for other commands
@bot.command()
async def hello(ctx):
    await ctx.send("Hey there! I am marketPal, here to please you with all your market associated needs!")

@bot.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!", ephemeral=True)

@bot.tree.command(name="say")
@app_commands.describe(thing_to_say = "What should I say?")
async def say(interaction: discord.Interaction, thing_to_say: str):
    await interaction.response.send_message(f"{interaction.user.name} said: '{thing_to_say}'")


# simple ping command
@bot.tree.command(name="ping", description="it will show a ping!")
async def ping(interaction : Interaction):
    bot_latency = round(bot.latency*1000)
    await interaction.response.send_message(f"Pong!... {bot_latency}ms")
# code above is used as example for other commands (below are the real commands heheheeh)

#Code below displays the /latestnews command which provides the five latest headlines related to the stock market market
@bot.tree.command(name="latestnews", description="Get the latest stock market news!")
async def latestnews(ctx):
    articles_data = get_financial_news()

    embed = discord.Embed(title="Latest Stock Market News", color=0x16e6b5)

    for index, article in enumerate(articles_data[:5], start=1):
        embed.add_field(
            name=f"Article {index}", 
            value=f"{article['title']}\nLink: [Read More]({article['url']})",
            inline=False
            )

    if isinstance(ctx, Interaction):
        await ctx.response.send_message(embed=embed, ephemeral=False)
    else:
        await ctx.send(embed=embed)

def get_financial_news():
    api_key = STOCKNEWS_APIKEY
    endpoint = LATESTNEWS_ENDPOINT
    params = {
        "country": "us",
        "category": "business",
        "apiKey": api_key
    }
    response = requests.get(endpoint, params=params)
    news_data = response.json()
    articles = news_data.get("articles", [])
    return articles


# Code below provides a more specific range of news that requires a ticker symbol
@bot.tree.command(name="news", description="Get the latest news for a specific stock!")
@app_commands.describe(ticker = "The ticker symbol to get news for *Please Use All Caps*")
async def specificnews(ctx, ticker: str):
    articles_data = get_specific_news(ticker)

    # Check if there are articles for the given ticker
    if not articles_data:
        # Check if the command was invoked through a slash command
        if isinstance(ctx, Interaction):
            await ctx.response.send_message(f"No news found for {ticker}", ephemeral=False)
        else:
            await ctx.send(f"No news found for {ticker}")
        return

    # Create an embed to accumulate articles
    embed = discord.Embed(title=f"News for {ticker} stock", color=0xf57083)

    # Add articles to the embed (limit to the first 3 articles)
    for index, article in enumerate(articles_data[:3], start=1):
        embed.add_field(
            name=f"Article {index}",
            value=f"[{article['title']} - Read More]({article['url']})\n{article['description'][:250] + '...' if len(article['description']) > 250 else article['description']}",
            inline=False
        )
        embed.set_image(url=article['urlToImage'])  # Set image for each article

    # Check if the command was invoked through a slash command
    if isinstance(ctx, Interaction):
        await ctx.response.send_message(embed=embed, ephemeral=False)
    else:
        await ctx.send(embed=embed)

def get_specific_news(ticker):
    api_key = STOCKNEWS_APIKEY
    endpoint = STOCKNEWS_ENDPOINT
    params = {
        "q": f"{ticker} stock",
        "apiKey": api_key
    }
    response = requests.get(endpoint, params=params)
    news_data = response.json()
    articles = news_data.get("articles", [])
    return articles




#portfolio







 # Chart

@bot.tree.command(name='chart')
async def stock(ctx, ticker: str):
    try:
        # Download stock data for the given ticker
        data = yf.download(ticker, start="2019-01-01", end="2024-02-16")

        # Reset index and get dates and close prices
        data = data.reset_index()
        dates = list(data['Date'])
        close = list(data['Close'])

        # Plot the graph
        plt.plot(dates, close)
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.title(f'{ticker} Stock Price')

        # Save the plot to a BytesIO object
        image_stream = BytesIO()
        plt.savefig(image_stream, format='png')
        plt.close()

        # Move the stream position to the beginning
        image_stream.seek(0)

        # Send the plot as an image
        await ctx.response.send_message(f'Sure! Here is latest chart data for {ticker}:', file=discord.File(image_stream, f'{ticker}_plot.png'))
    
    except Exception as e:
        # Handle errors (e.g., invalid ticker)
        await ctx.response.send_message(f'Error: {e}')


    




bot.run(DISCORD_TOKEN)